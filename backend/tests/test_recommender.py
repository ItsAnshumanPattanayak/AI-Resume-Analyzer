from app.recommender import recommend_job_roles


resume_text = """
ANSHUMAN PATTANAYAK

Computer Science student with experience in Python,
machine learning, deep learning and artificial intelligence.

TECHNICAL SKILLS
Python, FastAPI, SQL, Git, GitHub, Pandas, NumPy,
Scikit-learn, PyTorch, TensorFlow, Machine Learning,
Deep Learning, NLP, RAG, LangChain and MongoDB.

PROJECTS
Built an AI resume analyzer using Python, FastAPI,
TF-IDF, cosine similarity and Sentence Transformers.

Developed machine learning projects using Pandas,
Scikit-learn and data preprocessing techniques.

Created agentic AI applications using LangChain,
retrieval augmented generation and large language models.
"""


result = recommend_job_roles(
    resume_text=resume_text,
    top_n=5,
)


print("\nCandidate skills:")
print(result["candidate_skills"])

print("\nBest role:")
print(result["best_role"])

print("\nRecommended roles:")

for recommendation in result["recommended_roles"]:
    print(
        recommendation["role"],
        recommendation["overall_match_percentage"],
        recommendation["recommendation_level"],
    )