from django.urls import path
from .views import (
    AutomationLearningOverviewView,
    AutomationLearningPatternsView,
    AutomationLearningSuggestionsView,
    AutomationLearningPredictionsView,
    AutomationLearningModelsView,
    AutomationLearningRetrainView,
    AutomationCenterLearningSummaryView
)

urlpatterns = [
    path('overview/', AutomationLearningOverviewView.as_view(), name='learning-overview'),
    path('patterns/', AutomationLearningPatternsView.as_view(), name='learning-patterns'),
    path('suggestions/', AutomationLearningSuggestionsView.as_view(), name='learning-suggestions'),
    path('predictions/', AutomationLearningPredictionsView.as_view(), name='learning-predictions'),
    path('models/', AutomationLearningModelsView.as_view(), name='learning-models'),
    path('retrain/', AutomationLearningRetrainView.as_view(), name='learning-retrain'),
    path('center-summary/', AutomationCenterLearningSummaryView.as_view(), name='center-summary'),
]
