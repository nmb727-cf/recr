from django.urls import path
from apps.documents import views

urlpatterns = [
    # Documents
    path('documents/', views.DocumentListView.as_view(), name='document-list'),
    path('documents/<uuid:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<uuid:pk>/download/', views.DocumentDownloadView.as_view(), name='document-download'),

    # Offer letters
    path('offers/', views.OfferLetterListView.as_view(), name='offer-list'),
    path('offers/<uuid:pk>/', views.OfferLetterDetailView.as_view(), name='offer-detail'),
    path('offers/<uuid:pk>/submit-approval/', views.OfferLetterSubmitApprovalView.as_view(), name='offer-submit-approval'),
    path('offers/<uuid:pk>/send/', views.OfferLetterSendView.as_view(), name='offer-send'),
    path('offers/<uuid:pk>/approve/', views.OfferLetterApproveView.as_view(), name='offer-approve'),
    path('offers/<uuid:pk>/negotiate/', views.OfferLetterNegotiateView.as_view(), name='offer-negotiate'),
    path('offers/<uuid:pk>/revoke/', views.OfferLetterRevokeView.as_view(), name='offer-revoke'),

    # Candidate offer actions
    path('candidate/offers/<uuid:pk>/accept/', views.CandidateOfferAcceptView.as_view(), name='candidate-offer-accept'),
    path('candidate/offers/<uuid:pk>/reject/', views.CandidateOfferRejectView.as_view(), name='candidate-offer-reject'),
]
