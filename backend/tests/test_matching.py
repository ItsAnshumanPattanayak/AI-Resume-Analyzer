from app.ats import calculate_ats_score
from app.extractor import extract_resume_information
from app.similarity import calculate_tfidf_similarity
from app.skills import compare_resume_and_job_skills


resume_text = """
ANSHU KUMAR

Email: anshu@example.com
Phone: +91 9876543210
GitHub: https://github.com/anshu
LinkedIn: https://linkedin.com/in/anshu

SUMMARY
Computer Science student with experience in Python,
Machine Learning and FastAPI.

SKILLS
Python, FastAPI, SQL, Git, GitHub, Machine Learning,
Scikit-learn, MongoDB

EDUCATION
B.Tech Computer Science and Engineering
CGPA: 8.2

PROJECTS
Built an AI resume analyzer using Python and FastAPI.
Processed more than 1,000 resume records.
"""

job_description = """
We are hiring a Python backend developer with experience
in FastAPI, REST APIs, PostgreSQL, SQL, Git, Docker, Linux,
AWS and MongoDB. Machine learning knowledge is preferred.
"""


parsed_data = extract_resume_information(resume_text)

skill_comparison = compare_resume_and_job_skills(
    resume_text,
    job_description,
)

similarity = calculate_tfidf_similarity(
    resume_text,
    job_description,
)

ats_result = calculate_ats_score(
    resume_text=resume_text,
    parsed_data=parsed_data,
    skill_comparison=skill_comparison,
    text_similarity=similarity,
)


print("\nText similarity:")
print(similarity)

print("\nSkill comparison:")
print(skill_comparison)

print("\nATS result:")
print(ats_result)