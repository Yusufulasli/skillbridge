"""SkillBridge Kayseri data model (see docs/week1/database-plan.md).

Design rules:
- One shared Skill list used by firms, schools and students.
- Every content table has data_source = real / sample.
- No personal student data and no IP addresses are stored.
"""
import uuid

from django.db import models


class DataSource(models.TextChoices):
    REAL = "real", "Real"
    SAMPLE = "sample", "Sample"


class SourceModel(models.Model):
    """Abstract base: marks every record as real or sample data."""

    data_source = models.CharField(
        max_length=10, choices=DataSource.choices, default=DataSource.SAMPLE
    )

    class Meta:
        abstract = True

    @property
    def is_sample(self):
        return self.data_source == DataSource.SAMPLE


class Skill(SourceModel):
    class Category(models.TextChoices):
        MACHINING = "machining", "Machining"
        WELDING = "welding", "Welding"
        AUTOMATION = "automation", "Automation"
        TECHNICAL_DRAWING = "technical_drawing", "Technical drawing"
        MAINTENANCE = "maintenance", "Maintenance"
        ASSEMBLY = "assembly", "Assembly"
        OTHER = "other", "Other"

    name_tr = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["category", "name_en"]

    def __str__(self):
        return self.name_en


class Firm(SourceModel):
    class Sector(models.TextChoices):
        METAL_PRODUCTS = "metal_products", "Metal products"
        MACHINERY = "machinery", "Machinery"
        AUTOMOTIVE_PARTS = "automotive_parts", "Automotive parts"
        CASTING = "casting", "Casting"
        OTHER = "other", "Other"

    class Size(models.TextChoices):
        SMALL = "small", "Small"
        MEDIUM = "medium", "Medium"

    name = models.CharField(max_length=160, help_text="Use a label like 'Firm A' if the firm does not want its name shown.")
    sector = models.CharField(max_length=30, choices=Sector.choices, default=Sector.OTHER)
    size = models.CharField(max_length=10, choices=Size.choices, default=Size.SMALL)
    publish_consent = models.BooleanField(
        default=False, help_text="The firm agreed that its skill list may be shown. Required for real firms."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Listing(SourceModel):
    class Type(models.TextChoices):
        INTERNSHIP = "internship", "Internship"
        ENTRY_LEVEL_JOB = "entry_level_job", "Entry-level job"
        VISIT = "visit", "Firm visit"

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=160)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.INTERNSHIP)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    skills = models.ManyToManyField(Skill, through="ListingSkill", related_name="listings")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.title} ({self.firm})"


class ListingSkill(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["listing", "skill"], name="unique_listing_skill")]

    def __str__(self):
        return f"{self.listing_id}:{self.skill_id}"


class School(SourceModel):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SchoolSkill(SourceModel):
    """Skill map: is a skill taught at this school or not?"""

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="school_skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="school_skills")
    taught = models.BooleanField(default=False)
    where_taught = models.CharField(max_length=160, blank=True, help_text="Course or workshop name")
    workshop_ready = models.BooleanField(default=False, help_text="Does the workshop have the needed machine?")
    reviewed_with_teacher = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["school", "skill"], name="unique_school_skill")]

    def __str__(self):
        return f"{self.school} - {self.skill} ({'taught' if self.taught else 'not taught'})"


class StudentProfile(models.Model):
    """Anonymous profile: random code + field of study + skills. No personal data."""

    class Field(models.TextChoices):
        MACHINING = "machining", "Machining"
        WELDING = "welding", "Welding"
        AUTOMATION = "automation", "Automation"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field_of_study = models.CharField(max_length=20, choices=Field.choices, default=Field.OTHER)
    created_at = models.DateTimeField(auto_now_add=True)
    skills = models.ManyToManyField(Skill, through="ProfileSkill", related_name="profiles")

    def __str__(self):
        return str(self.id)


class ProfileSkill(models.Model):
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "skill"], name="unique_profile_skill")]


class UsageLog(models.Model):
    """Anonymized usage log: no user id, no IP address, no user agent."""

    class Event(models.TextChoices):
        VIEW_STUDENT_PAGE = "view_student_page", "View student page"
        VIEW_DASHBOARD = "view_dashboard", "View teacher dashboard"
        RUN_MATCH = "run_match", "Run match"
        VIEW_FIRM_FORM = "view_firm_form", "View firm form"

    event = models.CharField(max_length=30, choices=Event.choices)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
