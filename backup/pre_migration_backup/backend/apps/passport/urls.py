from django.urls import path
from apps.passport import views
from apps.passport.withdrawal_views import DataWithdrawalView
from apps.passport.candidate_sync_views import MyCandidateView

urlpatterns = [
    # Candidate passport management
    path('my-passport/', views.MyPassportView.as_view(), name='my-passport'),
    path('my-passport/access-log/', views.MyPassportAccessLogView.as_view(), name='passport-access-log'),
    path('my-passport/revoke-access/', views.MyPassportRevokeAccessView.as_view(), name='passport-revoke-access'),
    path('my-passport/revoke-all/', views.MyPassportRevokeAllView.as_view(), name='passport-revoke-all'),
    path('my-passport/share-link/', views.MyPassportShareLinkView.as_view(), name='passport-share-link'),
    path('my-passport/regenerate-link/', views.MyPassportRegenerateLinkView.as_view(), name='passport-regenerate-link'),

    # Public access
    path('public/<str:token>/', views.PublicPassportView.as_view(), name='passport-public'),

    # Linked candidate — prefill source for onboarding (GET) + candidate-model field update (PATCH)
    path('my-candidate/', MyCandidateView.as_view(), name='passport-my-candidate'),

    # Import by company/agency
    path('import/', views.PassportImportView.as_view(), name='passport-import'),

    # Data Withdrawal
    path('withdraw-data/', DataWithdrawalView.as_view(), name='withdraw-data'),
    path('withdrawal-status/', DataWithdrawalView.as_view(), name='withdrawal-status'),
]
