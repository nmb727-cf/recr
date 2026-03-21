from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.documents.models import Document, OfferLetter
from apps.documents.serializers import DocumentSerializer, OfferLetterSerializer
from apps.core.responses import success_response, error_response


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Document.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        entity_type = request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        entity_id = request.query_params.get('entity_id')
        if entity_id:
            qs = qs.filter(entity_id=entity_id)

        document_type = request.query_params.get('document_type')
        if document_type:
            qs = qs.filter(document_type=document_type)

        return success_response(
            data={'documents': DocumentSerializer(qs, many=True).data},
            message="Documents retrieved.",
            meta={'total': qs.count()}
        )

    def post(self, request):
        serializer = DocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        document = serializer.save(
            tenant_id=request.user.tenant_id,
            uploaded_by=request.user.id,
            created_by=request.user.id,
        )
        return success_response(
            data={'document': DocumentSerializer(document).data},
            message="Document uploaded.",
            status_code=status.HTTP_201_CREATED
        )


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Document.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Document.DoesNotExist:
            return None

    def get(self, request, pk):
        document = self.get_object(request, pk)
        if not document:
            return error_response("Document not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'document': DocumentSerializer(document).data},
            message="Document retrieved."
        )

    def delete(self, request, pk):
        document = self.get_object(request, pk)
        if not document:
            return error_response("Document not found.", status_code=status.HTTP_404_NOT_FOUND)
        document.soft_delete()
        return success_response(
            message="Document deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class DocumentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        document = Document.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False
        ).first()
        if not document:
            return error_response("Document not found.", status_code=status.HTTP_404_NOT_FOUND)

        # TODO: Generate presigned MinIO URL
        return success_response(
            data={
                'download_url': document.file_url,
                'filename': document.filename,
                'expires_at': None,
            },
            message="Download URL generated."
        )


class OfferLetterListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = OfferLetter.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        application_id = request.query_params.get('application_id')
        if application_id:
            qs = qs.filter(application_id=application_id)

        return success_response(
            data={'offers': OfferLetterSerializer(qs, many=True).data},
            message="Offer letters retrieved.",
            meta={'total': qs.count()}
        )

    def post(self, request):
        serializer = OfferLetterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        offer = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            status='draft',
        )
        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter created.",
            status_code=status.HTTP_201_CREATED
        )


class OfferLetterDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return OfferLetter.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except OfferLetter.DoesNotExist:
            return None

    def get(self, request, pk):
        offer = self.get_object(request, pk)
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter retrieved."
        )


class OfferLetterSendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk, tenant_id=request.user.tenant_id, is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)

        if offer.status not in ['draft', 'approved']:
            return error_response("Only draft or approved offers can be sent.")

        offer.status = 'sent'
        offer.sent_at = timezone.now()
        offer.save(update_fields=['status', 'sent_at', 'updated_at'])

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter sent."
        )


class OfferLetterApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk, tenant_id=request.user.tenant_id, is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)

        offer.status = 'approved'
        offer.approved_by = request.user.id
        offer.approved_at = timezone.now()
        offer.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter approved."
        )


class OfferLetterRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk, tenant_id=request.user.tenant_id, is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer letter not found.", status_code=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        offer.status = 'revoked'
        offer.revoked_at = timezone.now()
        offer.revoke_reason = reason
        offer.save(update_fields=['status', 'revoked_at', 'revoke_reason', 'updated_at'])

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer letter revoked."
        )


class CandidateOfferAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk,
            candidate_id=request.user.id,
            status='sent',
            is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer not found.", status_code=status.HTTP_404_NOT_FOUND)

        offer.status = 'accepted'
        offer.accepted_at = timezone.now()
        offer.save(update_fields=['status', 'accepted_at', 'updated_at'])

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer accepted. Congratulations!"
        )


class CandidateOfferRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = OfferLetter.objects.filter(
            id=pk,
            candidate_id=request.user.id,
            status='sent',
            is_deleted=False
        ).first()
        if not offer:
            return error_response("Offer not found.", status_code=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        offer.status = 'rejected'
        offer.rejected_at = timezone.now()
        offer.rejection_reason = reason
        offer.save(update_fields=['status', 'rejected_at', 'rejection_reason', 'updated_at'])

        return success_response(
            data={'offer': OfferLetterSerializer(offer).data},
            message="Offer rejected."
        )
