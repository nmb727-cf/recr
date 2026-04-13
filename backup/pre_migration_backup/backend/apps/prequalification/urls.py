from django.urls import path
from apps.prequalification import views

urlpatterns = [
    # ── Forms ─────────────────────────────────────────────────────────────────
    path('forms/',           views.PrequalFormListView.as_view(),     name='prequal-form-list'),
    path('forms/<uuid:pk>/', views.PrequalFormDetailView.as_view(),   name='prequal-form-detail'),

    # ── Sections ──────────────────────────────────────────────────────────────
    path('sections/',           views.PrequalSectionListView.as_view(),   name='prequal-section-list'),
    path('sections/<uuid:pk>/', views.PrequalSectionDetailView.as_view(), name='prequal-section-detail'),

    # ── Questions ─────────────────────────────────────────────────────────────
    path('questions/',           views.PrequalQuestionListView.as_view(),   name='prequal-question-list'),
    path('questions/<uuid:pk>/', views.PrequalQuestionDetailView.as_view(), name='prequal-question-detail'),

    # ── Rules ─────────────────────────────────────────────────────────────────
    path('rules/',           views.PrequalRuleListView.as_view(),   name='prequal-rule-list'),
    path('rules/<uuid:pk>/', views.PrequalRuleDetailView.as_view(), name='prequal-rule-detail'),

    # ── Responses ─────────────────────────────────────────────────────────────
    path('responses/', views.PrequalResponseListView.as_view(), name='prequal-response-list'),
]
