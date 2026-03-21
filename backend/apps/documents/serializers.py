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
            'sent_at', 'accepted_at', 'rejected_at', 'rejection_reason',
            'revoked_at', 'revoke_reason', 'approved_by', 'approved_at',
            'created_at', 'updated_at', 'created_by', 'metadata',
        ]
        read_only_fields = [
            'id', 'tenant_id', 'created_at', 'updated_at',
            'sent_at', 'accepted_at', 'rejected_at',
            'revoked_at', 'approved_by', 'approved_at',
        ]