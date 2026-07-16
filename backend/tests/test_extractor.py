from app.extractor import extract_resume_information


sample_resume = """
ANSHU KUMAR

Email: anshu@example.com
Phone: +91 9876543210
LinkedIn: https://www.linkedin.com/in/anshukumar
GitHub: https://github.com/anshukumar

SUMMARY
Computer Science student interested in Machine Learning and Agentic AI.

TECHNICAL SKILLS
Python, FastAPI, SQL, MongoDB, Git, GitHub, PyTorch,
Scikit-learn, Docker, Linux

EDUCATION
B.Tech in Computer Science and Engineering
Centurion University of Technology and Management
CGPA: 8.2

PROJECTS
AI Resume Analyzer using Python, FastAPI and NLP.
"""


result = extract_resume_information(sample_resume)

print("Name:", result["name"])
print("Email:", result["email"])
print("Phone:", result["phone"])
print("Links:", result["links"])
print("Skills:", result["skills"])
print("Education:", result["education"])
print("Sections:", result["sections"])