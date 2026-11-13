from django.test import TestCase

from .matching import curriculum_gap, match_profile, match_score, most_wanted_skills
from .models import (
    DataSource, Firm, Listing, ListingSkill, ProfileSkill, School, SchoolSkill, Skill, StudentProfile,
)

REAL, SAMPLE = DataSource.REAL, DataSource.SAMPLE


def make_skills(n, source=REAL):
    return [Skill.objects.create(name_tr=f"s{i}", name_en=f"skill{i}", data_source=source) for i in range(n)]


def make_listing(firm, skills, source=REAL, title="L", active=True):
    listing = Listing.objects.create(firm=firm, title=title, data_source=source, is_active=active)
    for s in skills:
        ListingSkill.objects.create(listing=listing, skill=s)
    return listing


def make_profile(skills):
    p = StudentProfile.objects.create()
    for s in skills:
        ProfileSkill.objects.create(profile=p, skill=s)
    return p


class MatchScoreTests(TestCase):
    def test_form_example_four_needed_two_owned(self):
        score, matched, missing = match_score({1, 2}, {1, 2, 3, 4})
        self.assertEqual(score, 0.5)
        self.assertEqual(matched, {1, 2})
        self.assertEqual(missing, {3, 4})

    def test_empty_listing_returns_none(self):
        self.assertIsNone(match_score({1}, set()))

    def test_full_and_zero_match(self):
        self.assertEqual(match_score({1, 2}, {1, 2})[0], 1.0)
        self.assertEqual(match_score(set(), {1, 2})[0], 0.0)


class MatchProfileTests(TestCase):
    def setUp(self):
        self.s = make_skills(5)
        self.firm = Firm.objects.create(name="F", data_source=REAL, publish_consent=True)

    def test_ranking_by_score_then_matched_count_then_newest(self):
        a = make_listing(self.firm, self.s[:2], title="A")        # 1/2 = 0.5, 1 matched
        b = make_listing(self.firm, self.s[:4], title="B")        # 2/4 = 0.5, 2 matched
        c = make_listing(self.firm, self.s[:1], title="C")        # 1/1 = 1.0
        profile = make_profile([self.s[0], self.s[1]][:1] + [self.s[3]])
        # profile owns s0 and s3
        results = match_profile(profile)
        self.assertEqual([r.listing.title for r in results], ["C", "B", "A"])
        self.assertEqual([r.score for r in results], [1.0, 0.5, 0.5])

    def test_missing_skills_are_reported(self):
        make_listing(self.firm, self.s[:4])
        result = match_profile(make_profile(self.s[:2]))[0]
        self.assertEqual(len(result.missing), 2)

    def test_real_listing_needs_consent_and_inactive_hidden(self):
        no_consent = Firm.objects.create(name="X", data_source=REAL, publish_consent=False)
        make_listing(no_consent, self.s[:1], title="hidden-consent")
        make_listing(self.firm, self.s[:1], title="hidden-inactive", active=False)
        make_listing(self.firm, self.s[:1], title="shown")
        titles = [r.listing.title for r in match_profile(make_profile(self.s[:1]))]
        self.assertEqual(titles, ["shown"])

    def test_listing_without_skills_not_shown(self):
        make_listing(self.firm, [], title="empty")
        self.assertEqual(match_profile(make_profile(self.s[:1])), [])


class DashboardTests(TestCase):
    def setUp(self):
        self.s = make_skills(3)
        self.f1 = Firm.objects.create(name="F1", data_source=REAL, publish_consent=True)
        self.f2 = Firm.objects.create(name="F2", data_source=REAL, publish_consent=True)

    def test_counts_distinct_firms_not_listings(self):
        make_listing(self.f1, [self.s[0]], title="a")
        make_listing(self.f1, [self.s[0]], title="b")  # same firm, same skill
        make_listing(self.f2, [self.s[0], self.s[1]], title="c")
        ranking = {s.name_en: s.firm_count for s in most_wanted_skills()}
        self.assertEqual(ranking["skill0"], 2)
        self.assertEqual(ranking["skill1"], 1)

    def test_sample_and_no_consent_excluded(self):
        sample_firm = Firm.objects.create(name="S", data_source=SAMPLE, publish_consent=True)
        make_listing(sample_firm, [self.s[2]], source=SAMPLE)
        nc = Firm.objects.create(name="N", data_source=REAL, publish_consent=False)
        make_listing(nc, [self.s[2]])
        self.assertEqual(list(most_wanted_skills()), [])

    def test_curriculum_gap(self):
        make_listing(self.f1, [self.s[0], self.s[1]])
        school = School.objects.create(name="School", data_source=REAL)
        SchoolSkill.objects.create(school=school, skill=self.s[0], taught=True, data_source=REAL)
        SchoolSkill.objects.create(school=school, skill=self.s[1], taught=False, data_source=REAL)
        self.assertEqual([s.name_en for s in curriculum_gap(school)], ["skill1"])
