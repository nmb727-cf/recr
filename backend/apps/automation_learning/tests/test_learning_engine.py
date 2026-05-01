import uuid
from django.test import TestCase
from django.utils import timezone
from apps.automation_learning.models import (
    AutomationLearningEvent,
    AutomationLearningPattern,
    AutomationOptimizationSuggestion,
    AutomationLearningModel
)
from apps.automation_learning.automation_self_learning_engine import AutomationSelfLearningEngine

class AutomationLearningEngineTest(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.workflow_id = uuid.uuid4()
        self.engine = AutomationSelfLearningEngine()

    def test_capture_learning_event(self):
        event = self.engine.capture_learning_event(
            tenant_id=self.tenant_id,
            workflow_id=self.workflow_id,
            event_type='workflow_failure',
            event_data={'error': 'timeout'},
            outcome='failed'
        )
        self.assertEqual(event.event_type, 'workflow_failure')
        self.assertEqual(AutomationLearningEvent.objects.count(), 1)

    def test_detect_patterns(self):
        # Create 6 failure events to trigger pattern detection
        for _ in range(6):
            self.engine.capture_learning_event(
                tenant_id=self.tenant_id,
                workflow_id=self.workflow_id,
                event_type='workflow_failure'
            )
        
        patterns = self.engine.detect_patterns(self.tenant_id)
        self.assertTrue(len(patterns) > 0)
        self.assertEqual(patterns[0].pattern_type, 'repeated_failure')

    def test_generate_optimization_suggestions(self):
        # First detect patterns
        for _ in range(6):
            self.engine.capture_learning_event(
                tenant_id=self.tenant_id,
                workflow_id=self.workflow_id,
                event_type='workflow_failure'
            )
        self.engine.detect_patterns(self.tenant_id)
        
        suggestions = self.engine.generate_optimization_suggestions(self.tenant_id)
        self.assertTrue(len(suggestions) > 0)
        self.assertEqual(suggestions[0].suggestion_type, 'add_fallback')

    def test_train_learning_models(self):
        model = self.engine.train_learning_models(self.tenant_id, 'failure_prediction')
        self.assertEqual(model.model_type, 'failure_prediction')
        self.assertTrue(model.accuracy_score > 0)
        self.assertIsNotNone(model.last_trained_at)

    def test_predict_failures(self):
        prediction = self.engine.predict_failures(self.tenant_id, self.workflow_id)
        self.assertIn('failure_probability', prediction)

    def test_predict_delays(self):
        prediction = self.engine.predict_delays(self.tenant_id, self.workflow_id)
        self.assertIn('delay_probability', prediction)
