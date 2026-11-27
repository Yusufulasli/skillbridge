import re

from django.shortcuts import render
from django.views.decorators.http import require_safe

from .matching import match_skills
from .models import Skill, StudentProfile, UsageLog

# Valid values for the "alan" (field of study) parameter, taken from the model so they cannot drift apart.
VALID_ALAN = {value for value, _label in StudentProfile.Field.choices}

# Only plain ASCII digits, at most 9 of them (keeps ids inside the database integer range).
_ID_PATTERN = re.compile(r"[0-9]{1,9}")


def _template(name):
    """Try core/templates/core/<name> first, then core/templates/<name>, so both layouts work."""
    return [f"core/{name}", name]


def _clean_skill_ids(raw_values):
    """Keep only well-formed ids that exist in the Skill table. Everything else is dropped silently."""
    wanted = {int(v) for v in (r.strip() for r in raw_values) if _ID_PATTERN.fullmatch(v)}
    return set(Skill.objects.filter(id__in=wanted).values_list("id", flat=True))


@require_safe
def index(request):
    return render(request, _template("index.html"))


@require_safe
def profil(request):
    return render(request, _template("profil.html"), {"beceriler": Skill.objects.all()})


@require_safe
def eslesmeler(request):
    alan = request.GET.get("alan", "")
    if alan not in VALID_ALAN:
        alan = ""
    skill_ids = _clean_skill_ids(request.GET.getlist("beceri"))

    # No StudentProfile is created: matching works directly on the chosen skill ids.
    sonuclar = match_skills(skill_ids)

    # Anonymous usage log: only the event name and the time (no user, IP, browser or chosen skills).
    UsageLog.objects.create(event=UsageLog.Event.RUN_MATCH)

    context = {
        "sonuclar": sonuclar,
        "alan": alan,
        "secilen_beceriler": Skill.objects.filter(id__in=skill_ids),
    }
    return render(request, _template("eslesmeler.html"), context)
