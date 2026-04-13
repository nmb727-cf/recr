from django.urls import include, path


urlpatterns = [
    path('', include('apps.orchestration_center.api.urls')),
]
