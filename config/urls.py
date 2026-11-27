from django.contrib import admin
from django.urls import path

from core import views

# No app_name / namespace: the templates use plain names, e.g. {% url 'eslesmeler' %}.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("profil/", views.profil, name="profil"),
    path("eslesmeler/", views.eslesmeler, name="eslesmeler"),
]
