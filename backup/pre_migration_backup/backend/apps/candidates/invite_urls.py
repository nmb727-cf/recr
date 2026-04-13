from django.urls import path
from apps.candidates.invite_views import InviteLinkListView, InviteLinkDeactivateView

urlpatterns = [
    path('', InviteLinkListView.as_view(), name='invite-link-list'),
    path('<uuid:pk>/deactivate/', InviteLinkDeactivateView.as_view(), name='invite-link-deactivate'),
]
