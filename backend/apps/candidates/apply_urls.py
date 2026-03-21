from django.urls import path
from apps.candidates.invite_views import PublicApplyFormView

urlpatterns = [
    path('<str:token>/', PublicApplyFormView.as_view(), name='apply-form'),
    path('<str:token>/submit/', PublicApplyFormView.as_view(), name='apply-submit'),
]
