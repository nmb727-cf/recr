from rest_framework import serializers
from apps.hdc.models import (
    HiringCommittee, CommitteeMember,
    ComparisonSet, ComparisonCandidate,
    DecisionApproval,
    OfferRecommendation, OfferScenario,
    NegotiationCase, NegotiationRound,
    OfferReleasePacket, JoiningCase,
    HDCAuditLog
)
from apps.pipeline.models import Application

class CommitteeMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommitteeMember
        fields = '__all__'

class HiringCommitteeSerializer(serializers.ModelSerializer):
    member_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    members = CommitteeMemberSerializer(many=True, read_only=True)

    class Meta:
        model = HiringCommittee
        fields = '__all__'

    def create(self, validated_data):
        member_ids = list(dict.fromkeys(validated_data.pop('member_ids', [])))
        committee = HiringCommittee.objects.create(**validated_data)

        if member_ids:
            CommitteeMember.objects.bulk_create([
                CommitteeMember(
                    tenant_id=committee.tenant_id,
                    committee=committee,
                    user_id=user_id,
                )
                for user_id in member_ids
            ])
            if not committee.quorum_required or committee.quorum_required < 1:
                committee.quorum_required = len(member_ids)
                committee.save(update_fields=['quorum_required', 'updated_at'])

        return committee

    def update(self, instance, validated_data):
        member_ids = validated_data.pop('member_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if member_ids is not None:
            normalized_ids = list(dict.fromkeys(member_ids))
            existing_members = {str(member.user_id): member for member in instance.members.all()}
            desired = {str(user_id) for user_id in normalized_ids}

            for user_id in desired:
                if user_id not in existing_members:
                    CommitteeMember.objects.create(
                        tenant_id=instance.tenant_id,
                        committee=instance,
                        user_id=user_id,
                    )

            for user_id, member in existing_members.items():
                if user_id not in desired and not member.has_voted:
                    member.delete()

        return instance

class ComparisonCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComparisonCandidate
        fields = '__all__'

class DecisionApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionApproval
        fields = '__all__'

class ComparisonSetSerializer(serializers.ModelSerializer):
    candidate_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    candidates = ComparisonCandidateSerializer(many=True, read_only=True)

    class Meta:
        model = ComparisonSet
        fields = '__all__'

    def _resolve_application_id(self, comparison_set: ComparisonSet, candidate_id):
        app = Application.objects.filter(
            tenant_id=comparison_set.tenant_id,
            requisition_id=comparison_set.requisition_id,
            candidate_id=candidate_id,
            is_deleted=False,
        ).order_by('-created_at').first()
        if app:
            return app.id
        
        # If no application found, we must return a UUID. 
        # Using a dummy or null might be better if the field allows it, 
        # but the model says it's a UUIDField and db_index=True.
        # However, comparison requires an application.
        return None 

    def create(self, validated_data):
        candidate_ids = list(dict.fromkeys(validated_data.pop('candidate_ids', [])))
        comparison_set = ComparisonSet.objects.create(**validated_data)

        if candidate_ids:
            ComparisonCandidate.objects.bulk_create([
                ComparisonCandidate(
                    tenant_id=comparison_set.tenant_id,
                    comparison_set=comparison_set,
                    candidate_id=candidate_id,
                    application_id=self._resolve_application_id(comparison_set, candidate_id),
                )
                for candidate_id in candidate_ids
            ])

        return comparison_set

    def update(self, instance, validated_data):
        candidate_ids = validated_data.pop('candidate_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if candidate_ids is not None:
            normalized_ids = list(dict.fromkeys(candidate_ids))
            instance.candidates.exclude(candidate_id__in=normalized_ids).delete()

            existing_candidate_ids = {
                str(candidate.candidate_id)
                for candidate in instance.candidates.all()
            }
            missing_ids = [candidate_id for candidate_id in normalized_ids if str(candidate_id) not in existing_candidate_ids]
            if missing_ids:
                ComparisonCandidate.objects.bulk_create([
                    ComparisonCandidate(
                        tenant_id=instance.tenant_id,
                        comparison_set=instance,
                        candidate_id=candidate_id,
                        application_id=self._resolve_application_id(instance, candidate_id),
                    )
                    for candidate_id in missing_ids
                ])

        return instance

class OfferScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferScenario
        fields = '__all__'

class OfferRecommendationSerializer(serializers.ModelSerializer):
    scenarios = OfferScenarioSerializer(many=True, read_only=True)
    class Meta:
        model = OfferRecommendation
        fields = '__all__'

class NegotiationRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = NegotiationRound
        fields = '__all__'

class NegotiationCaseSerializer(serializers.ModelSerializer):
    rounds = NegotiationRoundSerializer(many=True, read_only=True)
    class Meta:
        model = NegotiationCase
        fields = '__all__'

class OfferReleasePacketSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferReleasePacket
        fields = '__all__'

class JoiningCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = JoiningCase
        fields = '__all__'

class HDCAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HDCAuditLog
        fields = '__all__'

class ApplicationHDCStatusSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    current_stage = serializers.CharField()
    progress_percentage = serializers.IntegerField()
    timeline = HDCAuditLogSerializer(many=True, read_only=True)
    
    # Flags for UI safety
    can_approve = serializers.BooleanField()
    can_release_offer = serializers.BooleanField()
    can_negotiate = serializers.BooleanField()
    can_confirm_joining = serializers.BooleanField()
