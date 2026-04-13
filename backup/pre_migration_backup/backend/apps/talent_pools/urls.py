from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TalentPoolViewSet, TalentPoolMembershipViewSet

router = DefaultRouter()
router.register(r'pools', TalentPoolViewSet, basename='talent-pool')
router.register(r'memberships', TalentPoolMembershipViewSet, basename='talent-pool-membership')

urlpatterns = [
    path('', include(router.urls)),
]
