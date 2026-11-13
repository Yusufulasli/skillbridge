"""Create clearly labelled SAMPLE data for development. Safe to run more than once.

Usage: python manage.py load_sample_data
All records are created with data_source='sample'. Real firm data is entered only after interviews.
"""
from django.core.management.base import BaseCommand

from core.models import DataSource, Firm, Listing, ListingSkill, School, SchoolSkill, Skill

SKILLS = [
    ("Teknik resim okuma", "Reading technical drawings", "technical_drawing"),
    ("CNC tezgâh ayarı", "CNC machine setup", "machining"),
    ("G-kod okuma", "Reading G-code", "machining"),
    ("TIG kaynağı", "TIG welding", "welding"),
    ("Kumpas / mikrometre ile ölçme", "Measuring with caliper / micrometer", "machining"),
    ("İş güvenliği sertifikası", "Workplace safety certificate", "other"),
]

LISTINGS = [
    ("Sample Firm A", "Sample internship A", "internship",
     ["Reading technical drawings", "Measuring with caliper / micrometer",
      "Workplace safety certificate", "CNC machine setup"]),
    ("Sample Firm B", "Sample entry-level job B", "entry_level_job",
     ["Reading technical drawings", "Measuring with caliper / micrometer",
      "Reading G-code", "TIG welding"]),
]

TAUGHT = {"Reading technical drawings": True, "Measuring with caliper / micrometer": True,
          "Workplace safety certificate": True, "CNC machine setup": True,
          "Reading G-code": False, "TIG welding": False}


class Command(BaseCommand):
    help = "Load labelled sample data (data_source='sample')."

    def handle(self, *args, **options):
        S = DataSource.SAMPLE
        skills = {}
        for tr, en, cat in SKILLS:
            skills[en], _ = Skill.objects.get_or_create(
                name_en=en, defaults={"name_tr": tr, "category": cat, "data_source": S})
        for firm_name, title, type_, skill_names in LISTINGS:
            firm, _ = Firm.objects.get_or_create(
                name=firm_name, defaults={"data_source": S, "publish_consent": True})
            listing, _ = Listing.objects.get_or_create(
                firm=firm, title=title, defaults={"type": type_, "data_source": S})
            for name in skill_names:
                ListingSkill.objects.get_or_create(listing=listing, skill=skills[name])
        school, _ = School.objects.get_or_create(name="Sample Vocational School", defaults={"data_source": S})
        for name, taught in TAUGHT.items():
            SchoolSkill.objects.get_or_create(
                school=school, skill=skills[name], defaults={"taught": taught, "data_source": S})
        self.stdout.write(self.style.SUCCESS("Sample data loaded (all records marked 'sample')."))
