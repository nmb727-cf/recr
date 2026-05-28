from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.core.responses import success_response
from apps.translations.models import TranslationOverride


class TranslationOverrideListView(APIView):
    """
    Returns active DB-backed translation overrides for a given language.

    The frontend merges these on top of its static JSON translation files,
    allowing corrections and tenant-custom labels without a frontend deploy.

    Hierarchy: tenant override > global override > static JSON

    Query params:
        lang    (required) — language code, e.g. "en", "hi"
        module  (optional) — filter by module, e.g. "sidebar", "candidates"
        tenant  (optional) — UUID; when provided also returns tenant-specific overrides
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        lang = request.query_params.get('lang', 'en')
        module = request.query_params.get('module')
        tenant_id = request.query_params.get('tenant')

        # Start with global overrides
        qs = TranslationOverride.objects.filter(
            language_code=lang,
            is_active=True,
            tenant_id__isnull=True,
        )

        if module:
            qs = qs.filter(module=module)

        overrides = {obj.key: obj.value for obj in qs}

        # Layer tenant-specific overrides on top only when caller is authorized
        if tenant_id:
            user = getattr(request, 'user', None)
            is_authenticated = bool(user and getattr(user, 'is_authenticated', False))
            is_super_admin = bool(user and getattr(user, 'role', '') == 'super_admin')
            user_tenant_id = str(getattr(user, 'tenant_id', '')) if user else ''

            if not is_authenticated:
                return success_response(
                    data={
                        'language': lang,
                        'overrides': overrides,
                        'count': len(overrides),
                        'warning': 'Tenant overrides require authentication.',
                    },
                    message='Global overrides retrieved.',
                )

            if not is_super_admin and user_tenant_id != str(tenant_id):
                return success_response(
                    data={
                        'language': lang,
                        'overrides': overrides,
                        'count': len(overrides),
                        'warning': 'Tenant override access denied for requested tenant.',
                    },
                    message='Global overrides retrieved.',
                )

            tenant_qs = TranslationOverride.objects.filter(
                language_code=lang,
                is_active=True,
                tenant_id=tenant_id,
            )
            if module:
                tenant_qs = tenant_qs.filter(module=module)
            for obj in tenant_qs:
                overrides[obj.key] = obj.value  # tenant wins

        return success_response(data={
            'language': lang,
            'overrides': overrides,
            'count': len(overrides),
        })
