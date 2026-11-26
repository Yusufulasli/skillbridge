# Şablonların view'dan beklediği değişkenler (front end ↔ back end anlaşması)

Şablonlar: `core/templates/base.html`, `core/templates/core/{index,profil,eslesmeler}.html`
Stil: `core/static/core/style.css`

## 1. URL adları (`{% url %}` bunları arar)

Şablonlar bu üç adı kullanıyor. Biri eksikse sayfa `NoReverseMatch` hatası verir.

| Ad           | Önerilen yol     | Şablon                    |
|--------------|------------------|---------------------------|
| `index`      | `/`              | `core/index.html`         |
| `profil`     | `/profil/`       | `core/profil.html`        |
| `eslesmeler` | `/eslesmeler/`   | `core/eslesmeler.html`    |

Öneri (`config/urls.py`):

```python
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("profil/", views.profil, name="profil"),
    path("eslesmeler/", views.eslesmeler, name="eslesmeler"),
]
```

Namespace (`app_name = "core"`) eklenirse şablonlarda `{% url 'core:profil' %}` gibi değişmesi gerekir; haber verin.

## 2. `index` → `core/index.html`

Context değişkeni yok.

## 3. `profil` → `core/profil.html`

| Değişken    | Tür                                | Şablonda kullanılan alanlar |
|-------------|------------------------------------|-----------------------------|
| `beceriler` | `Skill` queryset'i (ya da listesi) | `id`, `name_tr`             |

Boşsa şablon "Beceri listesi henüz yüklenmedi." yazar.

## 4. Profil formunun gönderdiği GET parametreleri

Form `GET` ile `{% url 'eslesmeler' %}` adresine gider, örneğin:
`/eslesmeler/?alan=machining&beceri=1&beceri=5&beceri=6`

| Parametre | Değer                                                   | Okuma                          |
|-----------|---------------------------------------------------------|--------------------------------|
| `alan`    | `machining` / `welding` / `automation` / `other` (`StudentProfile.Field` ile aynı) | `request.GET.get("alan")`      |
| `beceri`  | `Skill.id`, birden çok kez gelebilir                     | `request.GET.getlist("beceri")`|

Bu değerler kullanıcıdan geliyor: sayı olmayan id'ler ve olmayan alan değerleri view'da elenmeli.

## 5. `eslesmeler` → `core/eslesmeler.html`

| Değişken   | Tür                                               |
|------------|---------------------------------------------------|
| `sonuclar` | `MatchResult` listesi, **en yüksek skor başta**   |

Şablon her `sonuc` için şu alanları okur. Bunlar `core/matching.py` içindeki `MatchResult` ile birebir aynı, yani `match_profile(...)` çıktısı doğrudan verilebilir:

| Alan                         | Tür            | Şablonda ne için                                  |
|------------------------------|----------------|---------------------------------------------------|
| `sonuc.listing.firm.name`    | str            | Kart başlığı                                      |
| `sonuc.listing.type`         | str            | `internship` → Staj, `entry_level_job` → İş, `visit` → Firma ziyareti |
| `sonuc.listing.is_sample`    | bool           | Karttaki sarı "Sample data" etiketi               |
| `sonuc.listing.skills.all`   | Skill'ler      | "(3/4)" içindeki 4 (toplam istenen beceri)        |
| `sonuc.score`                | float, 0.0–1.0 | "Skor 0.75" ve ilerleme çubuğu                    |
| `sonuc.matched`              | Skill listesi  | Yeşil ✓ satırı (`name_tr`)                        |
| `sonuc.missing`              | Skill listesi  | Kırmızı ✗ satırı (`name_tr`)                      |

- `listing.skills.all` için `visible_listings()` içindeki `prefetch_related("skills")` sayesinde ek sorgu atılmaz.
- `sonuclar` boş liste ise şablon "ilan yok" mesajını ve profile dönüş butonunu gösterir.
- Sıralamayı şablon yapmaz; listeyi geldiği sırayla basar.

## 6. Örnek view taslağı (sadece öneri)

```python
from django.shortcuts import render
from .models import Skill

def index(request):
    return render(request, "core/index.html")

def profil(request):
    return render(request, "core/profil.html", {"beceriler": Skill.objects.all()})

def eslesmeler(request):
    beceri_idleri = [i for i in request.GET.getlist("beceri") if i.isdigit()]
    sonuclar = ...  # match_profile(...) ya da match_score ile aynı MatchResult listesi
    return render(request, "core/eslesmeler.html", {"sonuclar": sonuclar})
```

Açık soru: `match_profile()` kaydedilmiş bir `StudentProfile` istiyor. Her GET isteğinde
veritabanına profil yazılsın mı, yoksa eşleştirme kayıt açmadan mı yapılsın? Karar back end'in.
