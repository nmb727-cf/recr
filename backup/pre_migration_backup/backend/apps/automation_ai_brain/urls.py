from django.urls import path
from .views import (
    AutomationAIDecisionsView,
    AutomationAIRecommendationsView,
    AutomationAIPredictionsView,
    AutomationAIContextView,
    AutomationAIRecalculateView
)

urlpatterns = [
    path('decisions/', AutomationAIDecisionsView.as_view(), name='ai-decisions'),
    path('recommendations/', AutomationAIRecommendationsView.as_view(), name='ai-recommendations'),
    path('predictions/', AutomationAIPredictionsView.as_view(), name='ai-predictions'),
    path('context/', AutomationAIContextView.as_view(), name='ai-context'),
    path('recalculate/', AutomationAIRecalculateView.as_view(), name='ai-recalculate'),
]
