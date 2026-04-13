"""
Commercial closure views: Placement, CommissionRecord, CommissionReminder.

These handle the offer → join → placement-confirmed → payment commercial lifecycle.
Deliberately separate from hiring stage management (views.py).
"""
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.pipeline.models import Application, Placement, CommissionRecord, CommissionReminder
from apps.pipeline.serializers import (
    PlacementSerializer, CommissionRecordSerializer, CommissionReminderSerializer,
)
from apps.core.responses import success_response, error_response


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_placement(pk, tenant_id):
    """Return Placement scoped to tenant or None."""
    return Placement.objects.filter(id=pk, tenant_id=tenant_id).first()


def _get_commission(pk, tenant_id):
    """Return CommissionRecord scoped to company tenant or None."""
    return CommissionRecord.objects.filter(id=pk, company_tenant_id=tenant_id).first()


def _auto_create_placement(application, user):
    """
    Idempotent: create a Placement for an application that reached offer stage.
    Also auto-creates CommissionRecord if this is an agency submission.
    Returns the Placement instance.
    """
    placement, created = Placement.objects.get_or_create(
        application_id=application.id,
        defaults=dict(
            tenant_id=application.tenant_id,
            candidate_id=application.candidate_id,
            requisition_id=application.requisition_id,
            agency_id=application.agency_id if application.is_agency_submission else None,
            placement_status='pending_offer',
            joining_date=application.joining_date,
            created_by=user.id,
        ),
    )

    if created and application.is_agency_submission and application.agency_id:
        _auto_create_commission(placement, application, user)

    return placement


def _auto_create_commission(placement, application, user):
    """
    Create a CommissionRecord, optionally inheriting terms from AgencyClientRelationship.
    """
    commission_model = 'percentage'
    commission_rate = None
    expected_amount = None
    basis_source = 'manual'
    agency_relationship_id = None
    currency = application.offer_currency or 'INR'

    # Try to inherit from relationship
    try:
        from apps.agencies.models import AgencyClientRelationship
        rel = AgencyClientRelationship.objects.filter(
            agency_tenant_id=application.agency_id,
            company_tenant_id=application.tenant_id,
            status='active',
        ).first()
        if rel:
            agency_relationship_id = rel.id
            commission_model = rel.commission_type or 'percentage'
            basis_source = 'inherited'
            if rel.commission_percentage:
                commission_rate = rel.commission_percentage
                if application.offer_amount and commission_rate:
                    expected_amount = (
                        Decimal(str(application.offer_amount)) *
                        commission_rate / Decimal('100')
                    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception:
        pass

    CommissionRecord.objects.get_or_create(
        placement_id=placement.id,
        defaults=dict(
            application_id=application.id,
            requisition_id=application.requisition_id,
            company_tenant_id=application.tenant_id,
            agency_tenant_id=application.agency_id,
            agency_relationship_id=agency_relationship_id,
            commission_model=commission_model,
            basis_source=basis_source,
            commission_rate=commission_rate,
            expected_amount=expected_amount,
            currency=currency,
            created_by=user.id,
        ),
    )


# ── Placement views ────────────────────────────────────────────────────────────

class PlacementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Placement.objects.filter(tenant_id=request.user.tenant_id)
        requisition_id = request.query_params.get('requisition_id')
        agency_id = request.query_params.get('agency_id')
        placement_status = request.query_params.get('placement_status')
        if requisition_id:
            qs = qs.filter(requisition_id=requisition_id)
        if agency_id:
            qs = qs.filter(agency_id=agency_id)
        if placement_status:
            qs = qs.filter(placement_status=placement_status)
        return success_response(data={
            'placements': PlacementSerializer(qs.order_by('-created_at')[:200], many=True).data
        })


class PlacementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        placement = _get_placement(pk, request.user.tenant_id)
        if not placement:
            return error_response('Placement not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data={'placement': PlacementSerializer(placement).data})

    def patch(self, request, pk):
        placement = _get_placement(pk, request.user.tenant_id)
        if not placement:
            return error_response('Placement not found.', status_code=status.HTTP_404_NOT_FOUND)

        allowed = {
            'placement_status', 'joining_date', 'joined_at',
            'offer_accepted_at', 'credited_recruiter_id', 'notes',
        }
        data = {k: v for k, v in request.data.items() if k in allowed}
        serializer = PlacementSerializer(placement, data=data, partial=True)
        if not serializer.is_valid():
            return error_response('Validation failed.', serializer.errors)
        serializer.save()
        return success_response(data={'placement': serializer.data})


class PlacementConfirmView(APIView):
    """Mark a placement as confirmed — the commercial milestone post-joining."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        placement = _get_placement(pk, request.user.tenant_id)
        if not placement:
            return error_response('Placement not found.', status_code=status.HTTP_404_NOT_FOUND)

        if placement.placement_status not in ('joined', 'pending_join', 'offer_accepted'):
            return error_response(
                'Placement can only be confirmed after offer acceptance or joining.',
            )

        placement.placement_status = 'placement_confirmed'
        placement.placement_confirmed_at = timezone.now()
        notes = request.data.get('notes', '')
        if notes:
            placement.notes = notes
        placement.save(update_fields=['placement_status', 'placement_confirmed_at', 'notes', 'updated_at'])

        # Advance commission to payment_due if it was pending
        commission = CommissionRecord.objects.filter(placement_id=placement.id).first()
        if commission and commission.payment_status in ('not_started', 'pending_invoice', 'invoice_expected'):
            commission.payment_status = 'payment_due'
            commission.save(update_fields=['payment_status', 'updated_at'])

        return success_response(
            data={'placement': PlacementSerializer(placement).data},
            message='Placement confirmed.',
        )


# ── Commission views ───────────────────────────────────────────────────────────

class CommissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, placement_id):
        commission = CommissionRecord.objects.filter(
            placement_id=placement_id,
            company_tenant_id=request.user.tenant_id,
        ).first()
        if not commission:
            return error_response('Commission record not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data={'commission': CommissionRecordSerializer(commission).data})

    def put(self, request, placement_id):
        """Create or update commission record for a placement."""
        placement = _get_placement(placement_id, request.user.tenant_id)
        if not placement:
            return error_response('Placement not found.', status_code=status.HTTP_404_NOT_FOUND)

        commission, _ = CommissionRecord.objects.get_or_create(
            placement_id=placement.id,
            defaults=dict(
                application_id=placement.application_id,
                requisition_id=placement.requisition_id,
                company_tenant_id=placement.tenant_id,
                agency_tenant_id=placement.agency_id,
                created_by=request.user.id,
            ),
        )
        allowed = {
            'commission_applicable', 'commission_model', 'basis_source',
            'commission_rate', 'commission_fixed_amount', 'expected_amount',
            'currency', 'payment_status', 'due_date', 'paid_date',
            'paid_amount', 'payment_notes',
        }
        data = {k: v for k, v in request.data.items() if k in allowed}
        serializer = CommissionRecordSerializer(commission, data=data, partial=True)
        if not serializer.is_valid():
            return error_response('Validation failed.', serializer.errors)
        serializer.save()
        return success_response(data={'commission': serializer.data})


class CommissionPaymentStatusView(APIView):
    """Update payment status and dates on a commission record."""
    permission_classes = [IsAuthenticated]

    def post(self, request, placement_id):
        commission = CommissionRecord.objects.filter(
            placement_id=placement_id,
            company_tenant_id=request.user.tenant_id,
        ).first()
        if not commission:
            return error_response('Commission record not found.', status_code=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('payment_status')
        valid_statuses = [s[0] for s in CommissionRecord.PAYMENT_STATUS_CHOICES]
        if new_status not in valid_statuses:
            return error_response(f'payment_status must be one of: {", ".join(valid_statuses)}')

        commission.payment_status = new_status
        update_fields = ['payment_status', 'updated_at']

        if new_status == 'paid':
            commission.paid_date = request.data.get('paid_date') or timezone.now().date()
            if request.data.get('paid_amount'):
                commission.paid_amount = request.data['paid_amount']
            update_fields += ['paid_date', 'paid_amount']

        if request.data.get('due_date'):
            commission.due_date = request.data['due_date']
            update_fields.append('due_date')

        if request.data.get('payment_notes'):
            commission.payment_notes = request.data['payment_notes']
            update_fields.append('payment_notes')

        commission.save(update_fields=update_fields)
        return success_response(
            data={'commission': CommissionRecordSerializer(commission).data},
            message='Payment status updated.',
        )


# ── Reminder views ─────────────────────────────────────────────────────────────

class CommissionReminderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, placement_id):
        commission = CommissionRecord.objects.filter(
            placement_id=placement_id,
            company_tenant_id=request.user.tenant_id,
        ).first()
        if not commission:
            return error_response('Commission record not found.', status_code=status.HTTP_404_NOT_FOUND)
        reminders = CommissionReminder.objects.filter(commission_record_id=commission.id)
        return success_response(data={
            'reminders': CommissionReminderSerializer(reminders, many=True).data
        })

    def post(self, request, placement_id):
        commission = CommissionRecord.objects.filter(
            placement_id=placement_id,
            company_tenant_id=request.user.tenant_id,
        ).first()
        if not commission:
            return error_response('Commission record not found.', status_code=status.HTTP_404_NOT_FOUND)

        reminder = CommissionReminder.objects.create(
            commission_record_id=commission.id,
            reminder_type=request.data.get('reminder_type', 'manual'),
            channel=request.data.get('channel', 'manual'),
            sent_by=request.user.id,
            note=request.data.get('note', ''),
            outcome=request.data.get('outcome', ''),
        )

        # Bump counter and timestamp on parent
        commission.reminder_count += 1
        commission.last_reminder_at = timezone.now()
        if commission.payment_status in ('not_started', 'pending_invoice', 'invoice_expected', 'payment_due'):
            commission.payment_status = 'reminder_sent'
        commission.save(update_fields=['reminder_count', 'last_reminder_at', 'payment_status', 'updated_at'])

        return success_response(
            data={'reminder': CommissionReminderSerializer(reminder).data},
            message='Reminder logged.',
            status_code=status.HTTP_201_CREATED,
        )
