from django.db.models import Prefetch
from django.urls import reverse

from apps.cv.models import CvProject, Entry, Evidence, Profile, Readout, Skill, SkillGroup


def cv_context() -> dict:
    """Everything the CV page shows, in the order it shows it."""
    entries = Entry.objects.select_related("project")
    return {
        "profile": Profile.objects.first(),
        "readouts": Readout.objects.all(),
        "education": entries.filter(kind=Entry.Kind.EDUCATION),
        "experience": entries.filter(kind=Entry.Kind.EXPERIENCE),
        "cv_projects": CvProject.objects.select_related("write_up"),
        "skill_groups": SkillGroup.objects.prefetch_related(
            Prefetch(
                "skills",
                queryset=Skill.objects.prefetch_related(
                    Prefetch("evidence", queryset=Evidence.objects.select_related("project"))
                ),
            )
        ),
    }


def cv_summary() -> dict:
    """The CV in brief, for the CV windows on the monitors' desktops on the projects page."""
    profile = Profile.objects.first()

    def when(entry: Entry) -> str:
        # An en dash between the dates, as on the CV.
        return f"{entry.started} \u2013 {entry.ended or 'now'}"

    return {
        "url": reverse("cv:page"),
        "name": profile.name if profile else "",
        "role": profile.role if profile else "",
        "profile": profile.summary if profile else "",
        "education": [
            {"title": entry.title, "where": entry.organisation, "when": when(entry)}
            for entry in Entry.objects.filter(kind=Entry.Kind.EDUCATION)
        ],
        "experience": [
            {
                "title": entry.title,
                "where": entry.organisation,
                "when": when(entry),
                "summary": entry.summary or " ".join(entry.point_list[:1]),
            }
            for entry in Entry.objects.filter(kind=Entry.Kind.EXPERIENCE)
        ],
        "projects": [
            {"title": project.title, "stack": project.stack} for project in CvProject.objects.all()
        ],
        "skills": ", ".join(Skill.objects.filter(group__position=0).values_list("name", flat=True)),
    }
