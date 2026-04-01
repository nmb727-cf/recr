"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/apply/', include('apps.candidates.apply_urls')),
    path('api/v1/candidates/claim/', include('apps.candidates.claim_urls')),
    path('api/v1/organisation/invite-links/', include('apps.candidates.invite_urls')),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/organisation/', include('apps.organisations.urls')),
    path('api/v1/organisations/', include('apps.organisations.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
    path('api/v1/candidates/', include('apps.candidates.urls')),
    path('api/v1/pipeline/', include('apps.pipeline.urls')),
    path('api/v1/agencies/', include('apps.agencies.urls')),
    path('api/v1/interviews/', include('apps.interviews.urls')),
    path('api/v1/candidate/interviews/', include('apps.interviews.candidate_urls')),
    path('api/v1/passport/', include('apps.passport.urls')),
    path('api/v1/communications/', include('apps.communications.urls')),
    path('api/v1/documents/', include('apps.documents.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/automation/', include('apps.automation.urls')),
    path('api/v1/rbac/', include('apps.rbac.urls')),
    path('api/v1/translations/', include('apps.translations.urls')),
    path('api/v1/candidate/', include('apps.jobs.candidate_urls')),
    path('api/v1/talent-pools/', include('apps.talent_pools.urls')),
    path('api/v1/prequalification/', include('apps.prequalification.urls')),
    path('api/v1/system/', include('apps.module_registry.urls')),
    path('api/v1/intelligence/', include('apps.orchestration_center.urls')),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema")),
     path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
