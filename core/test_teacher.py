"""Tests for the teacher page (most wanted skills and the gap between industry and school)."""
from django.test import TestCase
from django.urls import reverse

from .matching import teacher_dashboard
from .models import DataSource, Firm, Listing, ListingSkill, School, SchoolSkill, Skill, UsageLog

REAL, SAMPLE = DataSource.REAL, DataSource.SAMPLE


def skill(n, source=REAL):
    return Skill.objects.create(name_tr=f"b{n}", name_en=f"skill{n}", data_source=source)


def listing(firm, skills, title="L", source=REAL, active=True):
    obj = Listing.objects.create(firm=firm, title=title, data_source=source, is_active=active)
    for s in skills:
        ListingSkill.objects.create(listing=obj, skill=s)
    return obj


class TeacherPageTests(TestCase):
    def setUp(self):
        self.s = [skill(i) for i in range(4)]
        self.f1 = Firm.objects.create(name="F1", data_source=REAL, publish_consent=True)
        self.f2 = Firm.objects.create(name="F2", data_source=REAL, publish_consent=True)

    def test_url_and_empty_database_returns_200(self):
        Skill.objects.all().delete()
        self.assertEqual(reverse("ogretmen"), "/ogretmen/")
        response = self.client.get(reverse("ogretmen"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["panel"].rows, [])

    def test_rows_count_distinct_firms_and_show_school_status(self):
        listing(self.f1, [self.s[0], self.s[1]], "a")
        listing(self.f1, [self.s[0]], "b")          # same firm, same skill: counted once
        listing(self.f2, [self.s[0], self.s[2]], "c")
        school = School.objects.create(name="School", data_source=REAL)
        SchoolSkill.objects.create(school=school, skill=self.s[0], taught=True, data_source=REAL)
        SchoolSkill.objects.create(school=school, skill=self.s[1], taught=False, data_source=REAL)
        panel = self.client.get(reverse("ogretmen")).context["panel"]
        rows = {r.skill.name_en: (r.firm_count, r.taught) for r in panel.rows}
        self.assertEqual(rows["skill0"], (2, True))
        self.assertEqual(rows["skill1"], (1, False))
        self.assertEqual(rows["skill2"], (1, None))      # school not reviewed yet
        self.assertEqual(panel.rows[0].skill.name_en, "skill0")   # most wanted first
        self.assertEqual((panel.firm_count, panel.gap_count, panel.is_sample), (2, 1, False))

    def test_no_consent_and_inactive_listings_are_left_out(self):
        nc = Firm.objects.create(name="N", data_source=REAL, publish_consent=False)
        listing(nc, [self.s[3]], "hidden")
        listing(self.f1, [self.s[3]], "inactive", active=False)
        self.assertEqual(teacher_dashboard().rows, [])

    def test_sample_data_is_shown_only_when_there_is_no_real_data(self):
        sf = Firm.objects.create(name="S", data_source=SAMPLE, publish_consent=True)
        listing(sf, [self.s[0]], "sample", source=SAMPLE)
        panel = teacher_dashboard()
        self.assertTrue(panel.is_sample)
        self.assertEqual(len(panel.rows), 1)
        listing(self.f1, [self.s[1]], "real")           # real data appears -> sample is hidden
        panel = teacher_dashboard()
        self.assertFalse(panel.is_sample)
        self.assertEqual([r.skill.name_en for r in panel.rows], ["skill1"])

    def test_sample_label_is_in_the_page_when_sample_is_shown(self):
        sf = Firm.objects.create(name="S", data_source=SAMPLE, publish_consent=True)
        listing(sf, [self.s[0]], "sample", source=SAMPLE)
        self.assertContains(self.client.get(reverse("ogretmen")), "Sample data")

    def test_visit_is_logged_without_personal_data(self):
        self.client.get(reverse("ogretmen"), REMOTE_ADDR="10.9.8.7", HTTP_USER_AGENT="X")
        self.assertEqual(list(UsageLog.objects.values_list("event", flat=True)), [UsageLog.Event.VIEW_DASHBOARD])

    def test_post_is_not_allowed(self):
        self.assertEqual(self.client.post(reverse("ogretmen")).status_code, 405)
