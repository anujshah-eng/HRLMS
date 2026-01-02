import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.user_management import Role, User, UserRole
from models.tenant import Tenant
from models.ai_interview_model import AIInterviewRoles, AIInterviewers
from models.usage_models import SubscriptionPlan, UsageQuota
from models.organization import Designation
from custom_utilities.custom_exception import CustomException
from custom_utilities.validation_utitility import ValidationUtility

def seed_initial_data(db_session: Session) -> None:
    """Seed all initial database data."""
    insert_default_tenant(db_session)
    insert_default_roles(db_session)
    insert_default_superadmin(db_session)
    insert_default_subscription_plans(db_session)
    insert_default_usage_quotas(db_session)
    insert_default_designation(db_session)
    insert_default_interview_roles(db_session)
    insert_default_interviewers(db_session)
    insert_default_department_and_batch(db_session)


def insert_default_tenant(db_session: Session):
    key = os.getenv("DEFAULT_TENANT_KEY", "ace")
    name = os.getenv("DEFAULT_TENANT_NAME", "acelucid")
    domain = os.getenv("DEFAULT_TENANT_DOMAIN", "acelucid.com")
    existing = db_session.query(Tenant).filter(Tenant.key == key).first()
    if existing:
        print("Default tenant already exists.")
        return
    tenant = Tenant(key=key, name=name, domain=domain)
    db_session.add(tenant)
    db_session.commit()
    print("Default tenant created.")

def insert_default_interview_roles(db_session: Session):
    """Insert default AI interview roles."""

    now = datetime.now(timezone.utc)

    default_roles = [
        # Software Development Roles
        {
            "title": "Software Trainee",
            "description": "Entry-level software development position for freshers",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Full Stack Trainee",
            "description": "Entry-level full-stack development position covering both frontend and backend",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Backend Developer Trainee",
            "description": "Entry-level backend development position focusing on server-side development",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Frontend Developer Trainee",
            "description": "Entry-level frontend development position focusing on UI development",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Associate Software Engineer",
            "description": "Junior software engineering position with basic development responsibilities",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Junior Developer",
            "description": "Entry-level developer position working on software applications",
            "created_at": now,
            "updated_at": now
        },

        # Testing & QA Roles
        {
            "title": "Testing Engineer / QA Engineer Trainee",
            "description": "Entry-level quality assurance and testing position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Automation Test Engineer",
            "description": "Entry-level automation testing position focusing on test automation frameworks",
            "created_at": now,
            "updated_at": now
        },

        # Support & Infrastructure Roles
        {
            "title": "Support Engineer / Service Desk",
            "description": "Entry-level technical support and service desk position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Cloud Support Engineer",
            "description": "Entry-level cloud infrastructure support position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "IT Analyst Trainee",
            "description": "Entry-level IT analysis position for system and technology evaluation",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Technical Support Engineer",
            "description": "Entry-level technical support position providing customer assistance",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Product Support Specialist",
            "description": "Entry-level product support position assisting customers with product issues",
            "created_at": now,
            "updated_at": now
        },

        # Business Analysis & Operations Roles
        {
            "title": "Business Analyst Trainee",
            "description": "Entry-level business analysis position analyzing business requirements",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Business Systems Analyst",
            "description": "Entry-level position analyzing business systems and processes",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Business Operations Analyst",
            "description": "Entry-level position analyzing and optimizing business operations",
            "created_at": now,
            "updated_at": now
        },

        # Security & Cloud Roles
        {
            "title": "Cybersecurity Analyst Trainee",
            "description": "Entry-level cybersecurity position focusing on security analysis",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Digital Associate",
            "description": "Entry-level digital technology and transformation position",
            "created_at": now,
            "updated_at": now
        },

        # Data & Analytics Roles
        {
            "title": "Data Engineer Trainee",
            "description": "Entry-level data engineering position building data pipelines",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Data Analyst / Data Scientist – Trainee",
            "description": "Entry-level data analysis and data science position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Data Analyst",
            "description": "Entry-level position analyzing data and generating insights",
            "created_at": now,
            "updated_at": now
        },

        # AI/ML & DevOps Roles
        {
            "title": "AI/ML Trainee",
            "description": "Entry-level artificial intelligence and machine learning position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Machine Learning Engineer – Trainee",
            "description": "Entry-level ML engineering position developing machine learning models",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "DevOps Engineer Trainee",
            "description": "Entry-level DevOps position focusing on CI/CD and automation",
            "created_at": now,
            "updated_at": now
        },

        # Design Roles
        {
            "title": "UI/UX Designer – Trainee",
            "description": "Entry-level UI/UX design position focusing on user experience",
            "created_at": now,
            "updated_at": now
        },

        # Management & Leadership Roles
        {
            "title": "Management Trainee (MT)",
            "description": "Entry-level management trainee position with rotational assignments",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Program Manager – Intern",
            "description": "Entry-level program management internship position",
            "created_at": now,
            "updated_at": now
        },

        # Business Development & Sales Roles
        {
            "title": "Business Development Associate",
            "description": "Entry-level business development position focusing on growth",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Marketing Associate",
            "description": "Entry-level marketing position supporting marketing campaigns",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Sales Trainee",
            "description": "Entry-level sales position learning sales processes",
            "created_at": now,
            "updated_at": now
        },

        # HR & Finance Roles
        {
            "title": "HR Executive Trainee",
            "description": "Entry-level human resources position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Finance Analyst",
            "description": "Entry-level financial analysis position",
            "created_at": now,
            "updated_at": now
        },

        # Operations & Process Roles
        {
            "title": "Process Associate",
            "description": "Entry-level process management and execution position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Supply Chain Analyst",
            "description": "Entry-level supply chain analysis position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Strategy Analyst",
            "description": "Entry-level strategic analysis position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Product Operations Associate",
            "description": "Entry-level product operations position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Catalog Associate",
            "description": "Entry-level catalog management position",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Seller Support Associate",
            "description": "Entry-level position supporting sellers and vendors",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Web Developer",
            "description": "Entry-level web development position building websites and web applications",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Java Developer",
            "description": "Entry-level Java development position working on Java applications",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Python Developer",
            "description": "Entry-level Python development position building Python applications",
            "created_at": now,
            "updated_at": now
        },

        # New Roles - Marketing & Sales Positions
        {
            "title": "Digital Marketing Executive",
            "description": "Entry-level digital marketing position managing online marketing campaigns",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Marketing Executive",
            "description": "Entry-level marketing position supporting marketing initiatives",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Sales Engineer",
            "description": "Entry-level sales engineering position providing technical sales support",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "IT Sales",
            "description": "Entry-level IT sales position selling technology products and services",
            "created_at": now,
            "updated_at": now
        },

        # Client Services & Support Positions
        {
            "title": "Executive Client Servicing (FSF)",
            "description": "Entry-level client servicing position providing customer support",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Executive Sales and Services (Tele)",
            "description": "Entry-level telesales and service position handling customer calls",
            "created_at": now,
            "updated_at": now
        },

        # Recruitment Positions
        {
            "title": "IT Recruiter Executive",
            "description": "Entry-level IT recruitment position sourcing technical talent",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Associate Technical Recruiter",
            "description": "Entry-level technical recruitment position for IT hiring",
            "created_at": now,
            "updated_at": now
        }
    ]

    existing_roles = {
        role.title
        for role in db_session.query(AIInterviewRoles.title).all()
    }

    roles_to_add = [
        AIInterviewRoles(**role)
        for role in default_roles
        if role["title"] not in existing_roles
    ]

    if roles_to_add:
        db_session.bulk_save_objects(roles_to_add)
        db_session.commit()
        print("Default interview roles inserted.")
    else:
        print("Default interview roles already exist.")

def insert_default_target_companies(db_session: Session):
#     """Seed languages. Sets language-level preview/dubbing assets when available."""
#     now = datetime.now(timezone.utc)

#     default_languages = [
#         {"name": "English", "code": "en", "main_name": "English", "is_active": True},
#         {"name": "Hindi", "code": "hi", "main_name": "हिन्दी", "is_active": True,
#          # associate language-level video assets (using Payal assets for Hindi preview/dubb)
#          "video_blink_1": "s3://staging-mindmentor-user-uploads/ai-interview/avatars/payal-still_compress.mp4",
#          "video_blink_2": "s3://staging-mindmentor-user-uploads/ai-interview/avatars/payal-still_compress (1).mp4",
#          "video_dubb": "s3://staging-mindmentor-user-uploads/ai-interview/avatars/payal-dubb_compress.mp4"},
#         {"name": "Spanish", "code": "es", "main_name": "Español", "is_active": True},
#         {"name": "French", "code": "fr", "main_name": "Français", "is_active": True},
#         {"name": "German", "code": "de", "main_name": "Deutsch", "is_active": True},
#     ]

#     # fetch existing language codes
#     existing_codes = {row[0] for row in db_session.query(Languages.code).all()}

#     languages_to_add = []
#     for lang in default_languages:
#         if lang["code"] in existing_codes:
#             continue
#         languages_to_add.append(
#             Languages(
#                 name=lang["name"],
#                 code=lang["code"],
#                 main_name=lang.get("main_name"),
#                 is_active=lang.get("is_active", 1),
#                 video_blink_1=lang.get("video_blink_1"),
#                 video_blink_2=lang.get("video_blink_2"),
#                 video_dubb=lang.get("video_dubb"),
#                 created_at=now,
#                 updated_at=now
#             )
#         )

#     if languages_to_add:
#         try:
#             db_session.bulk_save_objects(languages_to_add)
#             db_session.commit()
#             print(f"Inserted {len(languages_to_add)} default languages.")
#         except Exception:
#             db_session.rollback()
#             raise
#     else:
#         print("Default languages already present.")

# def insert_default_avatars(db_session: Session):
#     """Seed avatars. Uses provided S3 links for Payal (Hindi avatar)."""
#     now = datetime.now(timezone.utc)

#     # Ensure we have language code -> id mapping
#     lang_objs = db_session.query(Languages).all()
#     lang_map = {lang.code: lang.id for lang in lang_objs}

#     # S3 links supplied for Payal avatar
#     payal_assets = {
#         "greet_video": "s3://staging-mindmentor-user-uploads/ai-interview/avatars/payal_greeting_compress.mp4",
#         "video_blink_1": "s3://staging-mindmentor-user-uploads/ai-interview/avatars/payal-still_compress.mp4",
#         "video_blink_2": "s3://staging-mindmentor-user-uploads/ai-interview/avatars/payal-still_compress (1).mp4",
#         "video_dubb": "s3://staging-mindmentor-user-uploads/ai-interview/avatars/payal-dubb_compress.mp4"
#     }

#     default_avatars = [
#         {"language_code": "en", "avatar_name": "Alex", "greet_video": None, "video_blink_1": None, "video_blink_2": None, "video_dubb": None, "img": "alex.png", "accent": "US"},
#         {"language_code": "en", "avatar_name": "Emma", "greet_video": None, "video_blink_1": None, "video_blink_2": None, "video_dubb": None, "img": "emma.png", "accent": "UK"},
#         {"language_code": "hi", "avatar_name": "Payal", "greet_video": payal_assets["greet_video"], "video_blink_1": payal_assets["video_blink_1"], "video_blink_2": payal_assets["video_blink_2"], "video_dubb": payal_assets["video_dubb"], "img": "payal.png", "accent": "IN"},
#     ]

#     # existing (avatar_name, language_id) pairs
#     existing_pairs = {(row[0], row[1]) for row in db_session.query(Avatars.avatar_name, Avatars.language_id).all()}

#     avatars_to_add = []
#     for av in default_avatars:
#         lang_id = lang_map.get(av["language_code"])
#         if not lang_id:
#             # skip if language not seeded
#             continue
#         pair = (av["avatar_name"], lang_id)
#         if pair in existing_pairs:
#             continue
#         avatars_to_add.append(
#             Avatars(
#                 language_id=lang_id,
#                 avatar_name=av["avatar_name"],
#                 greet_video=av.get("greet_video"),
#                 video_blink_1=av.get("video_blink_1"),
#                 video_blink_2=av.get("video_blink_2"),
#                 video_dubb=av.get("video_dubb"),
#                 img=av.get("img"),
#                 accent=av.get("accent"),
#                 created_at=now,
#                 updated_at=now
#             )
#         )

#     if avatars_to_add:
#         try:
#             db_session.bulk_save_objects(avatars_to_add)
#             db_session.commit()
#             print(f"Inserted {len(avatars_to_add)} default avatars.")
#         except Exception:
#             db_session.rollback()
#             raise
#     else:
#         print("Default avatars already present or languages missing.")

def insert_default_department_and_batch(db_session: Session):
    from models.tenant import Tenant
    from models.organization import Department, Batch
    tenant_key = os.getenv("DEFAULT_TENANT_KEY", "ace")
    tenant = db_session.query(Tenant).filter(Tenant.key == tenant_key).first()
    if not tenant:
        print("No tenant found to seed department/batch")
        return
    dept = db_session.query(Department).filter(Department.tenant_id == tenant.id, Department.name == 'General').first()
    if not dept:
        dept = Department(name='MCA', code='MCA', tenant_id=tenant.id)
        db_session.add(dept)
        db_session.commit()
    batch = db_session.query(Batch).filter(Batch.tenant_id == tenant.id, Batch.department_id == dept.id, Batch.name == '2025').first()
    if not batch:
        batch = Batch(name='2025', from_year=2025, to_year=2019, department_id=dept.id, tenant_id=tenant.id)
        db_session.add(batch)
        db_session.commit()

def insert_default_roles(db_session: Session):
    """Inserts default roles if they don't exist."""
    default_roles = ['teacher', 'student', 'superadmin', 'admin']
    
    existing_roles = {
        role.role_name
        for role in db_session.query(Role.role_name)
        .filter(Role.role_name.in_(default_roles))
        .all()
    }

    now = datetime.now(timezone.utc)

    roles_to_add = [
        Role(role_name=role_name, created_at=now, updated_at=now, is_active=True)
        for role_name in default_roles
        if role_name not in existing_roles
    ]

    if roles_to_add:
        db_session.bulk_save_objects(roles_to_add)
        db_session.commit()
        print("Default roles inserted.")
    else:
        print("Default roles already exist.")

def insert_default_superadmin(db_session: Session):
    """Inserts a default superadmin user if it doesn't exist."""
    # Read from environment variables
    superadmin_email = os.getenv("SUPERADMIN_EMAIL")
    superadmin_password = os.getenv("SUPERADMIN_PASSWORD")

    if not superadmin_email or not superadmin_password:
        raise CustomException(
            "Superadmin credentials not set in environment variables.",
            status_code=500,
        )

    now = datetime.now(timezone.utc)

    # Get default tenant
    from models.tenant import Tenant
    default_tenant = db_session.query(Tenant).filter(Tenant.key == 'ace').first()
    if not default_tenant:
        raise CustomException("Default tenant not found", status_code=500)

    # Check if superadmin user already exists
    existing_user = db_session.query(User).filter(User.phone_email == superadmin_email).first()
    if existing_user:
        print("Superadmin user already exists.")
        return

    # Create new superadmin user
    superadmin_user = User(
        first_name="Mind",
        last_name="Mentor",
        phone_email=superadmin_email,
        password=ValidationUtility.hash_password(superadmin_password),
        created_at=now,
        updated_at=now,
        is_active=True,
        tenant_id=default_tenant.id
    )
    db_session.add(superadmin_user)
    db_session.commit()

    # Assign superadmin role
    superadmin_role = db_session.query(Role).filter(Role.role_name == "superadmin").first()
    if superadmin_role:
        user_role = UserRole(
            user_id=superadmin_user.user_id,
            role_id=superadmin_role.id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db_session.add(user_role)
        db_session.commit()
        print("Superadmin user created and role assigned.")
    else:
        print("Superadmin role not found, cannot assign to user.")

def insert_default_subscription_plans(db_session: Session):
    """Insert default subscription plans for tenant and non-tenant users."""
    now = datetime.now(timezone.utc)
    
    # Check if plans already exist
    existing_plans = db_session.query(SubscriptionPlan).filter(
        SubscriptionPlan.name.in_(['Tenant Unlimited Plan', 'Free Plan'])
    ).all()
    
    if existing_plans:
        print("Default subscription plans already exist.")
        return existing_plans
    
    # Define default plans
    plans_to_create = [
        {
            'name': 'Tenant Unlimited Plan',
            'description': 'Unlimited access for tenant organizations with full feature set',
            'plan_type': 'tenant',
            'tier': 'enterprise',
            'billing_cycle': 'yearly',
            'price': 0.00,  # Custom pricing handled separately
            'currency': 'USD',
            'features': {
                'ai_quiz_generation': True,
                'unlimited_classrooms': True,
                'unlimited_invitations': True,
                'unlimited_students': True,
                'unlimited_courses': True,
                'unlimited_quizzes': True,
                'analytics_dashboard': True,
                'priority_support': True,
                'custom_branding': True
            },
            'is_active': True,
            'valid_from': now,
            'valid_until': None
        },
        {
            'name': 'Free Plan',
            'description': 'Basic plan for individual users with limited features',
            'plan_type': 'individual',
            'tier': 'free',
            'billing_cycle': 'monthly',
            'price': 0.00,
            'currency': 'USD',
            'features': {
                'ai_quiz_generation': True,
                'basic_analytics': True,
                'community_support': True
            },
            'is_active': True,
            'valid_from': now,
            'valid_until': None
        }
    ]
    
    created_plans = []
    for plan_data in plans_to_create:
        plan = SubscriptionPlan(**plan_data)
        db_session.add(plan)
        created_plans.append(plan)
    
    db_session.commit()
    print("Default subscription plans created.")
    return created_plans

def insert_default_usage_quotas(db_session: Session):
    """Insert default usage quotas for each subscription plan."""
    
    now = datetime.now(timezone.utc)
    
    # Get the created plans
    tenant_plan = db_session.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == 'Tenant Unlimited Plan'
    ).first()
    
    free_plan = db_session.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == 'Free Plan'
    ).first()
    
    if not tenant_plan or not free_plan:
        print("Subscription plans not found. Please run insert_default_subscription_plans first.")
        return
    
    # Check if quotas already exist
    existing_quotas = db_session.query(UsageQuota).filter(
        UsageQuota.plan_id.in_([tenant_plan.id, free_plan.id])
    ).all()
    
    if existing_quotas:
        print("Default usage quotas already exist.")
        return
    
    # Define quotas
    quotas_to_create = [
        {
            'plan_id': tenant_plan.id,
            # Classroom limits - Unlimited for tenants
            'number_classroom_limit': None,
            'max_students_per_classroom': None,
            'total_invites_sent': None,
            
            # Quiz limits - Unlimited
            'monthly_quiz_limit': None,
            'ai_evaluations': None,
            'max_questions_per_quiz': None,
            'max_ai_questions_per_quiz': None,
            
            # Course limits - Unlimited
            'monthly_course_limit': None,
            'max_units_per_course': None,
            
            # AI generation limits - Unlimited
            'monthly_ai_generations': None,
            'ai_tokens_per_generation': None,
            
            # Storage and bandwidth - Unlimited
            'storage_limit_gb': None,
            'monthly_bandwidth_gb': None,
            'max_file_size_mb': 500,  # Reasonable limit even for unlimited plans
            
            # User limits - Unlimited
            'active_user_limit': None,
            'teacher_limit': None,
            'student_limit': None,
            
            # Feature flags
            'is_unlimited': True,
            'allow_overage': False,
            'overage_rate_per_unit': None,
            
            # Rollover settings
            'allow_rollover': False,
            'max_rollover_percentage': 0,
            
            # Validity period
            'valid_from': now,
            'valid_until': None,
            'is_active': True
        },
        {
            'plan_id': free_plan.id,
            # Classroom limits - Restricted for free plan
            'number_classroom_limit': 4,  # classrooms total
            'max_students_per_classroom': 10,  # students per classroom
            'total_invites_sent': 40,  # invitations 
            
            # Quiz limits - Restricted
            'monthly_quiz_limit': 2,  # quizzes 
            'ai_evaluations': 40,  # AI evaluations 
            'max_questions_per_quiz': 30,  # 30 total questions per quiz
            'max_ai_questions_per_quiz': 10,  # 10 AI-generated questions per quiz
            
            # Course limits - Restricted
            'monthly_course_limit': 2,  # 2 courses per month
            'max_units_per_course': 5,  # 5 units per course
            
            # AI generation limits - Restricted
            'monthly_ai_generations': 20,  # 20 AI generations per month
            'ai_tokens_per_generation': 2000,  # 2000 tokens per AI generation
            
            # Storage and bandwidth - Restricted
            'storage_limit_gb': 1.0,  # 1 GB storage
            'monthly_bandwidth_gb': 5.0,  # 5 GB bandwidth per month
            'max_file_size_mb': 10,  # 10 MB max file size
            
            # User limits - Restricted (for individual users, these may not apply)
            'active_user_limit': 1,  # Single user account
            'teacher_limit': 1,  # Single teacher (the user themselves)
            'student_limit': 50,  # 50 students total (5 classrooms * 10 students)
            
            # Feature flags
            'is_unlimited': False,
            'allow_overage': False,  # No overage for free plan
            'overage_rate_per_unit': None,
            
            # Rollover settings
            'allow_rollover': False,  # No rollover for free plan
            'max_rollover_percentage': 0,
            
            # Validity period
            'valid_from': now,
            'valid_until': None,  # NULL means no expiration
            'is_active': True
        }
    ]
    
    # Create and add quota records
    for quota_data in quotas_to_create:
        quota = UsageQuota(**quota_data)
        db_session.add(quota)
    
    try:
        db_session.commit()
        print("Default usage quotas created successfully.")
        print(f"   - Tenant Unlimited Plan quota created (ID: {tenant_plan.id})")
        print(f"   - Free Plan quota created (ID: {free_plan.id})")
    except Exception as e:
        db_session.rollback()
        print(f"Error creating usage quotas: {str(e)}")
        raise

def insert_default_designation(db_session: Session):
    """Insert default designations if they don't exist."""

    # tenant_key = os.getenv("DEFAULT_TENANT_KEY", "ace")
    # tenant = db_session.query(Tenant).filter(Tenant.key == tenant_key).first()
    # if not tenant:
    #     print("No tenant found to seed designations")
    #     return

    default_designations = [
        "Professor",
        "Associate Professor",
        "Assistant Professor",
        "Lecturer",
        "Tutor",
        "Other"
    ]

    now = datetime.now(timezone.utc)

    for designation_name in default_designations:
        existing = (
            db_session.query(Designation)
            .filter(
                # Designation.tenant_id == tenant.id,
                Designation.name == designation_name,
            )
            .first()
        )

        if not existing:
            designation = Designation(
                name=designation_name,
                # tenant_id=tenant.id,
                created_at=now,
                updated_at=now,
            )
            db_session.add(designation)

    db_session.commit()
    print("Default designations inserted (if missing).")

def insert_default_interviewers(db_session: Session):
    """Insert default AI interviewers with voice models and video assets."""
    now = datetime.now(timezone.utc)

    default_interviewers = [
        {
            "name": "Priya Sharma",
            "voice_id": "shimmer",
            "gender": "female",
            "accent": "Indian English",
            "description": "Warm and encouraging interviewer with Indian English accent",
            "greet_video": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal_greeting_compress.mp4",
            "video_blink_1": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-still_compress+(1).mp4",
            "video_blink_2": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-still_compress.mp4",
            "video_dubb": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-dubb_compress.mp4",
            "img": "priya.png",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "name": "Sarah Johnson",
            "voice_id": "coral",
            "gender": "female",
            "accent": "US English",
            "description": "Professional interviewer with clear US English accent",
            "greet_video": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal_greeting_compress.mp4",
            "video_blink_1": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-still_compress+(1).mp4",
            "video_blink_2": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-still_compress.mp4",
            "video_dubb": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-dubb_compress.mp4",            "img": "sarah.png",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "name": "Arjun Patel",
            "voice_id": "echo",
            "gender": "male",
            "accent": "Indian English",
            "description": "Experienced technical interviewer with Indian English accent",
            "greet_video": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal_greeting_compress.mp4",
            "video_blink_1": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-still_compress+(1).mp4",
            "video_blink_2": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-still_compress.mp4",
            "video_dubb": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-dubb_compress.mp4",            "img": "arjun.png",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "name": "Michael Chen",
            "voice_id": "alloy",
            "gender": "male",
            "accent": "US English",
            "description": "Senior technical interviewer with neutral US English accent",
            "greet_video": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal_greeting_compress.mp4",
            "video_blink_1": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-still_compress+(1).mp4",
            "video_blink_2": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-still_compress.mp4",
            "video_dubb": "https://staging-mindmentor-user-uploads.s3.ap-south-1.amazonaws.com/ai-interview/avatars/payal-dubb_compress.mp4",            "img": "michael.png",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
    ]

    # Check existing interviewers by name
    existing_names = {
        interviewer.name
        for interviewer in db_session.query(AIInterviewers.name).all()
    }

    interviewers_to_add = [
        AIInterviewers(**interviewer)
        for interviewer in default_interviewers
        if interviewer["name"] not in existing_names
    ]

    if interviewers_to_add:
        try:
            db_session.bulk_save_objects(interviewers_to_add)
            db_session.commit()
            print(f"Inserted {len(interviewers_to_add)} default AI interviewers.")
        except Exception as e:
            db_session.rollback()
            print(f"Error inserting interviewers: {str(e)}")
            raise
    else:
        print("Default AI interviewers already exist.")
