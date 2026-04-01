from django.urls import path
from apps.accounts import views

urlpatterns = [
    # Public endpoints
    path('register/company/', views.RegisterCompanyView.as_view(), name='register-company'),
    path('register/agency/', views.RegisterAgencyView.as_view(), name='register-agency'),
    path('register/candidate/', views.RegisterCandidateView.as_view(), name='register-candidate'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('refresh/', views.RefreshTokenView.as_view(), name='token-refresh'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('send-otp/', views.SendOTPView.as_view(), name='send-otp'),

    # Authenticated endpoints
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('onboarding/complete/', views.CompleteOnboardingView.as_view(), name='onboarding-complete'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.MeView.as_view(), name='me'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('mfa/enable/', views.MFAEnableView.as_view(), name='mfa-enable'),
    path('mfa/verify/', views.MFAVerifyView.as_view(), name='mfa-verify'),

    # Recruiter Intelligence
    path('recruiters/intelligence/', views.RecruiterIntelligenceListView.as_view(), name='recruiter-intelligence-list'),
    path('jobs/<uuid:requisition_id>/recruiter-recommendations/', views.JobRecruiterIntelligenceView.as_view(), name='job-recruiter-intelligence'),
]