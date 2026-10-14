"""Puntuación de afinidad determinista; nunca representa confianza de IA."""

import re
import unicodedata


def normalize(text):
    return (
        "".join(
            c
            for c in unicodedata.normalize("NFKD", text or "")
            if not unicodedata.combining(c)
        )
        .lower()
        .strip()
    )


def tokens(text):
    words = set(re.findall(r"[\w+#]+", normalize(text)))
    aliases = {
        "desarrolladora": "desarrollador",
        "developer": "desarrollador",
        "ingeniera": "ingeniero",
        "engineer": "ingeniero",
    }
    return {
        aliases.get(w, w)
        for w in words
        if w not in {"de", "en", "y", "el", "la", "software"}
    }


WEIGHTS = {"skills": 45, "role": 20, "work_mode": 15, "location": 10, "salary": 10}


def score(profile, vacancy):
    p, v = profile, vacancy
    skills = {normalize(s) for s in p.skills}
    required = {normalize(s) for s in v["required_skills"]}
    matched, missing = sorted(skills & required), sorted(required - skills)
    roles = [p.target_role] if p.target_role else []
    roles += p.preferences.desired_roles
    candidate_roles = set().union(*(tokens(r) for r in roles)) if roles else set()
    title = tokens(v["title"])
    modes = {normalize(m) for m in p.preferences.work_modes}
    locations = p.preferences.preferred_locations or (
        [p.location] if p.location else []
    )
    place = normalize(v.get("location"))
    locations_match = any(
        normalize(l).split(",")[0].strip() == place.split(",")[0].strip()
        for l in locations
    )
    low, high = p.preferences.salary_min_cop, p.preferences.salary_max_cop
    vlow, vhigh = v.get("salary_min_cop"), v.get("salary_max_cop")
    salary_known = (
        (low is not None or high is not None) and vlow is not None and vhigh is not None
    )
    salary_match = (
        salary_known
        and (low is None or vhigh >= low)
        and (high is None or vlow <= high)
    )
    fractions = {
        "skills": len(matched) / len(required) if required and skills else None,
        "role": (
            len(candidate_roles & title) / len(title)
            if title and candidate_roles
            else None
        ),
        "work_mode": (
            float(v["work_mode"] in modes) if modes and v.get("work_mode") else None
        ),
        "location": (
            (1.0 if v.get("work_mode") == "remoto" else float(locations_match))
            if locations and place
            else None
        ),
        "salary": float(salary_match) if salary_known else None,
    }
    labels = {
        "skills": "Habilidades requeridas coincidentes",
        "role": "Palabras del cargo coincidentes",
        "work_mode": "Modalidad preferida",
        "location": "Ciudad preferida o vacante remota",
        "salary": "Intersección de rangos salariales en COP",
    }
    components = [
        dict(
            criterion=k,
            weight=w,
            points=round(w * (fractions[k] or 0), 2),
            known=fractions[k] is not None,
            reason=(
                labels[k]
                if fractions[k] is not None
                else "Datos insuficientes: aporta 0, sin redistribuir el peso"
            ),
        )
        for k, w in WEIGHTS.items()
    ]
    return dict(
        vacancy=v,
        score=round(sum(c["points"] for c in components), 2),
        matched_skills=matched,
        missing_skills=missing,
        components=components,
        unknown=[c["criterion"] for c in components if not c["known"]],
    )
