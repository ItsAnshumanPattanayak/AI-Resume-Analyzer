from app.extractor import extract_skills, flatten_skills


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill before comparison.
    """

    return skill.strip().lower()


def extract_flat_skills(text: str) -> list[str]:
    """
    Extract skills and return one flat list.
    """

    categorized_skills = extract_skills(text)
    return flatten_skills(categorized_skills)


def compare_resume_and_job_skills(
    resume_text: str,
    job_description: str,
) -> dict:
    """
    Compare resume skills with job-description skills.
    """

    resume_skills = extract_flat_skills(resume_text)
    job_skills = extract_flat_skills(job_description)

    resume_skill_map = {
        normalize_skill(skill): skill
        for skill in resume_skills
    }

    job_skill_map = {
        normalize_skill(skill): skill
        for skill in job_skills
    }

    resume_skill_set = set(resume_skill_map)
    job_skill_set = set(job_skill_map)

    matched_skill_keys = resume_skill_set.intersection(job_skill_set)
    missing_skill_keys = job_skill_set.difference(resume_skill_set)
    additional_skill_keys = resume_skill_set.difference(job_skill_set)

    matched_skills = sorted(
        [job_skill_map[key] for key in matched_skill_keys],
        key=str.lower,
    )

    missing_skills = sorted(
        [job_skill_map[key] for key in missing_skill_keys],
        key=str.lower,
    )

    additional_skills = sorted(
        [resume_skill_map[key] for key in additional_skill_keys],
        key=str.lower,
    )

    if job_skills:
        skill_match_percentage = (
            len(matched_skills) / len(job_skills)
        ) * 100
    else:
        skill_match_percentage = 0.0

    return {
        "resume_skills": resume_skills,
        "job_required_skills": job_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "additional_resume_skills": additional_skills,
        "matched_count": len(matched_skills),
        "missing_count": len(missing_skills),
        "skill_match_percentage": round(
            skill_match_percentage,
            2,
        ),
    }