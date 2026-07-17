# 3–5 minute demonstration guide

## Preparation checklist

- Start the backend and frontend locally, or use the verified Compose setup.
- Apply Alembic migrations and confirm `/health` reports a connected database.
- Use a fictional PDF/DOCX resume and fictional job description.
- Ensure the Sentence Transformer model is cached, or explain that first use
  may download/load it.
- Keep Swagger and logs free of credentials and personal data.

## Demonstration script

1. Introduce the project as a React/Vite and FastAPI platform for resume
   parsing, ATS-style guidance, matching, role recommendations, and feedback.
2. Register or log in with a fictional account.
3. Upload the sample resume and enter a job description in Analyze mode.
4. Point out structured candidate extraction, matched/missing skills, ATS-style
   components, TF-IDF/semantic similarity, and top semantic matches.
5. Open Roles mode and explain that roles come from repository-maintained
   profiles, with exact-skill and semantic components exposed.
6. Open Improve mode and show deterministic section, bullet, action-verb,
   quantification, repetition, readability, and privacy-safe evidence feedback.
7. Open Analysis History and show that reports are scoped to the logged-in user.
8. Scroll to Meet the Developer and the project footer.
9. Use the architecture diagram to explain the frontend, API, services, model,
   and database layers.

## Backup plan and common mistakes

If the semantic model is still loading, explain the lazy model lifecycle and use
Parse or Improve mode while it becomes available. Do not claim semantic results
were produced if the model failed. Avoid using a real resume, forgetting the
job-description minimum, or presenting internal scores as hiring probabilities.

## Recruiter-focused explanation

“This project combines deterministic extraction and ATS-style signals with
semantic similarity so keyword overlap is not the only signal. It keeps the
score components visible, adds role and writing feedback, and stores reports
per authenticated user. The outputs are advisory and designed for inspection,
not as employer decisions.”
