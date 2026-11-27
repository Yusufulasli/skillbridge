"""Matching rule and teacher-dashboard queries (see docs/week1/database-plan.md, sections 4 and 5)."""
from dataclasses import dataclass

from django.db.models import Count, Q

from .models import DataSource, Listing, SchoolSkill, Skill


def match_score(profile_skill_ids, listing_skill_ids):
    """score = |required ∩ student| / |required|.

    Returns (score, matched_ids, missing_ids), or None if the listing has no required skills.
    """
    profile_skill_ids = set(profile_skill_ids)
    listing_skill_ids = set(listing_skill_ids)
    if not listing_skill_ids:
        return None
    matched = listing_skill_ids & profile_skill_ids
    missing = listing_skill_ids - profile_skill_ids
    return len(matched) / len(listing_skill_ids), matched, missing


@dataclass
class MatchResult:
    listing: Listing
    score: float
    matched: list
    missing: list

    @property
    def matched_count(self):
        return len(self.matched)

    @property
    def required_count(self):
        return len(self.matched) + len(self.missing)


def visible_listings():
    """Active listings. Real listings need the firm's publish consent; sample listings are always allowed
    (templates must show the 'Sample data' label for them)."""
    return (
        Listing.objects.filter(is_active=True)
        .filter(Q(data_source=DataSource.SAMPLE) | Q(firm__publish_consent=True))
        .select_related("firm")
        .prefetch_related("skills")
    )


def match_skills(skill_ids):
    """Rank visible listings for a set of skill ids. Nothing is read from or written to a student profile.

    Order: highest score, then more matched skills, then newest listing.
    """
    student_ids = set(skill_ids)
    results = []
    for listing in visible_listings():
        skills = {s.id: s for s in listing.skills.all()}
        outcome = match_score(student_ids, skills.keys())
        if outcome is None:
            continue
        score, matched, missing = outcome
        results.append(
            MatchResult(
                listing=listing,
                score=score,
                matched=sorted((skills[i] for i in matched), key=lambda s: s.name_en),
                missing=sorted((skills[i] for i in missing), key=lambda s: s.name_en),
            )
        )
    results.sort(key=lambda r: (-r.score, -len(r.matched), -r.listing.id))
    return results


def match_profile(profile):
    """Same ranking for a saved StudentProfile (uses match_skills, so both paths always agree)."""
    return match_skills(profile.skills.values_list("id", flat=True))


def most_wanted_skills():
    """Skills ranked by the number of DISTINCT real firms (with consent) whose active listings require them."""
    return (
        Skill.objects.filter(
            listings__is_active=True,
            listings__data_source=DataSource.REAL,
            listings__firm__data_source=DataSource.REAL,
            listings__firm__publish_consent=True,
        )
        .annotate(firm_count=Count("listings__firm", distinct=True))
        .order_by("-firm_count", "name_en")
    )


def curriculum_gap(school):
    """Skills wanted by at least one real firm that the school does not teach (or has no row for)."""
    taught_ids = SchoolSkill.objects.filter(
        school=school, taught=True, data_source=DataSource.REAL
    ).values_list("skill_id", flat=True)
    return most_wanted_skills().exclude(id__in=taught_ids)
