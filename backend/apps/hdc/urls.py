from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.hdc.views import (
    HiringCommitteeViewSet, ComparisonSetViewSet,
    DecisionApprovalViewSet,
    OfferRecommendationViewSet, NegotiationCaseViewSet,
    OfferReleasePacketViewSet, JoiningCaseViewSet,
    DashboardStatsView, ApplicationHDCStatusView
)

router = DefaultRouter()
router.register(r'committees', HiringCommitteeViewSet, basename='hdc-committee')
router.register(r'comparisons', ComparisonSetViewSet, basename='hdc-comparison')
router.register(r'approvals', DecisionApprovalViewSet, basename='hdc-approval')
router.register(r'offer-recommendations', OfferRecommendationViewSet, basename='hdc-offer-rec')
router.register(r'negotiations', NegotiationCaseViewSet, basename='hdc-negotiation')
router.register(r'offer-release', OfferReleasePacketViewSet, basename='hdc-offer-release')
router.register(r'joining', JoiningCaseViewSet, basename='hdc-joining')

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='hdc-stats'),
    path('status/<uuid:application_id>/', ApplicationHDCStatusView.as_view(), name='hdc-app-status'),
    path('', include(router.urls)),
]
