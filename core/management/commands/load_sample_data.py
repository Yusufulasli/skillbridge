"""Create clearly labelled SAMPLE data for development. Safe to run more than once.

Usage: python manage.py load_sample_data
All records are created with data_source='sample'. Real firm data is entered only after interviews.
Older sample records (English names) are renamed instead of duplicated.
"""
from django.core.management.base import BaseCommand

from core.models import DataSource, Firm, Listing, ListingSkill, School, SchoolSkill, Skill

S = DataSource.SAMPLE

SKILLS = [
    ("Teknik resim okuma", "Reading technical drawings", "technical_drawing"),
    ("CNC tezgâh ayarı", "CNC machine setup", "machining"),
    ("G-kod okuma", "Reading G-code", "machining"),
    ("TIG kaynağı", "TIG welding", "welding"),
    ("Kumpas / mikrometre ile ölçme", "Measuring with caliper / micrometer", "machining"),
    ("İş güvenliği sertifikası", "Workplace safety certificate", "other"),
    ("Kalite kontrol", "Quality control", "other"),
]

LISTINGS = [
    ("Örnek Firma A", "Örnek staj ilanı A", "internship",
     ["Reading technical drawings", "Measuring with caliper / micrometer",
      "Workplace safety certificate", "CNC machine setup"]),
    ("Örnek Firma B", "Örnek iş ilanı B", "entry_level_job",
     ["Reading technical drawings", "Measuring with caliper / micrometer",
      "Reading G-code", "TIG welding"]),
    ("Örnek Firma C", "Örnek firma ziyareti C", "visit",
     ["Reading technical drawings", "Quality control", "Measuring with caliper / micrometer"]),
]

SCHOOL_NAME = "Örnek Meslek Lisesi"

TAUGHT = {"Reading technical drawings": True, "Measuring with caliper / micrometer": True,
          "Workplace safety certificate": True, "CNC machine setup": True,
          "Reading G-code": False, "TIG welding": False, "Quality control": False}

# Names used by the first version of this command -> new names (sample records only).
RENAME_FIRMS = {"Sample Firm A": "Örnek Firma A", "Sample Firm B": "Örnek Firma B"}
RENAME_LISTINGS = {"Sample internship A": "Örnek staj ilanı A", "Sample entry-level job B": "Örnek iş ilanı B"}
RENAME_SCHOOLS = {"Sample Vocational School": SCHOOL_NAME}


def _rename(model, field, mapping):
    for old, new in mapping.items():
        if not model.objects.filter(**{field: new}, data_source=S).exists():
            model.objects.filter(**{field: old}, data_source=S).update(**{field: new})


class Command(BaseCommand):
    help = "Load labelled sample data (data_source='sample'). Can be run many times."

    def handle(self, *args, **options):
        _rename(Firm, "name", RENAME_FIRMS)
        _rename(Listing, "title", RENAME_LISTINGS)
        _rename(School, "name", RENAME_SCHOOLS)

        skills = {}
        for tr, en, cat in SKILLS:
            skills[en], _ = Skill.objects.get_or_create(
                name_en=en, data_source=S, defaults={"name_tr": tr, "category": cat})

        for firm_name, title, type_, skill_names in LISTINGS:
            firm, _ = Firm.objects.get_or_create(
                name=firm_name, data_source=S, defaults={"publish_consent": True})
            listing, _ = Listing.objects.get_or_create(
                firm=firm, title=title, data_source=S, defaults={"type": type_})
            for name in skill_names:
                ListingSkill.objects.get_or_create(listing=listing, skill=skills[name])

        school, _ = School.objects.get_or_create(name=SCHOOL_NAME, data_source=S)
        for name, taught in TAUGHT.items():
            SchoolSkill.objects.get_or_create(
                school=school, skill=skills[name], data_source=S, defaults={"taught": taught})

        self.stdout.write(self.style.SUCCESS("Sample data loaded (all records marked 'sample')."))
