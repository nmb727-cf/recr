from django.urls import path
from apps.translations.views import TranslationOverrideListView

urlpatterns = [
    path('overrides/', TranslationOverrideListView.as_view(), name='translation-overrides'),
]
