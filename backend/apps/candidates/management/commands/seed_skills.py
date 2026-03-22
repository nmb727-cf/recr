from django.core.management.base import BaseCommand
from apps.candidates.models import Skill

SKILLS = [
    # Programming Languages
    ('Python', 'Programming'), ('JavaScript', 'Programming'),
    ('TypeScript', 'Programming'), ('Java', 'Programming'),
    ('C++', 'Programming'), ('C#', 'Programming'),
    ('Go', 'Programming'), ('Rust', 'Programming'),
    ('Ruby', 'Programming'), ('PHP', 'Programming'),
    ('Swift', 'Programming'), ('Kotlin', 'Programming'),
    ('R', 'Programming'), ('Scala', 'Programming'),
    # Frontend
    ('React', 'Frontend'), ('Vue.js', 'Frontend'),
    ('Angular', 'Frontend'), ('Next.js', 'Frontend'),
    ('HTML', 'Frontend'), ('CSS', 'Frontend'),
    ('Tailwind CSS', 'Frontend'), ('Redux', 'Frontend'),
    # Backend
    ('Django', 'Backend'), ('FastAPI', 'Backend'),
    ('Node.js', 'Backend'), ('Express.js', 'Backend'),
    ('Spring Boot', 'Backend'), ('Laravel', 'Backend'),
    ('Rails', 'Backend'), ('Flask', 'Backend'),
    # Cloud & DevOps
    ('AWS', 'Cloud'), ('GCP', 'Cloud'), ('Azure', 'Cloud'),
    ('Docker', 'DevOps'), ('Kubernetes', 'DevOps'),
    ('Terraform', 'DevOps'), ('CI/CD', 'DevOps'),
    ('Jenkins', 'DevOps'), ('GitHub Actions', 'DevOps'),
    # Data
    ('PostgreSQL', 'Database'), ('MySQL', 'Database'),
    ('MongoDB', 'Database'), ('Redis', 'Database'),
    ('Elasticsearch', 'Database'), ('Snowflake', 'Data'),
    ('Spark', 'Data'), ('Kafka', 'Data'),
    ('Pandas', 'Data'), ('NumPy', 'Data'),
    ('TensorFlow', 'AI/ML'), ('PyTorch', 'AI/ML'),
    ('Scikit-learn', 'AI/ML'), ('LangChain', 'AI/ML'),
    # Design
    ('Figma', 'Design'), ('Adobe XD', 'Design'),
    ('Sketch', 'Design'), ('Photoshop', 'Design'),
    ('UI/UX Design', 'Design'), ('Prototyping', 'Design'),
    # Management
    ('Project Management', 'Management'),
    ('Agile', 'Management'), ('Scrum', 'Management'),
    ('JIRA', 'Management'), ('Product Management', 'Management'),
    # Soft skills
    ('Leadership', 'Soft Skills'),
    ('Communication', 'Soft Skills'),
    ('Problem Solving', 'Soft Skills'),
    # Finance/Business
    ('Financial Modeling', 'Finance'),
    ('Excel', 'Business'), ('PowerPoint', 'Business'),
    ('Sales', 'Business'), ('Marketing', 'Business'),
    ('SEO', 'Marketing'), ('Content Writing', 'Marketing'),
]

class Command(BaseCommand):
    help = 'Seed skills master data'

    def handle(self, *args, **kwargs):
        created = 0
        for name, category in SKILLS:
            _, was_created = Skill.objects.get_or_create(
                name=name,
                defaults={'category': category}
            )
            if was_created:
                created += 1
        self.stdout.write(
            f'Seeded {created} new skills '
            f'({len(SKILLS) - created} already existed)'
        )
