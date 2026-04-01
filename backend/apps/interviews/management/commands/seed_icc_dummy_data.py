import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import CustomUser
from apps.candidates.models import Candidate, CandidateProfile
from apps.interviews.models import (
    Interview,
    InterviewAvailabilityBlock,
    InterviewAvailabilityProfile,
    InterviewCalendarConnection,
    InterviewDecision,
    InterviewDecisionHistory,
    InterviewExecutionMapping,
    InterviewFeedback,
    InterviewFlow,
    InterviewIntegrationProvider,
    InterviewPanelist,
    InterviewQuestion,
    InterviewQuestionAttachment,
    InterviewQuestionBank,
    InterviewQuestionGroup,
    InterviewQuestionGroupItem,
    InterviewSchedulingLink,
    InterviewScorecardTemplate,
    InterviewTemplate,
    InterviewTenantProviderConnection,
    InterviewType,
)
from apps.jobs.models import JobRequisition, JobStage
from apps.pipeline.models import Application


MODULE_ID = "ICC-E2E-DUMMY-DATA-01"
SEED_NAMESPACE = uuid.UUID("3bb99c1c-3ccf-45d5-b7bf-76c8901f9001")
TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
BASE_TIME = timezone.now()


def seed_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, key)


def as_decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


@dataclass
class SeedCandidate:
    slug: str
    first_name: str
    last_name: str
    email: str
    title: str
    company: str
    city: str
    skills: list[str]
    experience_years: float
    summary: str
    resume_url: str


class Command(BaseCommand):
    help = "Seed realistic Interview Command Center dummy data for end-to-end validation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id",
            dest="tenant_id",
            default=str(TENANT_ID),
            help="Tenant UUID to seed into. Defaults to the shared ICC demo tenant.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.tenant_id = uuid.UUID(str(options["tenant_id"]))
        self.now = BASE_TIME

        self.users = self.seed_users()
        self.types = self.seed_types()
        self.scorecards = self.seed_scorecards()
        self.ai_templates = self.seed_ai_templates()
        self.unified_templates = self.seed_unified_templates()
        self.questions = self.seed_question_bank()
        self.jobs = self.seed_jobs()
        self.candidates = self.seed_candidates()
        self.applications = self.seed_applications()
        self.flows = self.seed_flows()
        self.seed_integrations()
        self.seed_scheduling_setup()
        self.interviews = self.seed_interviews()
        self.refresh_usage_metadata()

        summary = {
            "types": InterviewType.objects.filter(is_deleted=False, is_active=True).count(),
            "ai_templates": InterviewTemplate.objects.filter(
                tenant_id=self.tenant_id,
                is_deleted=False,
                name__in=[
                    "Sales AI Screening",
                    "Customer Support Behavioral AI Screen",
                    "Junior Developer AI Technical Screen",
                    "Finance Analyst Async Text Screen",
                    "Leadership Behavioral One-Way Video",
                ],
            ).count(),
            "scorecards": InterviewScorecardTemplate.objects.filter(
                tenant_id=self.tenant_id,
                is_deleted=False,
            ).count(),
            "flows": InterviewFlow.objects.filter(tenant_id=self.tenant_id, is_deleted=False).count(),
            "jobs": JobRequisition.objects.filter(tenant_id=self.tenant_id, is_deleted=False).count(),
            "applications": Application.objects.filter(tenant_id=self.tenant_id, is_deleted=False).count(),
            "interviews": Interview.objects.filter(tenant_id=self.tenant_id, is_deleted=False).count(),
            "question_bank": InterviewQuestionBank.objects.filter(
                tenant_id=self.tenant_id,
                is_deleted=False,
            ).count(),
            "question_groups": InterviewQuestionGroup.objects.filter(
                tenant_id=self.tenant_id,
                is_deleted=False,
            ).count(),
        }

        self.stdout.write(self.style.SUCCESS("Interview Command Center dummy data seeded."))
        for key, value in summary.items():
            self.stdout.write(f"  - {key}: {value}")

    def seed_users(self):
        users = {}
        people = [
            ("tenant_admin", "icc-admin@talentos.example.com", "Tenant", "Admin", "tenant_admin"),
            ("recruiter", "maya.recruiter@talentos.example.com", "Maya", "Sharma", "recruiter"),
            ("scheduler", "nikhil.scheduler@talentos.example.com", "Nikhil", "Verma", "recruiter"),
            ("hiring_manager", "vivek.hm@talentos.example.com", "Vivek", "Raman", "hiring_manager"),
            ("hr_manager", "sana.hr@talentos.example.com", "Sana", "Qureshi", "hr_manager"),
            ("interviewer_1", "ananya.tech@talentos.example.com", "Ananya", "Kulkarni", "interviewer"),
            ("interviewer_2", "rohit.arch@talentos.example.com", "Rohit", "Deshmukh", "interviewer"),
            ("panelist_1", "kavya.panel@talentos.example.com", "Kavya", "Menon", "interviewer"),
            ("panelist_2", "aditya.panel@talentos.example.com", "Aditya", "Singh", "interviewer"),
            ("leadership_panel", "reena.exec@talentos.example.com", "Reena", "Sethi", "interviewer"),
        ]
        for slug, email, first_name, last_name, role in people:
            user, _ = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "id": seed_uuid(f"user:{slug}"),
                    "tenant_id": self.tenant_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role,
                    "is_active": True,
                    "is_staff": role in {"tenant_admin", "hr_manager", "recruiter"},
                    "timezone": "Asia/Kolkata",
                    "email_verified": True,
                },
            )
            for field, value in {
                "tenant_id": self.tenant_id,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_active": True,
                "timezone": "Asia/Kolkata",
                "email_verified": True,
            }.items():
                setattr(user, field, value)
            user.set_password("testpass123")
            user.save()
            users[slug] = user
        return users

    def seed_types(self):
        required = {
            "ai_screening": {"name": "AI Screening", "mode": "native"},
            "ai_behavioral": {"name": "AI Behavioral", "mode": "native"},
            "ai_technical": {"name": "AI Technical", "mode": "native"},
            "async_text": {"name": "Async Text", "mode": "async"},
            "async_audio": {"name": "Async Audio", "mode": "async"},
            "one_way_video": {"name": "One Way Video", "mode": "native"},
            "technical_interview": {"name": "Technical Interview", "mode": "manual"},
            "coding_interview": {"name": "Coding Interview", "mode": "native"},
            "system_design": {"name": "System Design", "mode": "manual"},
            "hr_interview": {"name": "HR Interview", "mode": "manual"},
            "panel": {"name": "Panel Interview", "mode": "manual"},
            "leadership": {"name": "Leadership Interview", "mode": "manual"},
            "final_round": {"name": "Final Round", "mode": "manual"},
            "recruiter_screening": {"name": "Recruiter Screening", "mode": "manual"},
            "case_study": {"name": "Case Study", "mode": "manual"},
            "take_home_assignment": {"name": "Take Home Assignment", "mode": "async"},
            "role_play": {"name": "Role Play", "mode": "manual"},
            "presentation": {"name": "Presentation Round", "mode": "manual"},
        }
        rows = {}
        for code, data in required.items():
            obj, _ = InterviewType.objects.get_or_create(
                code=code,
                defaults={
                    "name": data["name"],
                    "description": f"{data['name']} seeded for {MODULE_ID} validation.",
                    "execution_mode": data["mode"],
                    "configurable": True,
                    "is_active": True,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
            obj.name = data["name"]
            obj.execution_mode = data["mode"]
            obj.is_active = True
            obj.metadata = {**(obj.metadata or {}), "seed_module_id": MODULE_ID}
            obj.save(update_fields=["name", "execution_mode", "is_active", "metadata", "updated_at"])
            rows[code] = obj
        return rows

    def seed_scorecards(self):
        scorecards = {}
        definitions = [
            {
                "name": "AI Screening Scorecard",
                "interview_type": "ai_screening",
                "description": "Rubric for AI-led qualification and eligibility screening.",
                "attributes": [
                    ("Communication", 25, "scale_1_5", True),
                    ("Eligibility Fit", 25, "scale_1_5", True),
                    ("Motivation", 20, "scale_1_5", True),
                    ("Role Alignment", 30, "scale_1_5", True),
                ],
                "metadata": {
                    "scoring_logic": {
                        "ai_scoring_enabled": True,
                        "manual_scoring_enabled": True,
                        "blend_mode": "blended",
                        "ai_weight": 60,
                        "manual_weight": 40,
                    },
                    "recommendation_logic": {"pass_threshold": 75, "reject_threshold": 45},
                },
            },
            {
                "name": "Technical Scorecard",
                "interview_type": "technical_interview",
                "description": "Engineering rubric for technical rounds and code walkthroughs.",
                "attributes": [
                    ("Problem Solving", 30, "scale_1_5", True),
                    ("Technical Depth", 30, "scale_1_5", True),
                    ("Code Quality", 20, "scale_1_5", True),
                    ("Communication", 20, "scale_1_5", True),
                ],
                "metadata": {
                    "scoring_logic": {
                        "ai_scoring_enabled": False,
                        "manual_scoring_enabled": True,
                        "blend_mode": "human_only",
                        "ai_weight": 0,
                        "manual_weight": 100,
                    },
                    "recommendation_logic": {"pass_threshold": 78, "reject_threshold": 45},
                },
            },
            {
                "name": "HR Scorecard",
                "interview_type": "hr_interview",
                "description": "HR round rubric covering communication, compensation fit, and policy readiness.",
                "attributes": [
                    ("Communication", 35, "scale_1_5", True),
                    ("Culture Fit", 25, "scale_1_5", True),
                    ("Compensation Alignment", 20, "scale_1_5", True),
                    ("Policy Readiness", 20, "yes_no", True),
                ],
                "metadata": {
                    "scoring_logic": {
                        "ai_scoring_enabled": False,
                        "manual_scoring_enabled": True,
                        "blend_mode": "human_only",
                        "ai_weight": 0,
                        "manual_weight": 100,
                    },
                    "recommendation_logic": {"pass_threshold": 72, "reject_threshold": 40},
                },
            },
            {
                "name": "Panel Scorecard",
                "interview_type": "panel",
                "description": "Multi-interviewer panel rubric with combined recommendation support.",
                "attributes": [
                    ("Leadership", 25, "scale_1_5", True),
                    ("Collaboration", 20, "scale_1_5", True),
                    ("Problem Solving", 25, "scale_1_5", True),
                    ("Executive Presence", 30, "scale_1_5", True),
                ],
                "metadata": {
                    "scoring_logic": {
                        "ai_scoring_enabled": True,
                        "manual_scoring_enabled": True,
                        "blend_mode": "blended",
                        "ai_weight": 30,
                        "manual_weight": 70,
                    },
                    "recommendation_logic": {"pass_threshold": 80, "reject_threshold": 50},
                },
            },
            {
                "name": "Behavioral Scorecard",
                "interview_type": "ai_behavioral",
                "description": "Behavioral competency rubric for support and leadership screens.",
                "attributes": [
                    ("Behavioral Fit", 30, "scale_1_5", True),
                    ("Empathy", 20, "scale_1_5", True),
                    ("Collaboration", 25, "scale_1_5", True),
                    ("Conflict Handling", 25, "scale_1_5", True),
                ],
                "metadata": {
                    "scoring_logic": {
                        "ai_scoring_enabled": True,
                        "manual_scoring_enabled": True,
                        "blend_mode": "blended",
                        "ai_weight": 65,
                        "manual_weight": 35,
                    },
                    "recommendation_logic": {"pass_threshold": 74, "reject_threshold": 42},
                },
            },
            {
                "name": "Final Round Scorecard",
                "interview_type": "final_round",
                "description": "Final-stage decision scorecard for executive and offer readiness.",
                "attributes": [
                    ("Business Impact", 30, "scale_1_5", True),
                    ("Stakeholder Confidence", 25, "scale_1_5", True),
                    ("Leadership", 25, "scale_1_5", True),
                    ("Decision Readiness", 20, "pass_fail", True),
                ],
                "metadata": {
                    "scoring_logic": {
                        "ai_scoring_enabled": True,
                        "manual_scoring_enabled": True,
                        "blend_mode": "blended",
                        "ai_weight": 40,
                        "manual_weight": 60,
                    },
                    "recommendation_logic": {"pass_threshold": 82, "reject_threshold": 48},
                },
            },
        ]
        for definition in definitions:
            recommendation_logic = definition["metadata"]["recommendation_logic"]
            obj, _ = InterviewScorecardTemplate.objects.get_or_create(
                tenant_id=self.tenant_id,
                name=definition["name"],
                defaults={
                    "description": definition["description"],
                    "interview_type": definition["interview_type"],
                    "created_by": self.users["tenant_admin"].id,
                    "is_active": True,
                    "metadata": {
                        **definition["metadata"],
                        "reusable_template": True,
                        "recommendation_mapping": {
                            "strong_recommend": 90,
                            "recommend": recommendation_logic["pass_threshold"],
                            "neutral": round((recommendation_logic["pass_threshold"] + recommendation_logic["reject_threshold"]) / 2),
                            "concern": recommendation_logic["reject_threshold"],
                            "reject": 0,
                        },
                        "seed_module_id": MODULE_ID,
                    },
                },
            )
            obj.description = definition["description"]
            obj.interview_type = definition["interview_type"]
            obj.is_active = True
            obj.metadata = {
                **(obj.metadata or {}),
                **definition["metadata"],
                "reusable_template": True,
                "recommendation_mapping": {
                    "strong_recommend": 90,
                    "recommend": recommendation_logic["pass_threshold"],
                    "neutral": round((recommendation_logic["pass_threshold"] + recommendation_logic["reject_threshold"]) / 2),
                    "concern": recommendation_logic["reject_threshold"],
                    "reject": 0,
                },
                "seed_module_id": MODULE_ID,
            }
            obj.save(update_fields=["description", "interview_type", "is_active", "metadata", "updated_at"])
            obj.attributes.all().delete()
            for index, (attribute_name, weight, rating_type, required) in enumerate(definition["attributes"], start=1):
                obj.attributes.create(
                    tenant_id=self.tenant_id,
                    attribute_name=attribute_name,
                    weight=as_decimal(weight),
                    rating_type=rating_type,
                    required=required,
                    order_index=index,
                )
            scorecards[definition["name"]] = obj
        return scorecards

    def seed_ai_templates(self):
        templates = {}
        for definition in self.ai_template_definitions():
            template_type = self.types[definition["interview_type"]]
            obj, _ = InterviewTemplate.objects.get_or_create(
                tenant_id=self.tenant_id,
                name=definition["name"],
                defaults={
                    "description": definition["description"],
                    "interview_type": definition["interview_type"],
                    "type": template_type,
                    "duration_minutes": definition["setup"]["duration_minutes"],
                    "instructions": definition["candidate_experience"]["instructions"],
                    "scoring_type": "criteria",
                    "questions": definition["questions_payload"],
                    "scoring_criteria": {"dimensions": [item["name"] for item in definition["evaluation"]["dimensions"]]},
                    "created_by": self.users["tenant_admin"].id,
                    "is_active": True,
                    "metadata": definition["metadata"],
                },
            )
            obj.description = definition["description"]
            obj.interview_type = definition["interview_type"]
            obj.type = template_type
            obj.duration_minutes = definition["setup"]["duration_minutes"]
            obj.instructions = definition["candidate_experience"]["instructions"]
            obj.scoring_type = "criteria"
            obj.questions = definition["questions_payload"]
            obj.scoring_criteria = {"dimensions": [item["name"] for item in definition["evaluation"]["dimensions"]]}
            obj.is_active = True
            obj.metadata = definition["metadata"]
            obj.save()
            templates[definition["name"]] = obj
        return templates

    def ai_template_definitions(self):
        return [
            self.build_ai_template(
                name="Sales AI Screening",
                interview_type="ai_screening",
                response_mode="video",
                duration_minutes=20,
                prep_time_seconds=45,
                retries=1,
                description="Qualification screen for SaaS account executive hiring.",
                generation_brief={
                    "role": "Account Executive",
                    "skills": ["sales discovery", "pipeline management", "communication"],
                    "seniority": "Mid-market",
                    "job_description": "Own outbound and inbound pipeline, run demos, and close SMB to mid-market SaaS opportunities.",
                },
                candidate_experience={
                    "instructions": "Answer each question with crisp customer-facing examples and measurable outcomes.",
                    "intro_message": "Welcome to the sales AI screening. We want to understand how you qualify opportunities and drive momentum.",
                    "practice_mode": True,
                    "camera_required": True,
                    "mic_required": True,
                    "retry_behavior": "One retry allowed only if the first attempt is interrupted.",
                },
                questions=[
                    {
                        "title": "Discovery discipline",
                        "question": "Walk through how you qualify a new inbound lead before booking a demo.",
                        "objective": "Assess sales qualification structure and discovery discipline.",
                        "response_mode": "video",
                        "follow_up_shell": "Ask for the exact discovery questions used to uncover pain, budget, and timeline.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Surface consistency in qualification process.",
                        "follow_up_trigger_note": "Use if answer stays high-level.",
                        "expected_answer_guidance": "A strong answer references MEDDICC/BANT-style qualification, discovery sequencing, and qualification exit criteria.",
                        "poor_answer_guidance": "Weak answers skip qualification depth and move directly to pitching.",
                        "expected_keywords": ["qualification", "pain", "budget", "timeline", "decision maker"],
                        "evaluation_dimensions": ["communication", "behavioral_fit"],
                        "skill_mapping": ["sales discovery", "lead qualification"],
                        "knockout_intent_shell": "Fail if candidate cannot articulate a repeatable qualification method.",
                        "internal_note": "Core knockout for enterprise sales basics.",
                        "prep_guidance": "Use one recent deal example.",
                        "duration_guidance": "90 seconds",
                        "min_length_guidance": "",
                        "max_length_guidance": "",
                    },
                    {
                        "title": "Objection handling",
                        "question": "Tell us about a stalled opportunity you revived and what changed.",
                        "objective": "Evaluate objection handling and pipeline recovery.",
                        "response_mode": "video",
                        "follow_up_shell": "Ask what signal told the candidate the deal was at risk and what action they took first.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Measure ownership and deal strategy.",
                        "follow_up_trigger_note": "Use if the candidate speaks only about final outcome.",
                        "expected_answer_guidance": "Strong answer includes diagnosis, stakeholder management, and a quantified outcome.",
                        "poor_answer_guidance": "Weak answers blame the prospect without showing strategy.",
                        "expected_keywords": ["stakeholder", "risk", "re-engage", "next step", "close plan"],
                        "evaluation_dimensions": ["communication", "confidence"],
                        "skill_mapping": ["objection handling", "pipeline management"],
                        "knockout_intent_shell": "",
                        "internal_note": "Looks for seller judgment under pressure.",
                        "prep_guidance": "Focus on one concrete deal.",
                        "duration_guidance": "120 seconds",
                        "min_length_guidance": "",
                        "max_length_guidance": "",
                    },
                ],
                evaluation_dimensions=[
                    self.eval_dimension("communication", "Communication", 25, "blended", "Clear, concise, commercially credible answers.", "Vague or overly generic delivery."),
                    self.eval_dimension("confidence", "Confidence", 15, "ai", "Strong presence and ownership without overselling.", "Hesitant or defensive tone."),
                    self.eval_dimension("behavioral_fit", "Behavioral Fit", 20, "blended", "Evidence of resilience, curiosity, and accountability.", "No reflection or ownership."),
                    self.eval_dimension("domain_knowledge", "Domain Knowledge", 40, "ai", "Strong qualification, pipeline, and objection-handling understanding.", "No repeatable sales process."),
                ],
                recommendation_logic="sales_screening_recommendation_model",
                scorecard_name="AI Screening Scorecard",
                skill_mapping=["sales discovery", "lead qualification", "objection handling", "pipeline management"],
                outcome_stage_map={
                    "Strong Recommend": "Hiring Manager Interview",
                    "Recommend": "Hiring Manager Interview",
                    "Neutral": "Recruiter Review",
                    "Concern": "Manual Review Queue",
                    "Reject": "Reject Candidate",
                },
                preview={"suggested_outcome": "Recommend", "suggested_route": "Move to Hiring Manager Interview", "auto_notify_recruiter": True},
            ),
            self.build_ai_template(
                name="Customer Support Behavioral AI Screen",
                interview_type="ai_behavioral",
                response_mode="audio",
                duration_minutes=18,
                prep_time_seconds=30,
                retries=1,
                description="Behavioral AI screen for high-volume customer support hiring.",
                generation_brief={
                    "role": "Customer Support Specialist",
                    "skills": ["empathy", "de-escalation", "written communication"],
                    "seniority": "Associate",
                    "job_description": "Handle omnichannel customer support, triage issues, and maintain CSAT benchmarks.",
                },
                candidate_experience={
                    "instructions": "Use customer situations you handled personally and focus on your actions and reasoning.",
                    "intro_message": "This support behavioral screen focuses on empathy, ownership, and communication under pressure.",
                    "practice_mode": True,
                    "camera_required": False,
                    "mic_required": True,
                    "retry_behavior": "Single retry on interrupted recordings only.",
                },
                questions=[
                    {
                        "title": "Handling escalation",
                        "question": "Describe a situation where an angry customer contacted you and how you de-escalated it.",
                        "objective": "Measure empathy, listening, and de-escalation approach.",
                        "response_mode": "audio",
                        "follow_up_shell": "Ask what exact language the candidate used to acknowledge the customer emotion.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Test real de-escalation technique.",
                        "follow_up_trigger_note": "Use when the answer lacks empathy markers.",
                        "expected_answer_guidance": "A strong answer includes active listening, ownership, expectation setting, and follow-through.",
                        "poor_answer_guidance": "Weak answers focus on policy only and ignore emotional handling.",
                        "expected_keywords": ["empathy", "acknowledge", "ownership", "resolution", "follow-up"],
                        "evaluation_dimensions": ["communication", "collaboration", "behavioral_fit"],
                        "skill_mapping": ["de-escalation", "customer empathy"],
                        "knockout_intent_shell": "",
                        "internal_note": "Critical for frontline support fit.",
                        "prep_guidance": "Use one customer conversation you remember well.",
                        "duration_guidance": "90 seconds",
                        "min_length_guidance": "",
                        "max_length_guidance": "",
                    },
                    {
                        "title": "Cross-team collaboration",
                        "question": "Share an example where you partnered with another team to resolve a customer issue.",
                        "objective": "Evaluate collaboration and ownership across teams.",
                        "response_mode": "audio",
                        "follow_up_shell": "Ask how the candidate kept the customer informed while waiting on another team.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Test expectation management.",
                        "follow_up_trigger_note": "Use when the answer centers only on the internal team.",
                        "expected_answer_guidance": "Strong answer shows stakeholder coordination and customer communication discipline.",
                        "poor_answer_guidance": "Weak answers lose track of accountability during handoff.",
                        "expected_keywords": ["handoff", "stakeholder", "expectation", "ownership", "update cadence"],
                        "evaluation_dimensions": ["collaboration", "communication"],
                        "skill_mapping": ["cross-functional collaboration", "customer updates"],
                        "knockout_intent_shell": "",
                        "internal_note": "High signal for support maturity.",
                        "prep_guidance": "Explain who you worked with and why.",
                        "duration_guidance": "75 seconds",
                        "min_length_guidance": "",
                        "max_length_guidance": "",
                    },
                ],
                evaluation_dimensions=[
                    self.eval_dimension("communication", "Communication", 30, "blended", "Clear, calm, customer-safe verbal communication.", "Rambling or reactive communication."),
                    self.eval_dimension("collaboration", "Collaboration", 25, "blended", "Shows mature cross-functional coordination.", "No ownership across handoffs."),
                    self.eval_dimension("behavioral_fit", "Behavioral Fit", 25, "ai", "Demonstrates empathy, patience, and resilience.", "Defensive or rigid approach."),
                    self.eval_dimension("confidence", "Confidence", 20, "ai", "Steady under customer pressure.", "Uncertain or passive language."),
                ],
                recommendation_logic="support_behavioral_model",
                scorecard_name="Behavioral Scorecard",
                skill_mapping=["de-escalation", "customer empathy", "cross-functional collaboration"],
                outcome_stage_map={
                    "Strong Recommend": "HR Interview",
                    "Recommend": "HR Interview",
                    "Neutral": "Manual Review Queue",
                    "Concern": "Manual Review Queue",
                    "Reject": "Reject Candidate",
                },
                preview={"suggested_outcome": "Neutral", "suggested_route": "Manual review queue", "auto_notify_recruiter": True},
            ),
            self.build_ai_template(
                name="Junior Developer AI Technical Screen",
                interview_type="ai_technical",
                response_mode="video",
                duration_minutes=25,
                prep_time_seconds=60,
                retries=1,
                description="Foundational technical screen for junior backend engineer hiring.",
                generation_brief={
                    "role": "Junior Backend Developer",
                    "skills": ["python", "apis", "debugging", "sql"],
                    "seniority": "0-2 years",
                    "job_description": "Build backend services, debug issues, and work on Python APIs with PostgreSQL.",
                },
                candidate_experience={
                    "instructions": "Think aloud, explain tradeoffs, and use simple examples to show technical understanding.",
                    "intro_message": "This AI technical screen focuses on problem solving, APIs, debugging, and backend fundamentals.",
                    "practice_mode": True,
                    "camera_required": True,
                    "mic_required": True,
                    "retry_behavior": "No retries after submission unless the session disconnects.",
                },
                questions=[
                    {
                        "title": "API design basics",
                        "question": "Explain how you would design an API endpoint to create and fetch support tickets.",
                        "objective": "Measure API modeling and backend fundamentals.",
                        "response_mode": "video",
                        "follow_up_shell": "Ask about status codes, validation, and idempotency.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Probe deeper on HTTP fundamentals.",
                        "follow_up_trigger_note": "Use if answer skips edge cases.",
                        "expected_answer_guidance": "Strong answer covers request/response shapes, validation, error handling, and REST semantics.",
                        "poor_answer_guidance": "Weak answers only describe database storage without API contract details.",
                        "expected_keywords": ["endpoint", "validation", "status code", "idempotency", "schema"],
                        "evaluation_dimensions": ["problem_solving", "domain_knowledge", "technical_depth"],
                        "skill_mapping": ["apis", "python", "backend fundamentals"],
                        "knockout_intent_shell": "",
                        "internal_note": "High-signal junior backend question.",
                        "prep_guidance": "Explain the endpoint as if discussing with another engineer.",
                        "duration_guidance": "120 seconds",
                        "min_length_guidance": "",
                        "max_length_guidance": "",
                    },
                    {
                        "title": "Debugging mindset",
                        "question": "Tell us about a bug you investigated and how you narrowed down the root cause.",
                        "objective": "Assess debugging structure and analytical thinking.",
                        "response_mode": "video",
                        "follow_up_shell": "Ask which signals or logs helped most and what they ruled out.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Reveal debugging process quality.",
                        "follow_up_trigger_note": "Use when answer jumps straight to the fix.",
                        "expected_answer_guidance": "Strong answer includes reproduction, isolation, instrumentation, and learning.",
                        "poor_answer_guidance": "Weak answers show random trial and error with no method.",
                        "expected_keywords": ["reproduce", "logs", "hypothesis", "root cause", "verification"],
                        "evaluation_dimensions": ["problem_solving", "technical_depth"],
                        "skill_mapping": ["debugging", "logs", "backend fundamentals"],
                        "knockout_intent_shell": "",
                        "internal_note": "Useful for junior signal beyond theory.",
                        "prep_guidance": "Choose a bug you personally solved.",
                        "duration_guidance": "105 seconds",
                        "min_length_guidance": "",
                        "max_length_guidance": "",
                    },
                ],
                evaluation_dimensions=[
                    self.eval_dimension("problem_solving", "Problem Solving", 35, "blended", "Structured reasoning with clear tradeoffs.", "No stepwise thinking."),
                    self.eval_dimension("domain_knowledge", "Domain Knowledge", 25, "ai", "Solid API and backend fundamentals.", "Weak understanding of HTTP or data flow."),
                    self.eval_dimension("technical_depth", "Technical Depth", 25, "blended", "Understands debugging and implementation detail.", "Shallow technical explanations."),
                    self.eval_dimension("communication", "Communication", 15, "human", "Explains clearly and logically.", "Confusing or fragmented responses."),
                ],
                recommendation_logic="junior_backend_ai_model",
                scorecard_name="Technical Scorecard",
                skill_mapping=["python", "apis", "debugging", "backend fundamentals"],
                outcome_stage_map={
                    "Strong Recommend": "Coding Interview",
                    "Recommend": "Technical Interview",
                    "Neutral": "Manual Review Queue",
                    "Concern": "Manual Review Queue",
                    "Reject": "Reject Candidate",
                },
                preview={"suggested_outcome": "Recommend", "suggested_route": "Move to Technical Interview", "auto_notify_recruiter": True},
            ),
            self.build_ai_template(
                name="Finance Analyst Async Text Screen",
                interview_type="async_text",
                response_mode="text",
                duration_minutes=25,
                prep_time_seconds=0,
                retries=0,
                description="Async written screen for finance analysts and reporting roles.",
                generation_brief={
                    "role": "Finance Analyst",
                    "skills": ["financial modeling", "excel", "variance analysis"],
                    "seniority": "Associate",
                    "job_description": "Build forecasts, analyze variance, and communicate financial insights to business stakeholders.",
                },
                candidate_experience={
                    "instructions": "Answer clearly and concisely. Use structured bullets or short paragraphs where appropriate.",
                    "intro_message": "This async text screen evaluates written communication and finance analysis thinking.",
                    "practice_mode": False,
                    "camera_required": False,
                    "mic_required": False,
                    "retry_behavior": "No retries after final submission.",
                },
                questions=[
                    {
                        "title": "Variance analysis",
                        "question": "How would you explain a 12% month-over-month expense increase to a business leader?",
                        "objective": "Assess written financial analysis and executive communication.",
                        "response_mode": "text",
                        "follow_up_shell": "Ask how the candidate would separate temporary drivers from structural cost changes.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Probe analytical depth.",
                        "follow_up_trigger_note": "Use if the answer is purely narrative.",
                        "expected_answer_guidance": "Strong answer breaks down drivers, frames business impact, and recommends action.",
                        "poor_answer_guidance": "Weak answers restate the variance without interpretation.",
                        "expected_keywords": ["driver", "variance", "trend", "forecast", "action"],
                        "evaluation_dimensions": ["communication", "domain_knowledge"],
                        "skill_mapping": ["variance analysis", "stakeholder communication"],
                        "knockout_intent_shell": "",
                        "internal_note": "Written communication is core here.",
                        "prep_guidance": "",
                        "duration_guidance": "",
                        "min_length_guidance": "120 words minimum",
                        "max_length_guidance": "250 words maximum",
                    },
                    {
                        "title": "Forecast discipline",
                        "question": "Describe the inputs you would validate before finalizing a quarterly forecast.",
                        "objective": "Measure financial planning structure.",
                        "response_mode": "text",
                        "follow_up_shell": "Ask which assumptions are most likely to change late in the cycle.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Test forecast judgment.",
                        "follow_up_trigger_note": "Use if the candidate lists inputs without prioritization.",
                        "expected_answer_guidance": "Strong answer covers assumptions, source validation, sensitivity, and stakeholder alignment.",
                        "poor_answer_guidance": "Weak answers only mention spreadsheet mechanics.",
                        "expected_keywords": ["assumptions", "sensitivity", "actuals", "pipeline", "headcount"],
                        "evaluation_dimensions": ["domain_knowledge", "problem_solving"],
                        "skill_mapping": ["forecasting", "financial modeling"],
                        "knockout_intent_shell": "",
                        "internal_note": "Should reflect analyst fundamentals.",
                        "prep_guidance": "",
                        "duration_guidance": "",
                        "min_length_guidance": "100 words minimum",
                        "max_length_guidance": "220 words maximum",
                    },
                ],
                evaluation_dimensions=[
                    self.eval_dimension("communication", "Communication", 35, "blended", "Crisp written explanation with business clarity.", "Poor written structure or unclear reasoning."),
                    self.eval_dimension("domain_knowledge", "Domain Knowledge", 40, "ai", "Shows finance fundamentals and analysis depth.", "Weak finance terminology or logic."),
                    self.eval_dimension("problem_solving", "Problem Solving", 25, "blended", "Prioritizes data and implications well.", "No analytical prioritization."),
                ],
                recommendation_logic="finance_async_text_model",
                scorecard_name="Behavioral Scorecard",
                skill_mapping=["financial modeling", "variance analysis", "stakeholder communication"],
                outcome_stage_map={
                    "Strong Recommend": "Hiring Manager Interview",
                    "Recommend": "Hiring Manager Interview",
                    "Neutral": "Manual Review Queue",
                    "Concern": "Manual Review Queue",
                    "Reject": "Reject Candidate",
                },
                preview={"suggested_outcome": "Recommend", "suggested_route": "Move to Hiring Manager Interview", "auto_notify_recruiter": True},
            ),
            self.build_ai_template(
                name="Leadership Behavioral One-Way Video",
                interview_type="one_way_video",
                response_mode="video",
                duration_minutes=30,
                prep_time_seconds=90,
                retries=1,
                description="One-way video leadership screen for director-level hiring.",
                generation_brief={
                    "role": "Director of Operations",
                    "skills": ["leadership", "change management", "stakeholder management"],
                    "seniority": "Director",
                    "job_description": "Lead multi-team operations, drive change programs, and communicate with senior stakeholders.",
                },
                candidate_experience={
                    "instructions": "Answer with measurable leadership examples. Highlight your role, tradeoffs, and outcome.",
                    "intro_message": "This one-way video round evaluates leadership judgment, executive presence, and stakeholder management.",
                    "practice_mode": True,
                    "camera_required": True,
                    "mic_required": True,
                    "retry_behavior": "One retake is allowed before final submission.",
                },
                questions=[
                    {
                        "title": "Leading change",
                        "question": "Describe a difficult operational change you led and how you secured stakeholder buy-in.",
                        "objective": "Assess change leadership and influence.",
                        "response_mode": "video",
                        "follow_up_shell": "Ask which stakeholder resisted most and how the candidate addressed the resistance.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Probe influence strategy.",
                        "follow_up_trigger_note": "Use if resistance is glossed over.",
                        "expected_answer_guidance": "Strong answer covers context, stakeholder landscape, communication plan, and measurable change outcome.",
                        "poor_answer_guidance": "Weak answers describe the project but not leadership behavior.",
                        "expected_keywords": ["buy-in", "resistance", "communication plan", "change", "stakeholder"],
                        "evaluation_dimensions": ["leadership", "persuasion", "confidence"],
                        "skill_mapping": ["change management", "stakeholder management"],
                        "knockout_intent_shell": "",
                        "internal_note": "High-signal leadership question.",
                        "prep_guidance": "Use one strategic initiative you personally led.",
                        "duration_guidance": "150 seconds",
                        "min_length_guidance": "",
                        "max_length_guidance": "",
                    },
                    {
                        "title": "Decision under ambiguity",
                        "question": "Tell us about a time you had to make a decision with incomplete data and how you managed the risk.",
                        "objective": "Evaluate decision quality and risk framing.",
                        "response_mode": "video",
                        "follow_up_shell": "Ask what information the candidate still wanted and how they compensated for not having it.",
                        "follow_up_enabled": True,
                        "follow_up_objective": "Probe leadership judgment.",
                        "follow_up_trigger_note": "Use if the answer sounds certain from the start.",
                        "expected_answer_guidance": "Strong answer shows frameworks, contingencies, and clear accountability.",
                        "poor_answer_guidance": "Weak answers avoid the risk tradeoff entirely.",
                        "expected_keywords": ["ambiguity", "risk", "decision", "tradeoff", "contingency"],
                        "evaluation_dimensions": ["leadership", "problem_solving", "confidence"],
                        "skill_mapping": ["leadership", "risk management"],
                        "knockout_intent_shell": "",
                        "internal_note": "Checks executive decision maturity.",
                        "prep_guidance": "Focus on one meaningful decision.",
                        "duration_guidance": "150 seconds",
                        "min_length_guidance": "",
                        "max_length_guidance": "",
                    },
                ],
                evaluation_dimensions=[
                    self.eval_dimension("leadership", "Leadership", 35, "blended", "Demonstrates strategic leadership and accountability.", "No clear ownership or leadership action."),
                    self.eval_dimension("persuasion", "Persuasion", 20, "ai", "Shows stakeholder influence and narrative control.", "Weak stakeholder management."),
                    self.eval_dimension("confidence", "Confidence", 20, "ai", "Strong executive presence and composure.", "Low presence or uncertain framing."),
                    self.eval_dimension("problem_solving", "Problem Solving", 25, "human", "Navigates ambiguity with structured thinking.", "No risk logic or tradeoff awareness."),
                ],
                recommendation_logic="leadership_one_way_video_model",
                scorecard_name="Final Round Scorecard",
                skill_mapping=["leadership", "change management", "stakeholder management", "risk management"],
                outcome_stage_map={
                    "Strong Recommend": "Leadership Panel",
                    "Recommend": "Leadership Panel",
                    "Neutral": "Manual Review Queue",
                    "Concern": "Manual Review Queue",
                    "Reject": "Reject Candidate",
                },
                preview={"suggested_outcome": "Strong Recommend", "suggested_route": "Move to Leadership Panel", "auto_notify_recruiter": True},
            ),
        ]

    def build_ai_template(
        self,
        *,
        name,
        interview_type,
        response_mode,
        duration_minutes,
        prep_time_seconds,
        retries,
        description,
        generation_brief,
        candidate_experience,
        questions,
        evaluation_dimensions,
        recommendation_logic,
        scorecard_name,
        skill_mapping,
        outcome_stage_map,
        preview,
    ):
        outcomes = [
            {
                "id": str(seed_uuid(f"{name}:outcome:{label}")),
                "label": label,
                "min_score": minimum,
                "max_score": maximum,
                "route_action": route_action,
                "next_stage_mapping": next_stage,
            }
            for label, minimum, maximum, route_action, next_stage in [
                ("Strong Recommend", 90, 100, "move_to_next_stage", outcome_stage_map["Strong Recommend"]),
                ("Recommend", 75, 89, "move_to_next_stage", outcome_stage_map["Recommend"]),
                ("Neutral", 50, 74, "manual_review_queue", outcome_stage_map["Neutral"]),
                ("Concern", 30, 49, "manual_review_queue", outcome_stage_map["Concern"]),
                ("Reject", 0, 29, "reject_candidate", outcome_stage_map["Reject"]),
            ]
        ]
        serialized_questions = []
        flow_questions = []
        for index, question in enumerate(questions):
            question_id = str(seed_uuid(f"{name}:question:{index + 1}"))
            serialized_questions.append(
                {
                    "id": question_id,
                    "title": question["title"],
                    "text": question["question"],
                    "objective": question["objective"],
                    "type": question["response_mode"],
                    "follow_up_shell": question["follow_up_shell"],
                    "follow_up_enabled": question["follow_up_enabled"],
                    "follow_up_objective": question["follow_up_objective"],
                    "follow_up_trigger_note": question["follow_up_trigger_note"],
                    "expected_answer": question["expected_answer_guidance"],
                    "poor_answer_guidance": question["poor_answer_guidance"],
                    "expected_keywords": question["expected_keywords"],
                    "evaluation_dimensions": question["evaluation_dimensions"],
                    "custom_dimension": "",
                    "skills": question["skill_mapping"],
                    "knockout_intent_shell": question["knockout_intent_shell"],
                    "internal_note": question["internal_note"],
                    "prep_guidance": question["prep_guidance"],
                    "duration_guidance": question["duration_guidance"],
                    "min_length_guidance": question["min_length_guidance"],
                    "max_length_guidance": question["max_length_guidance"],
                    "order_index": index,
                    "duration": max(int((duration_minutes * 60) / max(len(questions), 1)), 60),
                    "options": [],
                }
            )
            flow_questions.append(
                {
                    "id": question_id,
                    "title": question["title"],
                    "question": question["question"],
                    "objective": question["objective"],
                    "follow_up_shell": question["follow_up_shell"],
                    "follow_up_enabled": question["follow_up_enabled"],
                    "follow_up_objective": question["follow_up_objective"],
                    "follow_up_trigger_note": question["follow_up_trigger_note"],
                    "expected_answer_guidance": question["expected_answer_guidance"],
                    "poor_answer_guidance": question["poor_answer_guidance"],
                    "expected_keywords": question["expected_keywords"],
                    "evaluation_dimensions": question["evaluation_dimensions"],
                    "custom_dimension": "",
                    "skill_mapping": question["skill_mapping"],
                    "knockout_intent_shell": question["knockout_intent_shell"],
                    "internal_note": question["internal_note"],
                    "prep_guidance": question["prep_guidance"],
                    "duration_guidance": question["duration_guidance"],
                    "min_length_guidance": question["min_length_guidance"],
                    "max_length_guidance": question["max_length_guidance"],
                    "response_mode": question["response_mode"],
                }
            )

        metadata = {
            "ai_interview": {
                "entity_type": "reusable_ai_interview_template",
                "creation_method": "manual",
                "setup": {
                    "name": name,
                    "interview_type": interview_type,
                    "duration_minutes": duration_minutes,
                    "response_mode": response_mode,
                    "prep_time_seconds": prep_time_seconds,
                    "retries": retries,
                },
                "question_flow": {
                    "intro_message": candidate_experience["intro_message"],
                    "questions": flow_questions,
                },
                "candidate_experience": candidate_experience,
                "evaluation": {
                    "scoring_enabled": True,
                    "manual_override": True,
                    "scoring_blend_mode": "blended",
                    "ai_scoring_weight": 60,
                    "human_scoring_weight": 40,
                    "skill_mapping": skill_mapping,
                    "recommendation_logic": recommendation_logic,
                    "scorecard_template_id": str(self.scorecards[scorecard_name].id),
                    "dimensions": evaluation_dimensions,
                    "score_sync": {
                        "save_ai_score_to_scorecard": True,
                        "save_dimension_scores_to_scorecard": True,
                        "save_total_score_to_scorecard": True,
                        "save_ai_recommendation_to_scorecard": True,
                        "sync_target": "scorecard_engine",
                    },
                    "recommendation_thresholds": {
                        "strong_recommend": 90,
                        "recommend": 75,
                        "neutral": 60,
                        "concern": 45,
                        "reject": 0,
                    },
                    "final_outcome_suggestion": {
                        "suggested_score_shell": "Weighted score blended from AI and human evaluation.",
                        "suggested_recommendation_shell": "Recommendation derived from weighted thresholds and confidence logic.",
                        "suggested_next_action_shell": "Route candidate to the mapped next stage or manual review queue.",
                    },
                },
                "outcome_routing": {
                    "outcomes": outcomes,
                    "automation": {
                        "auto_decision_enabled": True,
                        "manual_override_allowed": True,
                        "recruiter_review_required": True,
                        "confidence_threshold": 60,
                        "fallback_to_manual_review": True,
                    },
                    "preview": preview,
                },
                "generation_brief": generation_brief,
                "integrations": {
                    "question_engine": True,
                    "scorecard_engine": True,
                    "flow_engine": True,
                    "decision_engine": True,
                },
                "usage": {
                    "linked_jobs": [],
                    "linked_flows": [],
                    "linked_stages": [],
                },
            }
        }
        return {
            "name": name,
            "description": description,
            "interview_type": interview_type,
            "setup": {
                "name": name,
                "interview_type": interview_type,
                "duration_minutes": duration_minutes,
                "response_mode": response_mode,
                "prep_time_seconds": prep_time_seconds,
                "retries": retries,
            },
            "candidate_experience": candidate_experience,
            "evaluation": {
                "dimensions": evaluation_dimensions,
            },
            "questions_payload": serialized_questions,
            "metadata": metadata,
        }

    def eval_dimension(self, key, name, weight, scoring_owner, strong_guidance, weak_guidance):
        return {
            "id": str(seed_uuid(f"eval-dimension:{name}")),
            "key": key,
            "name": name,
            "description": f"{name} evaluation dimension for ICC seeded AI interviews.",
            "scorecard_attribute_name": name,
            "weight": weight,
            "enabled": True,
            "scoring_owner": scoring_owner,
            "rubric": {
                "excellent": strong_guidance,
                "acceptable": f"Baseline evidence of {name.lower()} with some structure.",
                "weak": weak_guidance,
                "red_flags": f"Major gaps in {name.lower()} or contradictory signals.",
                "positive_signals": f"Consistent evidence of strong {name.lower()} and clear examples.",
            },
        }

    def seed_unified_templates(self):
        templates = {}
        definitions = [
            {
                "name": "Structured Technical Round",
                "interview_type": "technical_interview",
                "description": "Reusable live technical round with interviewer guidance and scorecard mapping.",
                "category": "Technical",
                "duration_minutes": 60,
                "instructions": "Focus on problem decomposition, code quality, and tradeoffs.",
                "scorecard_name": "Technical Scorecard",
                "configuration": {
                    "ai_config": "",
                    "interviewer_config": "Use one coding problem and one system tradeoff discussion.",
                    "assessment_config": "",
                    "screening_config": "",
                    "advanced_config": "",
                },
                "automation": {"trigger_mode": "manual_trigger", "routing": "panel_review", "scheduling_enabled": True},
            },
            {
                "name": "HR Final Conversation",
                "interview_type": "hr_interview",
                "description": "HR final round focused on compensation, policy readiness, and close plan.",
                "category": "Human",
                "duration_minutes": 45,
                "instructions": "Validate compensation alignment, notice period, and offer-readiness.",
                "scorecard_name": "HR Scorecard",
                "configuration": {
                    "ai_config": "",
                    "interviewer_config": "Check policy fit, compensation expectations, and joining readiness.",
                    "assessment_config": "",
                    "screening_config": "",
                    "advanced_config": "",
                },
                "automation": {"trigger_mode": "manual_trigger", "routing": "offer_readiness", "scheduling_enabled": True},
            },
            {
                "name": "Sales Role Play Simulation",
                "interview_type": "role_play",
                "description": "Sales objection handling role play for customer-facing hires.",
                "category": "Advanced",
                "duration_minutes": 40,
                "instructions": "Run a prospect objection scenario and assess discovery plus control.",
                "scorecard_name": "AI Screening Scorecard",
                "configuration": {
                    "ai_config": "",
                    "interviewer_config": "",
                    "assessment_config": "",
                    "screening_config": "",
                    "advanced_config": "Run a mock objection-handling role play and capture deal control signals.",
                },
                "automation": {"trigger_mode": "manual_trigger", "routing": "hiring_manager_review", "scheduling_enabled": True},
            },
            {
                "name": "Operations Case Study",
                "interview_type": "case_study",
                "description": "Case study template for operations and finance roles.",
                "category": "Assessment",
                "duration_minutes": 50,
                "instructions": "Walk through analysis structure, assumptions, and recommendation quality.",
                "scorecard_name": "Behavioral Scorecard",
                "configuration": {
                    "ai_config": "",
                    "interviewer_config": "",
                    "assessment_config": "Share a business case and evaluate structuring, prioritization, and recommendation quality.",
                    "screening_config": "",
                    "advanced_config": "",
                },
                "automation": {"trigger_mode": "auto_trigger", "routing": "manual_review", "scheduling_enabled": False},
            },
        ]
        for definition in definitions:
            template_type = self.types[definition["interview_type"]]
            metadata = {
                "unified_template": {
                    "category": definition["category"],
                    "setup": {"reusable_template": True},
                    "configuration": definition["configuration"],
                    "scorecard": {"scorecard_template_id": str(self.scorecards[definition["scorecard_name"]].id)},
                    "automation": definition["automation"],
                    "integrations": {
                        "flow_engine": True,
                        "scorecard_engine": True,
                        "ai_engine": definition["category"] == "AI",
                        "scheduling_engine": definition["automation"]["scheduling_enabled"],
                    },
                },
                "seed_module_id": MODULE_ID,
            }
            obj, _ = InterviewTemplate.objects.get_or_create(
                tenant_id=self.tenant_id,
                name=definition["name"],
                defaults={
                    "description": definition["description"],
                    "interview_type": definition["interview_type"],
                    "type": template_type,
                    "duration_minutes": definition["duration_minutes"],
                    "instructions": definition["instructions"],
                    "scoring_type": "criteria",
                    "questions": [],
                    "created_by": self.users["tenant_admin"].id,
                    "is_active": True,
                    "metadata": metadata,
                },
            )
            obj.description = definition["description"]
            obj.interview_type = definition["interview_type"]
            obj.type = template_type
            obj.duration_minutes = definition["duration_minutes"]
            obj.instructions = definition["instructions"]
            obj.scoring_type = "criteria"
            obj.is_active = True
            obj.metadata = metadata
            obj.save()
            templates[definition["name"]] = obj
        return templates

    def seed_question_bank(self):
        questions = {}
        definitions = [
            {
                "slug": "sales-qualification",
                "title": "How do you qualify whether a prospect is worth a demo?",
                "description": "Screening prompt for sales discovery quality.",
                "question_type": "text",
                "difficulty": "medium",
                "tags": ["sales", "screening"],
                "skills": ["sales discovery", "qualification"],
                "expected_answer": "Should mention pain, decision-maker, urgency, and next-step logic.",
            },
            {
                "slug": "support-escalation",
                "title": "How would you calm a customer whose issue has remained unresolved for 48 hours?",
                "description": "Behavioral support question.",
                "question_type": "text",
                "difficulty": "medium",
                "tags": ["support", "behavioral"],
                "skills": ["de-escalation", "customer empathy"],
                "expected_answer": "Should show empathy, ownership, expectation setting, and follow-up.",
            },
            {
                "slug": "api-idempotency",
                "title": "Explain idempotency in REST APIs with a practical example.",
                "description": "Backend fundamentals question.",
                "question_type": "text",
                "difficulty": "medium",
                "tags": ["backend", "apis"],
                "skills": ["apis", "backend fundamentals"],
                "expected_answer": "Should explain repeated safe operations and why duplicate side effects matter.",
            },
            {
                "slug": "rate-limiter",
                "title": "Design a simple rate limiter for an API gateway.",
                "description": "System design shell question.",
                "question_type": "coding",
                "difficulty": "hard",
                "tags": ["system design", "backend"],
                "skills": ["system design", "redis"],
                "expected_answer": "Should mention counters, windows, storage choice, and tradeoffs.",
            },
            {
                "slug": "leadership-change",
                "title": "Describe a difficult change initiative you led and how you brought others along.",
                "description": "Leadership behavioral prompt.",
                "question_type": "video",
                "difficulty": "hard",
                "tags": ["leadership", "behavioral"],
                "skills": ["change management", "leadership"],
                "expected_answer": "Should include resistance, communication strategy, and outcome.",
            },
            {
                "slug": "finance-variance",
                "title": "What are the first checks you make when a forecast misses by more than 10%?",
                "description": "Finance analytical prompt.",
                "question_type": "text",
                "difficulty": "medium",
                "tags": ["finance", "analysis"],
                "skills": ["forecasting", "variance analysis"],
                "expected_answer": "Should mention assumptions, actuals, drivers, and sensitivity.",
            },
        ]
        for definition in definitions:
            obj, _ = InterviewQuestionBank.objects.get_or_create(
                id=seed_uuid(f"question-bank:{definition['slug']}"),
                defaults={
                    "tenant_id": self.tenant_id,
                    "scope": "tenant",
                    "question_title": definition["title"],
                    "description": definition["description"],
                    "question_type": definition["question_type"],
                    "difficulty": definition["difficulty"],
                    "tags": definition["tags"],
                    "skills": definition["skills"],
                    "expected_answer": definition["expected_answer"],
                    "scoring_weight": as_decimal(1),
                    "is_active": True,
                    "created_by": self.users["tenant_admin"].id,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
            obj.tenant_id = self.tenant_id
            obj.scope = "tenant"
            obj.question_title = definition["title"]
            obj.description = definition["description"]
            obj.question_type = definition["question_type"]
            obj.difficulty = definition["difficulty"]
            obj.tags = definition["tags"]
            obj.skills = definition["skills"]
            obj.expected_answer = definition["expected_answer"]
            obj.scoring_weight = as_decimal(1)
            obj.is_active = True
            obj.created_by = self.users["tenant_admin"].id
            obj.metadata = {"seed_module_id": MODULE_ID}
            obj.save()
            questions[definition["slug"]] = obj

        groups = [
            {
                "name": "Enterprise Screening Questions",
                "section_name": "Screening",
                "target_type": "interview_type",
                "target_ref": "recruiter_screening",
                "items": ["sales-qualification", "support-escalation"],
            },
            {
                "name": "Backend Technical Core",
                "section_name": "Technical",
                "target_type": "interview_type",
                "target_ref": "technical_interview",
                "items": ["api-idempotency", "rate-limiter"],
            },
            {
                "name": "Leadership Signals",
                "section_name": "Leadership",
                "target_type": "interview_type",
                "target_ref": "leadership",
                "items": ["leadership-change"],
            },
        ]
        for group_def in groups:
            group, _ = InterviewQuestionGroup.objects.get_or_create(
                id=seed_uuid(f"question-group:{group_def['name']}"),
                defaults={
                    "tenant_id": self.tenant_id,
                    "scope": "tenant",
                    "name": group_def["name"],
                    "description": f"{group_def['name']} seeded for ICC question engine validation.",
                    "section_name": group_def["section_name"],
                    "target_type": group_def["target_type"],
                    "target_ref": group_def["target_ref"],
                    "order_index": 0,
                    "is_active": True,
                    "created_by": self.users["tenant_admin"].id,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
            group.items.all().delete()
            for index, slug in enumerate(group_def["items"]):
                InterviewQuestionGroupItem.objects.create(
                    group=group,
                    question=questions[slug],
                    order_index=index,
                    required=True,
                    metadata={"seed_module_id": MODULE_ID},
                )

        attachments = [
            ("sales-qualification", "interview_type", None, "recruiter_screening", ""),
            ("api-idempotency", "interview_type", None, "technical_interview", ""),
            ("rate-limiter", "interview_type", None, "system_design", ""),
            ("finance-variance", "template", self.unified_templates["Operations Case Study"].id, "", ""),
        ]
        for slug, attach_type, template_id, interview_type, assessment_ref in attachments:
            InterviewQuestionAttachment.objects.update_or_create(
                tenant_id=self.tenant_id,
                question=questions[slug],
                attach_type=attach_type,
                template_id=template_id,
                interview_type=interview_type,
                assessment_ref=assessment_ref,
                defaults={
                    "is_active": True,
                    "order_index": 0,
                    "created_by": self.users["tenant_admin"].id,
                    "is_deleted": False,
                    "deleted_at": None,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
        return questions

    def seed_jobs(self):
        jobs = {}
        definitions = [
            ("sales", "Sales Account Executive", "Drive pipeline generation, demos, and new business closure for SMB SaaS accounts.", ["sales discovery", "objection handling", "crm discipline"]),
            ("engineering", "Backend Engineer", "Build and maintain Python services, APIs, and reliability-focused backend systems.", ["python", "apis", "debugging", "postgresql"]),
            ("support", "Customer Support Specialist", "Resolve customer issues across chat and email while maintaining CSAT goals.", ["customer empathy", "de-escalation", "written communication"]),
            ("leadership", "Director of Operations", "Lead multi-team operational programs and executive stakeholder communication.", ["leadership", "change management", "stakeholder management"]),
        ]
        for slug, title, description, skills in definitions:
            job, _ = JobRequisition.objects.get_or_create(
                id=seed_uuid(f"job:{slug}"),
                defaults={
                    "job_ref_id": f"ICC-{slug[:3].upper()}-2026",
                    "tenant_id": self.tenant_id,
                    "title": title,
                    "status": "active",
                    "hiring_status": "active_hiring",
                    "description": description,
                    "requirements": description,
                    "responsibilities": description,
                    "skills_required": skills,
                    "job_type": "full_time",
                    "work_mode": "hybrid" if slug in {"sales", "leadership"} else "remote",
                    "experience_min": 1 if slug != "leadership" else 8,
                    "experience_max": 4 if slug != "leadership" else 14,
                    "priority": "high",
                    "created_by": self.users["tenant_admin"].id,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
            job.tenant_id = self.tenant_id
            job.title = title
            job.status = "active"
            job.hiring_status = "active_hiring"
            job.description = description
            job.requirements = description
            job.responsibilities = description
            job.skills_required = skills
            job.priority = "high"
            job.metadata = {"seed_module_id": MODULE_ID}
            job.save()
            JobStage.objects.filter(requisition_id=job.id).delete()
            for order, (name, stage_type) in enumerate(
                [
                    ("Application Review", "screening"),
                    ("Interview Flow", "interview"),
                    ("Offer", "offer"),
                ],
                start=1,
            ):
                JobStage.objects.create(
                    id=seed_uuid(f"job-stage:{slug}:{order}"),
                    tenant_id=self.tenant_id,
                    requisition_id=job.id,
                    name=name,
                    stage_order=order,
                    stage_type=stage_type,
                    action_deadline_hours=48,
                    is_active=True,
                    created_by=self.users["tenant_admin"].id,
                    metadata={"seed_module_id": MODULE_ID},
                )
            jobs[slug] = job
        return jobs

    def seed_candidates(self):
        definitions = [
            SeedCandidate("sales-pass", "Aisha", "Khan", "aisha.khan@demo.example.com", "Account Executive", "RevenueLeaf", "Mumbai", ["sales discovery", "objection handling"], 4, "Quota-carrying SaaS seller with strong discovery and closing discipline.", "https://cdn.demo.example.com/resumes/aisha-khan.pdf"),
            SeedCandidate("sales-reject", "Rahul", "Mehta", "rahul.mehta@demo.example.com", "Inside Sales Associate", "MarketPulse", "Pune", ["cold calling", "crm discipline"], 2, "High-activity inside sales associate transitioning to full-cycle SaaS sales.", "https://cdn.demo.example.com/resumes/rahul-mehta.pdf"),
            SeedCandidate("support-review", "Priya", "Nair", "priya.nair@demo.example.com", "Customer Support Associate", "CareLoop", "Bengaluru", ["customer empathy", "de-escalation"], 3, "Support associate with chat and email experience in B2B SaaS.", "https://cdn.demo.example.com/resumes/priya-nair.pdf"),
            SeedCandidate("engineering-tech", "Arjun", "Rao", "arjun.rao@demo.example.com", "Backend Developer", "CodeHarbor", "Hyderabad", ["python", "apis", "debugging"], 2, "Backend engineer with API and debugging experience in Python stacks.", "https://cdn.demo.example.com/resumes/arjun-rao.pdf"),
            SeedCandidate("leadership-pass", "Neha", "Iyer", "neha.iyer@demo.example.com", "Operations Manager", "ScalePilot", "Delhi", ["leadership", "change management"], 10, "Operations leader driving cross-functional process changes in scaled teams.", "https://cdn.demo.example.com/resumes/neha-iyer.pdf"),
            SeedCandidate("scheduled-sales", "Dev", "Kapoor", "dev.kapoor@demo.example.com", "Business Development Executive", "Outreachly", "Gurugram", ["sales development", "communication"], 1.5, "Early-career SDR moving into account executive responsibilities.", "https://cdn.demo.example.com/resumes/dev-kapoor.pdf"),
            SeedCandidate("candidate-expired", "Farah", "Ansari", "farah.ansari@demo.example.com", "Finance Associate", "LedgerBridge", "Mumbai", ["excel", "variance analysis"], 2, "Finance associate with reporting and forecasting support experience.", "https://cdn.demo.example.com/resumes/farah-ansari.pdf"),
            SeedCandidate("candidate-blocked", "Kunal", "Joshi", "kunal.joshi@demo.example.com", "Support Specialist", "HelpOrbit", "Pune", ["customer empathy", "written communication"], 2.5, "Customer support specialist with strong chat resolution metrics.", "https://cdn.demo.example.com/resumes/kunal-joshi.pdf"),
        ]
        rows = {}
        for definition in definitions:
            user, _ = CustomUser.objects.get_or_create(
                email=definition.email,
                defaults={
                    "id": seed_uuid(f"candidate-user:{definition.slug}"),
                    "tenant_id": self.tenant_id,
                    "first_name": definition.first_name,
                    "last_name": definition.last_name,
                    "role": "candidate",
                    "is_active": True,
                    "email_verified": True,
                    "timezone": "Asia/Kolkata",
                },
            )
            user.first_name = definition.first_name
            user.last_name = definition.last_name
            user.role = "candidate"
            user.tenant_id = self.tenant_id
            user.is_active = True
            user.email_verified = True
            user.set_password("testpass123")
            user.save()

            candidate, _ = Candidate.objects.get_or_create(
                id=user.id,
                defaults={
                    "candidate_ref_id": f"ICC-CAND-{definition.slug.replace('-', '').upper()}",
                    "tenant_id": self.tenant_id,
                    "first_name": definition.first_name,
                    "last_name": definition.last_name,
                    "email": definition.email,
                    "source": "company",
                    "current_title": definition.title,
                    "current_company": definition.company,
                    "current_location_city": definition.city,
                    "experience_years": as_decimal(definition.experience_years),
                    "relevant_experience_years": as_decimal(definition.experience_years),
                    "profile_status": "complete",
                    "account_status": "active",
                    "is_actively_looking": True,
                    "skills": definition.skills,
                    "workflow_mode": "manual",
                    "lifecycle_state": "active",
                    "engagement_stage": "qualified",
                    "candidate_state": "JOB_ASSOCIATED",
                    "candidate_pool": "GENERAL",
                    "created_by": self.users["tenant_admin"].id,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
            candidate.tenant_id = self.tenant_id
            candidate.first_name = definition.first_name
            candidate.last_name = definition.last_name
            candidate.email = definition.email
            candidate.source = "company"
            candidate.current_title = definition.title
            candidate.current_company = definition.company
            candidate.current_location_city = definition.city
            candidate.experience_years = as_decimal(definition.experience_years)
            candidate.relevant_experience_years = as_decimal(definition.experience_years)
            candidate.profile_status = "complete"
            candidate.account_status = "active"
            candidate.is_actively_looking = True
            candidate.skills = definition.skills
            candidate.workflow_mode = "manual"
            candidate.lifecycle_state = "active"
            candidate.engagement_stage = "qualified"
            candidate.candidate_state = "JOB_ASSOCIATED"
            candidate.candidate_pool = "GENERAL"
            candidate.metadata = {"seed_module_id": MODULE_ID}
            candidate.save()

            CandidateProfile.objects.update_or_create(
                candidate_id=candidate.id,
                defaults={
                    "tenant_id": self.tenant_id,
                    "summary": definition.summary,
                    "cv_url": definition.resume_url,
                    "created_by": self.users["tenant_admin"].id,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
            rows[definition.slug] = candidate
        return rows

    def seed_applications(self):
        rows = {}
        definitions = [
            ("sales-pass", "sales", "interview"),
            ("sales-reject", "sales", "interview"),
            ("support-review", "support", "interview"),
            ("engineering-tech", "engineering", "interview"),
            ("leadership-pass", "leadership", "shortlisted"),
            ("scheduled-sales", "sales", "screening"),
            ("candidate-expired", "engineering", "interview"),
            ("candidate-blocked", "support", "screening"),
        ]
        for candidate_slug, job_slug, status in definitions:
            candidate = self.candidates[candidate_slug]
            job = self.jobs[job_slug]
            app, _ = Application.objects.get_or_create(
                tenant_id=self.tenant_id,
                candidate_id=candidate.id,
                requisition_id=job.id,
                defaults={
                    "status": status,
                    "source": "direct",
                    "created_by": self.users["recruiter"].id,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
            app.status = status
            app.source = "direct"
            app.metadata = {"seed_module_id": MODULE_ID}
            app.save()
            rows[candidate_slug] = app
        return rows

    def seed_flows(self):
        flow_defs = {
            "Sales Hiring Flow": {
                "description": "AI-led screening flow for account executive hiring.",
                "linked_jobs": [self.jobs["sales"]],
                "stages": [
                    self.stage("sales-prequal", "Prequalification", "recruiter_screening", 1),
                    self.ai_stage("sales-ai", "Sales AI Screening", self.ai_templates["Sales AI Screening"], 2),
                    self.stage("sales-hm", "Hiring Manager Interview", "hiring_manager", 3, scorecard=self.scorecards["AI Screening Scorecard"]),
                    self.stage("sales-final", "Final Round", "final_round", 4, scorecard=self.scorecards["Final Round Scorecard"]),
                ],
            },
            "Engineering Hiring Flow": {
                "description": "AI technical screen followed by live engineering rounds.",
                "linked_jobs": [self.jobs["engineering"]],
                "stages": [
                    self.stage("eng-screen", "Recruiter Screening", "recruiter_screening", 1),
                    self.ai_stage("eng-ai", "Junior Developer AI Technical Screen", self.ai_templates["Junior Developer AI Technical Screen"], 2),
                    self.stage("eng-tech", "Technical Interview", "technical_interview", 3, scorecard=self.scorecards["Technical Scorecard"]),
                    self.stage("eng-system", "System Design", "system_design", 4, scorecard=self.scorecards["Technical Scorecard"]),
                    self.stage("eng-final", "Final Round", "final_round", 5, scorecard=self.scorecards["Final Round Scorecard"]),
                ],
            },
            "Support Hiring Flow": {
                "description": "Behavioral support screen with manual review path.",
                "linked_jobs": [self.jobs["support"]],
                "stages": [
                    self.stage("support-prequal", "Prequalification", "recruiter_screening", 1),
                    self.ai_stage("support-ai", "Support Behavioral AI", self.ai_templates["Customer Support Behavioral AI Screen"], 2),
                    self.stage("support-hr", "HR Interview", "hr_interview", 3, scorecard=self.scorecards["HR Scorecard"]),
                ],
            },
            "Leadership Hiring Flow": {
                "description": "Director-level leadership flow with one-way video and panel review.",
                "linked_jobs": [self.jobs["leadership"]],
                "stages": [
                    self.ai_stage("lead-ai", "Leadership One-Way Video", self.ai_templates["Leadership Behavioral One-Way Video"], 1),
                    self.stage("lead-panel", "Leadership Panel", "panel", 2, scorecard=self.scorecards["Panel Scorecard"]),
                    self.stage("lead-final", "Executive Final", "final_round", 3, scorecard=self.scorecards["Final Round Scorecard"]),
                ],
            },
        }
        flows = {}
        for name, definition in flow_defs.items():
            flow, _ = InterviewFlow.objects.get_or_create(
                tenant_id=self.tenant_id,
                name=name,
                defaults={
                    "description": definition["description"],
                    "stages": definition["stages"],
                    "created_by": self.users["tenant_admin"].id,
                    "is_active": True,
                    "metadata": {
                        "ai_flow_integration": True,
                        "linked_jobs": [
                            {"id": str(job.id), "title": job.title}
                            for job in definition["linked_jobs"]
                        ],
                        "seed_module_id": MODULE_ID,
                    },
                },
            )
            flow.description = definition["description"]
            flow.stages = definition["stages"]
            flow.is_active = True
            flow.metadata = {
                "ai_flow_integration": True,
                "linked_jobs": [
                    {"id": str(job.id), "title": job.title}
                    for job in definition["linked_jobs"]
                ],
                "seed_module_id": MODULE_ID,
            }
            flow.save()
            flows[name] = flow
        return flows

    def stage(self, slug, name, type_code, order, scorecard=None):
        return {
            "id": str(seed_uuid(f"flow-stage:{slug}")),
            "name": name,
            "type_code": type_code,
            "mode": "native" if type_code in {"technical_interview", "coding_interview"} else "manual",
            "order": order,
            "selection_category": self.category_for_type(type_code),
            "trigger_mode": "manual_trigger",
            "recruiter_review_required": False,
            "notify_recruiter": True,
            "generate_interview_link": True,
            "send_candidate_notification": True,
            "update_candidate_status": True,
            "scorecard_template_id": str(scorecard.id) if scorecard else "",
        }

    def ai_stage(self, slug, name, template, order):
        meta = template.metadata.get("ai_interview", {})
        setup = meta.get("setup", {})
        return {
            "id": str(seed_uuid(f"flow-stage:{slug}")),
            "name": f"AI Interview – {template.name}",
            "type_code": "ai_interview",
            "mode": "native",
            "order": order,
            "selection_category": "AI",
            "ai_template_id": str(template.id),
            "ai_template_name": template.name,
            "ai_interview_type": setup.get("interview_type", template.interview_type),
            "ai_duration_minutes": setup.get("duration_minutes", template.duration_minutes),
            "ai_response_mode": setup.get("response_mode", "video"),
            "ai_outcome_rules": meta.get("outcome_routing", {}).get("outcomes", []),
            "scorecard_template_id": str(meta.get("evaluation", {}).get("scorecard_template_id", "")),
            "trigger_mode": "auto_trigger",
            "recruiter_review_required": True,
            "notify_recruiter": True,
            "generate_interview_link": True,
            "send_candidate_notification": True,
            "update_candidate_status": True,
        }

    def category_for_type(self, type_code):
        if type_code.startswith("ai_") or type_code in {"async_text", "async_audio", "one_way_video"}:
            return "AI"
        if type_code in {"technical_interview", "coding_interview", "system_design"}:
            return "Technical"
        if type_code in {"recruiter_screening"}:
            return "Screening"
        if type_code in {"case_study", "take_home_assignment"}:
            return "Assessment"
        if type_code in {"role_play", "presentation"}:
            return "Advanced"
        return "Human"

    def seed_integrations(self):
        providers = [
            ("google_meet", "Google Meet", "meeting"),
            ("zoom", "Zoom", "meeting"),
            ("microsoft_teams", "Microsoft Teams", "meeting"),
            ("google_calendar", "Google Calendar", "calendar"),
            ("outlook_calendar", "Outlook Calendar", "calendar"),
            ("greenhouse_manual", "Greenhouse Manual", "external"),
        ]
        provider_rows = {}
        for code, name, provider_type in providers:
            provider, _ = InterviewIntegrationProvider.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "provider_type": provider_type,
                    "is_active": True,
                    "tenant_configurable": True,
                    "metadata": {"seed_module_id": MODULE_ID},
                },
            )
            provider.name = name
            provider.provider_type = provider_type
            provider.is_active = True
            provider.tenant_configurable = True
            provider.metadata = {**(provider.metadata or {}), "seed_module_id": MODULE_ID}
            provider.save()
            provider_rows[code] = provider

        connections = [
            ("zoom", self.users["scheduler"], {"meeting_owner": "scheduler"}, {"account_email": self.users["scheduler"].email}, "connected"),
            ("google_calendar", self.users["interviewer_1"], {"oauth_state": "seeded"}, {"calendar_id": "primary", "account_email": self.users["interviewer_1"].email}, "connected"),
            ("outlook_calendar", self.users["interviewer_2"], {"oauth_state": "seeded"}, {"calendar_id": "primary", "account_email": self.users["interviewer_2"].email}, "configured"),
        ]
        for code, user, auth_data, config_data, status in connections:
            InterviewTenantProviderConnection.objects.update_or_create(
                tenant_id=self.tenant_id,
                provider=provider_rows[code],
                defaults={
                    "auth_data": auth_data,
                    "config_data": config_data,
                    "is_enabled": True,
                    "connection_status": status,
                    "created_by": self.users["tenant_admin"].id,
                    "metadata": {"seed_module_id": MODULE_ID},
                    "is_deleted": False,
                    "deleted_at": None,
                },
            )

        mappings = [
            ("ai_screening", "", "native", "zoom"),
            ("one_way_video", "", "native", "google_meet"),
            ("technical_interview", "round_2", "external_manual", "greenhouse_manual"),
            ("system_design", "", "manual", ""),
        ]
        for interview_type, stage_code, execution_mode, provider_code in mappings:
            InterviewExecutionMapping.objects.update_or_create(
                tenant_id=self.tenant_id,
                interview_type=interview_type,
                stage_code=stage_code,
                defaults={
                    "execution_mode": execution_mode if execution_mode in {"native", "third_party", "external_manual"} else "native",
                    "provider_code": provider_code,
                    "is_active": True,
                    "created_by": self.users["tenant_admin"].id,
                    "metadata": {"seed_module_id": MODULE_ID},
                    "is_deleted": False,
                    "deleted_at": None,
                },
            )

    def seed_scheduling_setup(self):
        InterviewAvailabilityProfile.objects.update_or_create(
            tenant_id=self.tenant_id,
            interviewer_id=self.users["scheduler"].id,
            defaults={
                "mode": "calendar",
                "timezone": "Asia/Kolkata",
                "working_hours": {
                    "mon": {"enabled": True, "start": "09:00", "end": "18:00"},
                    "tue": {"enabled": True, "start": "09:00", "end": "18:00"},
                    "wed": {"enabled": True, "start": "09:00", "end": "18:00"},
                    "thu": {"enabled": True, "start": "09:00", "end": "18:00"},
                    "fri": {"enabled": True, "start": "09:00", "end": "17:00"},
                    "sat": {"enabled": False, "start": "09:00", "end": "18:00"},
                    "sun": {"enabled": False, "start": "09:00", "end": "18:00"},
                },
                "default_duration_minutes": 45,
                "default_buffer_minutes": 15,
                "is_active": True,
            },
        )
        for slug, starts_in_days, reason in [
            ("scheduler-ooo", 2, "Leadership offsite"),
            ("scheduler-hiring-sync", 5, "Hiring sync block"),
        ]:
            start = self.now + timedelta(days=starts_in_days, hours=2)
            InterviewAvailabilityBlock.objects.update_or_create(
                id=seed_uuid(f"availability-block:{slug}"),
                defaults={
                    "tenant_id": self.tenant_id,
                    "interviewer_id": self.users["scheduler"].id,
                    "starts_at": start,
                    "ends_at": start + timedelta(hours=2),
                    "reason": reason,
                    "source": "manual",
                    "created_by": self.users["scheduler"].id,
                },
            )
        InterviewCalendarConnection.objects.update_or_create(
            tenant_id=self.tenant_id,
            interviewer_id=self.users["scheduler"].id,
            provider="google",
            external_calendar_id="primary",
            defaults={
                "account_email": self.users["scheduler"].email,
                "is_active": True,
                "sync_enabled": True,
                "last_synced_at": self.now,
                "metadata": {"seed_module_id": MODULE_ID},
            },
        )

    def seed_interviews(self):
        interviews = {}
        definitions = [
            {
                "slug": "sales-pass",
                "application_slug": "sales-pass",
                "template": self.ai_templates["Sales AI Screening"],
                "scorecard": self.scorecards["AI Screening Scorecard"],
                "interview_type": "ai_screening",
                "status": "completed",
                "scheduled_at": self.now - timedelta(days=4),
                "started_at": self.now - timedelta(days=4, minutes=-10),
                "completed_at": self.now - timedelta(days=4, minutes=-35),
                "duration_minutes": 20,
                "title": "Sales AI Screening",
                "ai_score": 88,
                "human_score": 82,
                "overall_score": 86,
                "recommendation": "recommend",
                "feedback_summary": "Strong qualification discipline and clear objection handling.",
                "decision": ("next_round", "automation_rules", "auto", "Advance to hiring manager interview"),
                "question_answers": [
                    ("Walk through how you qualify a new inbound lead before booking a demo.", "I start with the problem, business impact, who owns the decision, and whether there is urgency tied to the deal."),
                    ("Tell us about a stalled opportunity you revived and what changed.", "I diagnosed a stalled procurement path, rebuilt the mutual action plan, and secured legal review within the week."),
                ],
                "candidate_runtime": self.runtime_shell("submitted"),
                "metadata_extra": {"scenario": "SCENARIO 1 — AI Screening Flow", "outcome_label": "Recommend", "routed_to": "Hiring Manager Interview"},
            },
            {
                "slug": "sales-reject",
                "application_slug": "sales-reject",
                "template": self.ai_templates["Sales AI Screening"],
                "scorecard": self.scorecards["AI Screening Scorecard"],
                "interview_type": "ai_screening",
                "status": "completed",
                "scheduled_at": self.now - timedelta(days=3),
                "started_at": self.now - timedelta(days=3, minutes=-5),
                "completed_at": self.now - timedelta(days=3, minutes=-20),
                "duration_minutes": 20,
                "title": "Sales AI Screening",
                "ai_score": 24,
                "human_score": 30,
                "overall_score": 27,
                "recommendation": "reject",
                "feedback_summary": "Low qualification depth and weak ownership examples.",
                "decision": ("reject", "automation_rules", "auto", "Low qualification signal. Reject candidate."),
                "question_answers": [
                    ("Walk through how you qualify a new inbound lead before booking a demo.", "I mainly look at whether they replied and seem interested."),
                    ("Tell us about a stalled opportunity you revived and what changed.", "I usually send another follow-up and hope the prospect replies."),
                ],
                "candidate_runtime": self.runtime_shell("submitted"),
                "metadata_extra": {"scenario": "SCENARIO 2 — AI Screening Reject", "outcome_label": "Reject", "routed_to": "Reject Candidate"},
            },
            {
                "slug": "support-review",
                "application_slug": "support-review",
                "template": self.ai_templates["Customer Support Behavioral AI Screen"],
                "scorecard": self.scorecards["Behavioral Scorecard"],
                "interview_type": "ai_behavioral",
                "status": "completed",
                "scheduled_at": self.now - timedelta(days=2),
                "started_at": self.now - timedelta(days=2, minutes=-8),
                "completed_at": self.now - timedelta(days=2, minutes=-25),
                "duration_minutes": 18,
                "title": "Support Behavioral AI Screen",
                "ai_score": 58,
                "human_score": 55,
                "overall_score": 57,
                "recommendation": "neutral",
                "feedback_summary": "Good empathy but mixed ownership signals. Needs recruiter review.",
                "decision": ("manual_review", "automation_rules", "conditional", "Borderline AI result routed to manual review queue."),
                "question_answers": [
                    ("Describe a situation where an angry customer contacted you and how you de-escalated it.", "I acknowledged the frustration, summarized the issue, and committed to a precise update window."),
                    ("Share an example where you partnered with another team to resolve a customer issue.", "I worked with engineering and kept the customer updated twice a day while we validated the fix."),
                ],
                "candidate_runtime": self.runtime_shell("submitted"),
                "metadata_extra": {"scenario": "SCENARIO 4 — Manual Review", "outcome_label": "Neutral", "routed_to": "Manual Review Queue"},
            },
            {
                "slug": "engineering-tech",
                "application_slug": "engineering-tech",
                "template": self.unified_templates["Structured Technical Round"],
                "scorecard": self.scorecards["Technical Scorecard"],
                "interview_type": "technical_interview",
                "status": "scheduled",
                "scheduled_at": self.now + timedelta(days=2, hours=3),
                "started_at": None,
                "completed_at": None,
                "duration_minutes": 60,
                "title": "Technical Interview",
                "ai_score": None,
                "human_score": None,
                "overall_score": None,
                "recommendation": "",
                "feedback_summary": "",
                "decision": None,
                "question_answers": [
                    ("Explain how you would debug an intermittent API timeout issue.", ""),
                    ("Design an endpoint for creating and fetching support tickets.", ""),
                ],
                "candidate_runtime": self.runtime_shell("invited"),
                "panelists": [self.users["interviewer_1"], self.users["interviewer_2"]],
                "metadata_extra": {"scenario": "SCENARIO 3 — Technical Flow", "stage_visible_in_flow": True},
            },
            {
                "slug": "leadership-pass",
                "application_slug": "leadership-pass",
                "template": self.ai_templates["Leadership Behavioral One-Way Video"],
                "scorecard": self.scorecards["Final Round Scorecard"],
                "interview_type": "one_way_video",
                "status": "completed",
                "scheduled_at": self.now - timedelta(days=1, hours=5),
                "started_at": self.now - timedelta(days=1, hours=5) + timedelta(minutes=15),
                "completed_at": self.now - timedelta(days=1, hours=4, minutes=20),
                "duration_minutes": 30,
                "title": "Leadership One-Way Video",
                "ai_score": 93,
                "human_score": 90,
                "overall_score": 92,
                "recommendation": "strongly_recommend",
                "feedback_summary": "Strong strategic framing and executive presence.",
                "decision": ("next_round", "automation_rules", "auto", "Advance to leadership panel."),
                "question_answers": [
                    ("Describe a difficult operational change you led and how you secured stakeholder buy-in.", "I aligned finance, operations, and customer success around a phased rollout with clear success measures."),
                    ("Tell us about a time you had to make a decision with incomplete data and how you managed the risk.", "I set guardrails, escalated tradeoffs, and ran a controlled launch with weekly review checkpoints."),
                ],
                "candidate_runtime": self.runtime_shell("submitted"),
                "metadata_extra": {"scenario": "Leadership AI flow", "outcome_label": "Strong Recommend", "routed_to": "Leadership Panel"},
            },
            {
                "slug": "scheduled-sales",
                "application_slug": "scheduled-sales",
                "template": self.ai_templates["Sales AI Screening"],
                "scorecard": self.scorecards["AI Screening Scorecard"],
                "interview_type": "ai_screening",
                "status": "scheduled",
                "scheduled_at": self.now + timedelta(days=1, hours=2),
                "started_at": None,
                "completed_at": None,
                "duration_minutes": 20,
                "title": "Sales AI Screening",
                "ai_score": None,
                "human_score": None,
                "overall_score": None,
                "recommendation": "",
                "feedback_summary": "",
                "decision": None,
                "question_answers": [
                    ("Walk through how you qualify a new inbound lead before booking a demo.", ""),
                    ("Tell us about a stalled opportunity you revived and what changed.", ""),
                ],
                "candidate_runtime": self.runtime_shell("invited"),
                "metadata_extra": {"scenario": "SCENARIO 5 — Scheduling / Operations", "candidate_state": "invited"},
                "create_scheduling_link": True,
            },
            {
                "slug": "candidate-expired",
                "application_slug": "candidate-expired",
                "template": self.ai_templates["Finance Analyst Async Text Screen"],
                "scorecard": self.scorecards["Behavioral Scorecard"],
                "interview_type": "async_text",
                "status": "scheduled",
                "scheduled_at": self.now - timedelta(days=1),
                "started_at": None,
                "completed_at": None,
                "duration_minutes": 25,
                "title": "Finance Async Text Screen",
                "ai_score": None,
                "human_score": None,
                "overall_score": None,
                "recommendation": "",
                "feedback_summary": "",
                "decision": None,
                "question_answers": [
                    ("How would you explain a 12% month-over-month expense increase to a business leader?", ""),
                    ("Describe the inputs you would validate before finalizing a quarterly forecast.", ""),
                ],
                "candidate_runtime": self.runtime_shell("expired"),
                "metadata_extra": {"candidate_state": "expired"},
            },
            {
                "slug": "candidate-blocked",
                "application_slug": "candidate-blocked",
                "template": self.ai_templates["Customer Support Behavioral AI Screen"],
                "scorecard": self.scorecards["Behavioral Scorecard"],
                "interview_type": "ai_behavioral",
                "status": "scheduled",
                "scheduled_at": self.now + timedelta(hours=8),
                "started_at": None,
                "completed_at": None,
                "duration_minutes": 18,
                "title": "Support Behavioral AI Screen",
                "ai_score": None,
                "human_score": None,
                "overall_score": None,
                "recommendation": "",
                "feedback_summary": "",
                "decision": None,
                "question_answers": [
                    ("Describe a situation where an angry customer contacted you and how you de-escalated it.", ""),
                    ("Share an example where you partnered with another team to resolve a customer issue.", ""),
                ],
                "candidate_runtime": self.runtime_shell("blocked"),
                "metadata_extra": {"candidate_state": "blocked"},
            },
            {
                "slug": "panel-awaiting-decision",
                "application_slug": "engineering-tech",
                "template": self.unified_templates["Structured Technical Round"],
                "scorecard": self.scorecards["Panel Scorecard"],
                "interview_type": "panel",
                "status": "completed",
                "scheduled_at": self.now - timedelta(days=1, hours=2),
                "started_at": self.now - timedelta(days=1, hours=2) + timedelta(minutes=5),
                "completed_at": self.now - timedelta(days=1, hours=1),
                "duration_minutes": 55,
                "title": "Technical Panel",
                "ai_score": 78,
                "human_score": 80,
                "overall_score": 79,
                "recommendation": "recommend",
                "feedback_summary": "Panel feedback submitted. Final decision pending.",
                "decision": None,
                "question_answers": [
                    ("Design a rate limiter for a public API.", ""),
                    ("Explain a tradeoff you would make between consistency and availability.", ""),
                ],
                "candidate_runtime": self.runtime_shell("submitted"),
                "panelists": [self.users["panelist_1"], self.users["panelist_2"]],
                "feedbacks": [
                    (self.users["panelist_1"], 4, "hire", {"Leadership": 4, "Collaboration": 4, "Problem Solving": 5, "Executive Presence": 4}, "Structured thinking and calm reasoning."),
                    (self.users["panelist_2"], 3, "next_round", {"Leadership": 3, "Collaboration": 4, "Problem Solving": 4, "Executive Presence": 3}, "Good fundamentals, final decision can wait for HM review."),
                ],
                "metadata_extra": {"scenario": "Awaiting decision with panel feedback"},
            },
            {
                "slug": "in-progress-runtime",
                "application_slug": "support-review",
                "template": self.ai_templates["Customer Support Behavioral AI Screen"],
                "scorecard": self.scorecards["Behavioral Scorecard"],
                "interview_type": "ai_behavioral",
                "status": "in_progress",
                "scheduled_at": self.now,
                "started_at": self.now - timedelta(minutes=12),
                "completed_at": None,
                "duration_minutes": 18,
                "title": "Support Behavioral AI Screen",
                "ai_score": None,
                "human_score": None,
                "overall_score": None,
                "recommendation": "",
                "feedback_summary": "",
                "decision": None,
                "question_answers": [
                    ("Describe a situation where an angry customer contacted you and how you de-escalated it.", "I first acknowledged the frustration and clarified the exact problem."),
                    ("Share an example where you partnered with another team to resolve a customer issue.", ""),
                ],
                "candidate_runtime": self.runtime_shell("started"),
                "metadata_extra": {"candidate_state": "started"},
            },
        ]

        for definition in definitions:
            app = self.applications[definition["application_slug"]]
            candidate = self.candidates[definition["application_slug"]]
            job = self.jobs[
                "sales" if definition["application_slug"] in {"sales-pass", "sales-reject", "scheduled-sales"} else
                "support" if definition["application_slug"] in {"support-review", "candidate-blocked"} else
                "engineering" if definition["application_slug"] in {"engineering-tech", "candidate-expired"} else
                "leadership"
            ]
            interview, _ = Interview.objects.update_or_create(
                id=seed_uuid(f"interview:{definition['slug']}"),
                defaults={
                    "tenant_id": self.tenant_id,
                    "application_id": app.id,
                    "candidate_id": candidate.id,
                    "requisition_id": job.id,
                    "template_id": definition["template"].id,
                    "scorecard_template_id": definition["scorecard"].id,
                    "interview_type": definition["interview_type"],
                    "interview_round": 1,
                    "title": definition["title"],
                    "scheduled_at": definition["scheduled_at"],
                    "started_at": definition["started_at"],
                    "completed_at": definition["completed_at"],
                    "duration_minutes": definition["duration_minutes"],
                    "status": definition["status"],
                    "execution_mode": "native" if definition["interview_type"].startswith("ai_") or definition["interview_type"] in {"one_way_video", "async_text"} else "manual",
                    "overall_score": definition["overall_score"],
                    "ai_score": definition["ai_score"],
                    "human_score": definition["human_score"],
                    "recommendation": definition["recommendation"],
                    "feedback_summary": definition["feedback_summary"],
                    "created_by": self.users["recruiter"].id,
                    "metadata": {
                        "seed_module_id": MODULE_ID,
                        "candidate_runtime_access": definition["candidate_runtime"],
                        "ai_result_shell": {
                            "score": definition["ai_score"],
                            "recommendation": definition["recommendation"],
                        },
                        **definition.get("metadata_extra", {}),
                    },
                },
            )
            InterviewQuestion.objects.filter(interview_id=interview.id).delete()
            for index, (question_text, answer_text) in enumerate(definition["question_answers"], start=1):
                question_type = "text" if definition["interview_type"] == "async_text" else "video" if definition["interview_type"] in {"ai_screening", "ai_technical", "one_way_video"} else "audio" if definition["interview_type"] == "ai_behavioral" else "text"
                InterviewQuestion.objects.create(
                    id=seed_uuid(f"interview-question:{definition['slug']}:{index}"),
                    tenant_id=self.tenant_id,
                    interview_id=interview.id,
                    question_text=question_text,
                    question_type=question_type,
                    expected_duration_seconds=90,
                    candidate_answer=answer_text,
                    ai_score=as_decimal(definition["ai_score"] or 0) if answer_text and definition["ai_score"] is not None else None,
                    ai_feedback="Seeded AI evaluation feedback." if answer_text and definition["ai_score"] is not None else "",
                    human_score=as_decimal(definition["human_score"] or 0) if answer_text and definition["human_score"] is not None else None,
                    human_feedback="Seeded human review feedback." if answer_text and definition["human_score"] is not None else "",
                    order_index=index,
                    answered_at=definition["completed_at"] if answer_text and definition["completed_at"] else definition["started_at"],
                    metadata={"seed_module_id": MODULE_ID},
                )

            InterviewPanelist.objects.filter(interview_id=interview.id).delete()
            for user in definition.get("panelists", []):
                InterviewPanelist.objects.create(
                    tenant_id=self.tenant_id,
                    interview_id=interview.id,
                    interviewer_id=user.id,
                    role="panelist",
                    deadline_at=definition["scheduled_at"] + timedelta(hours=24) if definition["scheduled_at"] else None,
                    metadata={"seed_module_id": MODULE_ID},
                )

            InterviewFeedback.objects.filter(interview_id=interview.id).delete()
            for feedback_user, score, recommendation, ratings, notes in definition.get("feedbacks", []):
                InterviewFeedback.objects.create(
                    tenant_id=self.tenant_id,
                    interview_id=interview.id,
                    panelist_id=feedback_user.id,
                    score=as_decimal(score),
                    notes=notes,
                    recommendation=recommendation,
                    scorecard_ratings=ratings,
                    metadata={"seed_module_id": MODULE_ID},
                )

            InterviewDecision.objects.filter(interview_id=interview.id).delete()
            InterviewDecisionHistory.objects.filter(interview_id=interview.id).delete()
            if definition.get("decision"):
                decision, source, mode, notes = definition["decision"]
                decision_obj = InterviewDecision.objects.create(
                    tenant_id=self.tenant_id,
                    interview_id=interview.id,
                    decision=decision,
                    decision_source=source,
                    decision_mode=mode,
                    notes=notes,
                    previous_decision="",
                    is_override=False,
                    decided_by=self.users["recruiter"].id,
                    metadata={"seed_module_id": MODULE_ID},
                )
                InterviewDecisionHistory.objects.create(
                    id=seed_uuid(f"decision-history:{definition['slug']}"),
                    tenant_id=self.tenant_id,
                    interview_id=interview.id,
                    decision_id=decision_obj.id,
                    previous_decision="",
                    new_decision=decision,
                    changed_by=self.users["recruiter"].id,
                    change_source=source,
                    is_override=False,
                    metadata={"seed_module_id": MODULE_ID},
                )

            if definition.get("create_scheduling_link"):
                InterviewSchedulingLink.objects.update_or_create(
                    interview_id=interview.id,
                    defaults={
                        "tenant_id": self.tenant_id,
                        "token": seed_uuid(f"scheduling-link:{definition['slug']}").hex,
                        "timezone": "Asia/Kolkata",
                        "expires_at": self.now + timedelta(days=5),
                        "max_bookings": 1,
                        "booking_count": 0,
                        "is_active": True,
                        "metadata": {"mode": "candidate_self", "seed_module_id": MODULE_ID},
                        "created_by": self.users["scheduler"].id,
                    },
                )
            interviews[definition["slug"]] = interview
        return interviews

    def runtime_shell(self, state):
        token = seed_uuid(f"runtime-token:{state}").hex
        base = {
            "token": token,
            "token_expires_at": (self.now + timedelta(days=2)).isoformat(),
            "single_attempt": True,
            "attempts_used": 0,
            "attempt_status": "pending",
            "active_session_id": "",
            "rejoin_count": 0,
            "attempt_history": [],
            "security_events": {
                "tab_switch_count": 0,
                "copy_paste_count": 0,
                "multiple_window_count": 0,
                "last_event_at": None,
            },
            "not_before": (self.now - timedelta(hours=1)).isoformat(),
            "expires_at": (self.now + timedelta(hours=8)).isoformat(),
        }
        if state == "submitted":
            base["attempts_used"] = 1
            base["attempt_status"] = "completed"
            base["attempt_history"] = [{"attempt_no": 1, "status": "completed"}]
        elif state == "started":
            base["attempts_used"] = 1
            base["attempt_status"] = "in_progress"
            base["active_session_id"] = seed_uuid("runtime-session:started").hex
            base["attempt_history"] = [{"attempt_no": 1, "status": "in_progress"}]
        elif state == "expired":
            base["token_expires_at"] = (self.now - timedelta(hours=1)).isoformat()
            base["expires_at"] = (self.now - timedelta(minutes=15)).isoformat()
            base["attempt_status"] = "expired"
        elif state == "blocked":
            base["attempts_used"] = 1
            base["attempt_status"] = "blocked"
            base["attempt_history"] = [{"attempt_no": 1, "status": "blocked"}]
        return base

    def refresh_usage_metadata(self):
        flow_usage_by_template = {}
        for flow in self.flows.values():
            for stage in flow.stages or []:
                template_id = stage.get("ai_template_id")
                if not template_id:
                    continue
                flow_usage_by_template.setdefault(template_id, {"linked_flows": [], "linked_stages": []})
                flow_usage_by_template[template_id]["linked_flows"].append({"id": str(flow.id), "name": flow.name})
                flow_usage_by_template[template_id]["linked_stages"].append(
                    {"flow_id": str(flow.id), "flow_name": flow.name, "stage_name": stage.get("name", "")}
                )

        job_usage = {
            str(self.ai_templates["Sales AI Screening"].id): [{"id": str(self.jobs["sales"].id), "title": self.jobs["sales"].title}],
            str(self.ai_templates["Customer Support Behavioral AI Screen"].id): [{"id": str(self.jobs["support"].id), "title": self.jobs["support"].title}],
            str(self.ai_templates["Junior Developer AI Technical Screen"].id): [{"id": str(self.jobs["engineering"].id), "title": self.jobs["engineering"].title}],
            str(self.ai_templates["Finance Analyst Async Text Screen"].id): [{"id": str(self.jobs["engineering"].id), "title": "Finance Analyst Pilot Role"}],
            str(self.ai_templates["Leadership Behavioral One-Way Video"].id): [{"id": str(self.jobs["leadership"].id), "title": self.jobs["leadership"].title}],
        }

        for template in self.ai_templates.values():
            metadata = template.metadata or {}
            ai_meta = metadata.get("ai_interview", {})
            usage = flow_usage_by_template.get(str(template.id), {"linked_flows": [], "linked_stages": []})
            ai_meta["usage"] = {
                "linked_jobs": job_usage.get(str(template.id), []),
                "linked_flows": usage["linked_flows"],
                "linked_stages": usage["linked_stages"],
            }
            metadata["ai_interview"] = ai_meta
            metadata["seed_module_id"] = MODULE_ID
            template.metadata = metadata
            template.save(update_fields=["metadata", "updated_at"])
