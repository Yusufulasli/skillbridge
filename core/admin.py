from django.contrib import admin

from .models import (
    Firm, Listing, ListingSkill, ProfileSkill, School, SchoolSkill, Skill, StudentProfile, UsageLog,
)

admin.site.site_header = "SkillBridge Kayseri admin"


class ListingSkillInline(admin.TabularInline):
    model = ListingSkill
    extra = 1


class ProfileSkillInline(admin.TabularInline):
    model = ProfileSkill
    extra = 0


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_tr", "category", "data_source")
    list_filter = ("category", "data_source")
    search_fields = ("name_en", "name_tr")


@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = ("name", "sector", "size", "publish_consent", "data_source")
    list_filter = ("sector", "size", "publish_consent", "data_source")
    search_fields = ("name",)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "firm", "type", "is_active", "data_source")
    list_filter = ("type", "is_active", "data_source")
    search_fields = ("title", "firm__name")
    inlines = [ListingSkillInline]


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "data_source")
    list_filter = ("data_source",)


@admin.register(SchoolSkill)
class SchoolSkillAdmin(admin.ModelAdmin):
    list_display = ("school", "skill", "taught", "workshop_ready", "reviewed_with_teacher", "data_source")
    list_filter = ("taught", "workshop_ready", "reviewed_with_teacher", "data_source", "school")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "field_of_study", "created_at")
    inlines = [ProfileSkillInline]


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ("event", "timestamp")
    list_filter = ("event",)
