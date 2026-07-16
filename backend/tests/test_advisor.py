from app.advisor import analyze_resume_quality
from app.extractor import extract_resume_information
from app.skills import compare_resume_and_job_skills


resume_text = """
ANSHUMAN PATTANAYAK

Email: anshuman@example.com
Phone: +91 9876543210

SUMMARY
Computer Science student with knowledge of Python and AI.

SKILLS
Python, Machine Learning, FastAPI, SQL, Git

PROJECTS
Worked on resume analyzer.
Used Python and FastAPI.
Made a machine learning model.
Responsible for testing the application.

EDUCATION
B.Tech Computer Science and Engineering
CGPA: 8.2
"""

job_description = """
We are looking for a Python AI engineer with experience in
FastAPI, Docker, AWS, machine learning, REST APIs, SQL and Git.
Candidates should have experience deploying AI applications.
"""


parsed_data = extract_resume_information(
    resume_text
)

skill_comparison = compare_resume_and_job_skills(
    resume_text=resume_text,
    job_description=job_description,
)

result = analyze_resume_quality(
    resume_text=resume_text,
    parsed_data=parsed_data,
    skill_comparison=skill_comparison,
)


print("\nQuality score:")
print(result["quality_score"])

print("\nQuality rating:")
print(result["quality_rating"])

print("\nWeak phrases:")
print(result["weak_phrases"])

print("\nRecommendations:")

for recommendation in result[
    "priority_recommendations"
]:
    print(
        recommendation["priority"],
        recommendation["category"],
        recommendation["recommendation"],
    )

print("\nBullet templates:")

for template in result["bullet_point_templates"]:
    print(template)