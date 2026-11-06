# SkillBridge Kayseri

**Connecting vocational high schools with local industry**

GLB300 · Section 7 · Group 3 · Primary SDG: **SDG 4 (Quality Education), Target 4.4**

## The problem

Vocational high school students in Kayseri do not have clear, up-to-date information about which technical skills local factories need, and there is no simple channel that connects them with these firms. According to İŞKUR's 2024 Kayseri Labour Market Survey, most open jobs are in manufacturing, and many workplaces have difficulty finding workers with the right vocational skills.

## Our solution

SkillBridge Kayseri is a simple website:

- **Firms** list the technical skills they need for entry-level jobs and internships.
- **Students** create a skill profile and see which opportunities match them best and which skills they are still missing.
- **Teachers** use a "most wanted skills" dashboard to compare what local industry asks for with what the school teaches.

### How the matching works

For each listing, the website checks how many of the required skills the student has.

```
score = number of required skills the student has / number of required skills
```

Example: a firm wants 4 skills and the student has 2 → score = 0.5, and the student sees the 2 missing skills.

## Data rules

- Every record is marked as **real** (from a firm interview) or **sample** data.
- Sample data is always labelled "Sample data" on the pages where it appears.
- In the pilot we do **not** collect personal data from students.
- If students under 18 take part, we first get consent from the students, their parents and the school, and follow Turkey's Personal Data Protection Law (KVKK).
- This repository contains no real firm contact details or non-anonymized interview notes.

## Tech stack

- Python, Django
- SQLite (pilot)
- GitHub for code and progress records
- Free hosting service for the live version
- Google Forms for surveys

## Project structure

```
skillbridge-kayseri/
├── README.md
├── docs/
│   └── week1/
│       ├── database-plan.md
│       ├── screen-sketches/
│       └── contact-list.md
├── .gitignore
└── LICENSE
```

The Django code will be added from Week 2.

## Team

| Name | Discipline | Main role |
|---|---|---|
| Yusuf Ulaşlı | Computer Engineering | Back end: database, matching rule, data protection |
| Ahmet Safa Açıköz | Computer Engineering | Front end: interface, skills dashboard, testing; group representative |
| Necati Batuhan Oktay | Economics | Labour-market data, cost analysis, surveys and indicators |
| Esranur Tecik | Mechanical Engineering | Industry side: firm interviews, list of skills firms need |
| Edip Emir Altunay | Mechanical Engineering | School side: curriculum and workshop review, skill map |

## Progress

| Week | Status |
|---|---|
| 1 | Repository, database plan, screen sketches |

## Running locally

Setup instructions will be added when the Django project is created (Week 2).

