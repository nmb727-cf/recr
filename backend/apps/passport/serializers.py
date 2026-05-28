from rest_framework import serializers
from apps.passport.models import TalentPassport, ResumeVersion, PassportAccessLog, PassportRevocation


class ResumeVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeVersion
        fields = [
            'id', 'passport_id', 'version_number', 'file_url', 'filename',
            'file_size', 'mime_type', 'is_current', 'label', 'uploaded_at',
        ]
        read_only_fields = ['id', 'passport_id', 'uploaded_at']


class PassportAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassportAccessLog
        fields = [
            'id', 'passport_id', 'accessed_by_user_id', 'accessed_by_tenant_id',
            'access_type', 'ip_address', 'imported_to_system',
            'revoked_at', 'accessed_at',
        ]
        read_only_fields = ['id', 'accessed_at']


class TalentPassportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentPassport
        fields = [
            'id', 'user_id', 'candidate_id', 'passport_number',
            'is_active', 'headline', 'summary', 'profile_photo_url',
            'cover_image_url', 'video_intro_url',
            'current_title', 'current_company',
            'current_location_city', 'current_location_country',
            'experience_years', 'current_cv_url', 'current_cv_filename',
            'current_cv_uploaded_at',
            'work_history', 'education', 'skills', 'certifications',
            'projects', 'publications', 'awards', 'volunteer_work',
            'test_scores', 'languages', 'references',
            'linkedin_url', 'github_url', 'portfolio_url',
            'twitter_url', 'behance_url', 'dribbble_url',
            'preferred_locations', 'preferred_work_mode',
            'preferred_job_types', 'preferred_industries',
            'expected_salary_min', 'expected_salary_max', 'salary_currency',
            'notice_period_days', 'availability_date',
            'is_actively_looking', 'open_to_work',
            'identity_verified', 'background_verified',
            'employment_verified', 'education_verified',
            'heat_score', 'completeness_score', 'market_demand_score',
            'visibility_settings', 'view_count', 'last_viewed_at',
            'created_at', 'updated_at',
            'metadata',
        ]
        read_only_fields = [
            'id', 'user_id', 'passport_number', 'share_link_token',
            'created_at', 'updated_at', 'view_count',
            'identity_verified', 'background_verified',
            'heat_score', 'completeness_score', 'market_demand_score',
        ]


class TalentPassportPublicSerializer(serializers.ModelSerializer):
    """Limited serializer for public passport view — respects visibility settings"""
    class Meta:
        model = TalentPassport
        fields = [
            'id', 'passport_number', 'headline', 'summary',
            'profile_photo_url', 'cover_image_url', 'video_intro_url',
            'current_title', 'current_company',
            'current_location_city', 'current_location_country',
            'experience_years', 'current_cv_url',
            'skills', 'work_history', 'education',
            'certifications', 'projects', 'languages',
            'linkedin_url', 'github_url', 'portfolio_url',
            'twitter_url', 'behance_url', 'dribbble_url',
            'notice_period_days', 'preferred_work_mode',
            'is_actively_looking', 'open_to_work',
            'identity_verified', 'background_verified',
            'heat_score', 'completeness_score',
            'publications', 'awards', 'volunteer_work',
        ]
