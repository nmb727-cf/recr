import uuid
from apps.jobs.models import JobRequisition
from apps.prequalification.models import PrequalForm, PrequalSection, PrequalQuestion
from apps.interviews.models import InterviewTemplate, InterviewScorecardTemplate, InterviewScorecardAttribute

def create_templates():
    tenant_id = uuid.UUID('f26e9892-d729-45a2-a673-4133ce3b4326') 
    user_id = uuid.uuid4()

    print("Creating Job Registry Templates...")
    job_titles = [
        "Senior Software Engineer", "Product Manager", "UX Designer", "DevOps Lead", 
        "Data Scientist", "Marketing Manager", "Sales Executive", "HR Business Partner",
        "Solutions Architect", "Frontend Developer", "Backend Developer", "Mobile Engineer",
        "QA Automation Engineer", "Project Coordinator", "Customer Success Manager"
    ]
    for title in job_titles:
        JobRequisition.objects.create(
            tenant_id=tenant_id,
            title=title,
            job_type='full_time',
            work_mode='hybrid',
            experience_min=3,
            experience_max=8,
            status='draft',
            created_by=user_id,
            description=f"Standard template for {title} role."
        )

    print("Creating Prequalification Templates...")
    prequal_names = [
        "Engineering Core Skills", "Management Experience", "Design Portfolio Review", 
        "Cultural Alignment", "Technical Proficiency Test", "Sales Target History",
        "Logistics & Operations", "Remote Work Readiness", "Leadership Competency",
        "Entry Level Aptitude", "Executive Strategy", "Security Compliance",
        "Customer Handling Skills", "Marketing Analytics", "Agile Methodology"
    ]
    for name in prequal_names:
        form = PrequalForm.objects.create(
            tenant_id=tenant_id,
            name=name,
            description=f"Prequalification criteria for {name}.",
            created_by=user_id
        )
        section = PrequalSection.objects.create(
            tenant_id=tenant_id,
            form=form,
            title="General Questions",
            order=1
        )
        PrequalQuestion.objects.create(
            tenant_id=tenant_id,
            section=section,
            question_text="Years of relevant experience?",
            question_type='number',
            order=1
        )

    print("Creating Scorecard Templates...")
    scorecard_names = [
        "Technical Coding Rubric", "Soft Skills Evaluation", "Leadership Assessment", 
        "System Design Grade", "Behavioral Interview Scorecard", "Sales Pitch Evaluation",
        "Analytical Thinking", "Team Collaboration Score", "Product Strategy Matrix",
        "Visual Design Critique", "DevOps Knowledge", "QA Process Audit",
        "HR Policy Review", "Client Interaction Score", "Executive Presence"
    ]
    for name in scorecard_names:
        scorecard = InterviewScorecardTemplate.objects.create(
            tenant_id=tenant_id,
            name=name,
            description=f"Standard scorecard for {name}.",
            interview_type='technical_interview' if "Technical" in name else 'behavioral',
            created_by=user_id
        )
        InterviewScorecardAttribute.objects.create(
            tenant_id=tenant_id,
            scorecard=scorecard,
            attribute_name="Technical Accuracy",
            weight=5.0,
            rating_type='scale_1_5'
        )
        InterviewScorecardAttribute.objects.create(
            tenant_id=tenant_id,
            scorecard=scorecard,
            attribute_name="Communication",
            weight=3.0,
            rating_type='scale_1_5'
        )

    print("Creating Live Interview Templates...")
    interview_templates = [
        "Standard Coding Interview", "Deep Dive Architecture", "Behavioral Round 1", 
        "Hiring Manager Meet", "UX Whiteboarding", "Sales Simulation",
        "Executive Strategy Session", "HR Culture Round", "Peer Technical Review",
        "Final Leadership Interview", "Case Study Discussion", "Bug Squash Session",
        "Product Thinking", "Stakeholder Alignment", "Team Fit Lunch"
    ]
    for name in interview_templates:
        InterviewTemplate.objects.create(
            tenant_id=tenant_id,
            name=name,
            description=f"Template for {name} session.",
            interview_type='coding_interview' if "Coding" in name else 'technical_interview',
            duration_minutes=60,
            instructions="Follow the standard interview protocol.",
            scoring_type='numeric',
            created_by=user_id
        )

    print("All templates created successfully.")

create_templates()
