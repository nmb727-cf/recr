"""
Public URL patterns for the candidate claim flow.
Mounted at /api/v1/candidates/claim/ in config/urls.py.
"""
from django.urls import path
from apps.candidates.claim_views import CandidateClaimVerifyView

urlpatterns = [
    # GET  → verify token, return prefilled identity data
    # POST → authenticated candidate links their account to the candidate record
    path('<str:token>/', CandidateClaimVerifyView.as_view(), name='candidate-claim'),
]
