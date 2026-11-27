"""Tests for the page views, the shared matching function and the sample data command."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .matching import match_profile, match_skills
from .models import (
    DataSource, Firm, Listing, ListingSkill, ProfileSkill, School, Skill, StudentProfile, UsageLog,
)

REAL, SAMPLE = DataSource.REAL, DataSource.SAMPLE


def make_skills(n, source=REAL):
    return [Skill.objects.create(name_tr=f"b{i}", name_en=f"skill{i}", data_source=source) for i in range(n)]


def make_listing(firm, skills, title, source=REAL, active=True, type_=Listing.Type.INTERNSHIP):
    listing = Listing.objects.create(firm=firm, title=title, data_source=source, is_active=active, type=type_)
    for s in skills:
        ListingSkill.objects.create(listing=listing, skill=s)
    return listing


class PageTests(TestCase):
    def setUp(self):
        self.skills = make_skills(5)
        self.firm = Firm.objects.create(name="F", data_source=REAL, publish_consent=True)

    def test_three_pages_return_200(self):
        for name in ("index", "profil", "eslesmeler"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_url_paths(self):
        self.assertEqual(reverse("index"), "/")
        self.assertEqual(reverse("profil"), "/profil/")
        self.assertEqual(reverse("eslesmeler"), "/eslesmeler/")

    def test_profil_gets_all_skills(self):
        response = self.client.get(reverse("profil"))
        self.assertEqual(set(response.context["beceriler"]), set(self.skills))

    def test_post_is_not_allowed(self):
        self.assertEqual(self.client.post(reverse("eslesmeler")).status_code, 405)

    def test_invalid_ids_and_field_do_not_raise(self):
        junk = ["abc", "-1", "1.5", "", " ", "99999999999999999999", "²", "0", "999999", "1; DROP TABLE"]
        response = self.client.get(reverse("eslesmeler"), {"alan": "zzz", "beceri": junk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["alan"], "")
        self.assertEqual(list(response.context["secilen_beceriler"]), [])

    def test_valid_ids_survive_among_junk_and_valid_field_is_kept(self):
        make_listing(self.firm, self.skills[:2], "A")
        response = self.client.get(
            reverse("eslesmeler"),
            {"alan": "machining", "beceri": [str(self.skills[0].id), "abc", "999999"]},
        )
        self.assertEqual(response.context["alan"], "machining")
        self.assertEqual(list(response.context["secilen_beceriler"]), [self.skills[0]])
        self.assertEqual(response.context["sonuclar"][0].score, 0.5)

    def test_results_come_in_the_right_order(self):
        s = self.skills
        make_listing(self.firm, s[:2], "A")   # student owns s0, s3 -> 1/2, 1 matched
        make_listing(self.firm, s[:4], "B")   # 2/4, 2 matched
        make_listing(self.firm, s[:1], "C")   # 1/1
        response = self.client.get(reverse("eslesmeler"), {"beceri": [s[0].id, s[3].id]})
        results = response.context["sonuclar"]
        self.assertEqual([r.listing.title for r in results], ["C", "B", "A"])
        self.assertEqual([r.score for r in results], [1.0, 0.5, 0.5])
        self.assertEqual((results[1].matched_count, results[1].required_count), (2, 4))

    def test_hidden_listings_are_not_shown(self):
        no_consent = Firm.objects.create(name="X", data_source=REAL, publish_consent=False)
        make_listing(no_consent, self.skills[:1], "no-consent")
        make_listing(self.firm, self.skills[:1], "inactive", active=False)
        make_listing(self.firm, [], "no-skills")
        make_listing(self.firm, self.skills[:1], "shown")
        response = self.client.get(reverse("eslesmeler"), {"beceri": [self.skills[0].id]})
        self.assertEqual([r.listing.title for r in response.context["sonuclar"]], ["shown"])

    def test_no_student_profile_is_created(self):
        make_listing(self.firm, self.skills[:2], "A")
        before = (StudentProfile.objects.count(), ProfileSkill.objects.count())
        self.client.get(reverse("eslesmeler"), {"alan": "machining", "beceri": [self.skills[0].id]})
        self.client.get(reverse("profil"))
        self.assertEqual((StudentProfile.objects.count(), ProfileSkill.objects.count()), before)
        self.assertEqual(before, (0, 0))

    def test_run_match_is_logged_without_personal_data(self):
        self.client.get(reverse("eslesmeler"), {"beceri": [self.skills[0].id]}, REMOTE_ADDR="10.1.2.3",
                        HTTP_USER_AGENT="TestBrowser")
        self.client.get(reverse("eslesmeler"))
        logs = UsageLog.objects.all()
        self.assertEqual(logs.count(), 2)
        self.assertTrue(all(log.event == UsageLog.Event.RUN_MATCH for log in logs))
        # The table has nothing that could hold a user, an IP address, a browser or chosen skills.
        self.assertEqual({f.name for f in UsageLog._meta.get_fields()}, {"id", "event", "timestamp"})

    def test_other_pages_are_not_logged_as_matches(self):
        self.client.get(reverse("index"))
        self.client.get(reverse("profil"))
        self.assertEqual(UsageLog.objects.count(), 0)


class SharedMatchingTests(TestCase):
    def test_match_skills_and_match_profile_give_the_same_result(self):
        s = make_skills(5)
        firm = Firm.objects.create(name="F", data_source=REAL, publish_consent=True)
        sample_firm = Firm.objects.create(name="S", data_source=SAMPLE, publish_consent=False)
        make_listing(firm, s[:2], "A")
        make_listing(firm, s[:4], "B")
        make_listing(firm, s[:1], "C")
        make_listing(sample_firm, s[1:3], "D", source=SAMPLE)
        profile = StudentProfile.objects.create()
        for skill in (s[0], s[3]):
            ProfileSkill.objects.create(profile=profile, skill=skill)

        def summary(results):
            return [(r.listing.id, r.score, [x.id for x in r.matched], [x.id for x in r.missing]) for r in results]

        self.assertEqual(summary(match_skills([s[0].id, s[3].id])), summary(match_profile(profile)))
        self.assertEqual(len(StudentProfile.objects.all()), 1)  # match_skills created nothing

    def test_match_skills_with_no_skills_scores_zero(self):
        s = make_skills(2)
        firm = Firm.objects.create(name="F", data_source=REAL, publish_consent=True)
        make_listing(firm, s, "A")
        self.assertEqual([r.score for r in match_skills([])], [0.0])


class ModelFieldTests(TestCase):
    def test_listing_is_sample_and_visit_type(self):
        firm = Firm.objects.create(name="F", data_source=SAMPLE)
        listing = make_listing(firm, [], "V", source=SAMPLE, type_=Listing.Type.VISIT)
        self.assertTrue(listing.is_sample)
        self.assertEqual(listing.type, "visit")
        self.assertEqual(listing.get_type_display(), "Firma ziyareti")
        listing.data_source = REAL
        self.assertFalse(listing.is_sample)


class SampleDataCommandTests(TestCase):
    def run_command(self):
        call_command("load_sample_data", stdout=StringIO())

    def counts(self):
        return tuple(m.objects.count() for m in (Skill, Firm, Listing, ListingSkill, School))

    def test_running_twice_adds_nothing_new(self):
        self.run_command()
        first = self.counts()
        self.run_command()
        self.assertEqual(self.counts(), first)

    def test_content_is_labelled_sample_and_has_quality_control_and_visit(self):
        self.run_command()
        for model in (Skill, Firm, Listing, School):
            self.assertFalse(model.objects.exclude(data_source=SAMPLE).exists(), model.__name__)
        self.assertTrue(Skill.objects.filter(name_tr="Kalite kontrol", data_source=SAMPLE).exists())
        self.assertTrue(Listing.objects.filter(type=Listing.Type.VISIT).exists())
        names = set(Firm.objects.values_list("name", flat=True))
        self.assertEqual(names, {"Örnek Firma A", "Örnek Firma B", "Örnek Firma C"})

    def test_old_english_sample_records_are_renamed_not_duplicated(self):
        old = Firm.objects.create(name="Sample Firm A", data_source=SAMPLE, publish_consent=True)
        Listing.objects.create(firm=old, title="Sample internship A", data_source=SAMPLE)
        School.objects.create(name="Sample Vocational School", data_source=SAMPLE)
        self.run_command()
        self.run_command()
        self.assertFalse(Firm.objects.filter(name__startswith="Sample").exists())
        self.assertEqual(Firm.objects.filter(name="Örnek Firma A").count(), 1)
        self.assertEqual(Listing.objects.filter(firm__name="Örnek Firma A").count(), 1)
        self.assertEqual(School.objects.count(), 1)
