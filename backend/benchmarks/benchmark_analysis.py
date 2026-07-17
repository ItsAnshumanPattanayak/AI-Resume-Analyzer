"""Synthetic, non-threshold performance benchmarks for local comparison."""

from __future__ import annotations

import argparse
import platform
import statistics
import sys
import time
from pathlib import Path


BACKEND_DIRECTORY = Path(__file__).resolve().parent.parent
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.ats import calculate_ats_score
from app.extractor import extract_resume_information
from app.recommender import recommend_job_roles, reset_recommender_caches
from app.semantic import reset_semantic_state
from app.skills import compare_resume_and_job_skills


RESUME = """
Synthetic Candidate
Python FastAPI SQL Docker Git AWS C++ C# .NET Node.js CI/CD
Built a synthetic API and improved test execution by 20 percent.
Experience
Developed backend services and machine learning prototypes.
Education
Bachelor of Computer Science
""".strip()

JOB = """
Seeking a Python backend engineer with FastAPI, SQL, Docker, Git, AWS,
automated testing, API design, and continuous integration experience.
""".strip()


def duration(function, iterations: int) -> list[float]:
    results = []
    for _ in range(iterations):
        started = time.perf_counter()
        function()
        results.append((time.perf_counter() - started) * 1000)
    return results


def non_semantic_analysis() -> None:
    parsed = extract_resume_information(RESUME)
    comparison = compare_resume_and_job_skills(
        RESUME,
        JOB,
        parsed["skills"]["all"],
    )
    calculate_ats_score(RESUME, parsed, comparison, 50.0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--semantic", action="store_true")
    arguments = parser.parse_args()
    if arguments.iterations < 1:
        parser.error("--iterations must be at least 1")

    timings = duration(non_semantic_analysis, arguments.iterations)
    print(f"environment={platform.platform()} python={platform.python_version()}")
    print("input=synthetic iterations=" + str(arguments.iterations))
    print(f"non_semantic_first_ms={timings[0]:.2f}")
    print(f"non_semantic_warm_median_ms={statistics.median(timings[1:] or timings):.2f}")

    if arguments.semantic:
        reset_semantic_state()
        reset_recommender_caches()
        started = time.perf_counter()
        recommend_job_roles(RESUME, 5)
        cold = (time.perf_counter() - started) * 1000
        warm = duration(lambda: recommend_job_roles(RESUME, 5), arguments.iterations)
        print(f"semantic_first_ms={cold:.2f}")
        print(f"semantic_warm_median_ms={statistics.median(warm):.2f}")
        print("semantic_note=model availability, hardware, and cache state affect results")
    else:
        print("semantic=not-run (pass --semantic only when the configured model is available)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
