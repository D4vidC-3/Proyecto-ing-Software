from app.models.candidate_profile import CandidateProfile


def profile_gaps(p: CandidateProfile):
    """No bloquea guardado. Vacío = desconocido; opcional no significa completo."""
    items = [
        ("name", "Nombre", bool(p.name), "recomendado"),
        ("contact", "Correo o teléfono", bool(p.email or p.phone), "recomendado"),
        ("location", "Ubicación", bool(p.location), "recomendado"),
        (
            "target_role",
            "Cargo objetivo",
            bool(p.target_role or p.preferences.desired_roles),
            "recomendado",
        ),
        ("skills", "Habilidades", bool(p.skills), "recomendado"),
        ("languages", "Idiomas", bool(p.languages), "opcional"),
        (
            "education",
            "Educación",
            any(e.degree or e.institution for e in p.education),
            "opcional",
        ),
        (
            "experience",
            "Experiencia (0 indica sin experiencia)",
            p.years_experience is not None
            or any(e.role or e.company for e in p.work_experience),
            "opcional",
        ),
        (
            "work_modes",
            "Modalidad laboral",
            bool(p.preferences.work_modes),
            "recomendado",
        ),
        (
            "salary",
            "Aspiración salarial",
            p.preferences.salary_min_cop is not None
            or p.preferences.salary_max_cop is not None,
            "opcional",
        ),
        (
            "availability",
            "Disponibilidad",
            bool(p.preferences.availability),
            "opcional",
        ),
    ]
    return [
        dict(
            field=k,
            label=label,
            importance=importance,
            status="informado" if present else "desconocido",
            missing=not present,
        )
        for k, label, present, importance in items
    ]
