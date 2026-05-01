from rest_framework import serializers
from apps.documents.models import Document, OfferLetter


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'tenant_id', 'entity_type', 'entity_id',
            'document_type', 'title', 'file_url', 'filename',
            'file_size', 'mime_type', 'version', 'is_current',
            'is_verified', 'verified_by', 'verified_at',
            'expires_at', 'notes', 'uploaded_by',
            'created_at', 'updated_at', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'is_verified', 'verified_by', 'verified_at',
        ]


class OfferLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferLetter
        fields = [
            'id', 'tenant_id', 'application_id', 'candidate_id',
            'title', 'joining_date', 'offered_salary', 'currency',
            'compensation_details', 'status', 'document_url',
            'version', 'parent_offer_id', 'expires_at',
            'sent_at', 'accepted_at', 'rejected_at', 'rejection_reason',
            'revoked_at', 'revoke_reason', 'approved_by', 'approved_at',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'sent_at', 'accepted_at', 'rejected_at',
            'revoked_at', 'approved_by', 'approved_at',
        ]

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        creating = instance is None
        data = attrs

        if creating:
            required_fields = ['application_id', 'candidate_id', 'offered_salary', 'currency', 'joining_date']
            missing = [field for field in required_fields if data.get(field) in (None, '')]
            if missing:
                raise serializers.ValidationError(
                    {field: 'This field is required.' for field in missing}
                )

        offered_salary = data.get('offered_salary')
        if offered_salary is not None and offered_salary <= 0:
            raise serializers.ValidationError({'offered_salary': 'Must be greater than 0.'})

        expires_at = data.get('expires_at')
        joining_date = data.get('joining_date') or (instance.joining_date if instance else None)
        if expires_at is not None and joining_date is not None and expires_at.date() < joining_date:
            raise serializers.ValidationError({'expires_at': 'Expiry must be on or after joining date.'})

        return attrs
