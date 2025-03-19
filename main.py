from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import plotly.express as px
import json
from collections import Counter

# Import shared functions from backend.py
from backend import scrape_jobs_with_descriptions, extract_skills

app = FastAPI(title="Job Helper API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Request Models
# ----------------------------
class ScrapeRequest(BaseModel):
    keywords: str = "software engineer"
    location: str = "New York, USA"
    f_WT: str = "2"
    pages_to_scrape: int = 1

class ExtractRequest(BaseModel):
    job_description: str

class PipelineRequest(BaseModel):
    keywords: str = "software engineer"
    location: str = "New York, USA"
    f_WT: str = "2"
    pages_to_scrape: int = 1

# ----------------------------
# API Endpoints
# ----------------------------
@app.post("/scrape-jobs")
def scrape_jobs_endpoint(req: ScrapeRequest):
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
    jobs = scrape_jobs_with_descriptions(req.keywords, req.location, req.f_WT, req.pages_to_scrape, headers)
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")
    return {"jobs": jobs}

@app.post("/extract-skills")
def extract_skills_endpoint(req: ExtractRequest):
    skills = extract_skills(req.job_description)
    return skills

@app.post("/pipeline")
def pipeline_endpoint(req: PipelineRequest):
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
    # Scrape job postings using the provided parameters
    jobs = scrape_jobs_with_descriptions(req.keywords, req.location, req.f_WT, req.pages_to_scrape, headers)

    # Extract skills for each job posting
    for job in jobs:
        job["extracted_skills"] = extract_skills(job["description"])

    # Aggregate skills across all jobs
    hard_skills_counter = Counter()
    soft_skills_counter = Counter()
    for job in jobs:
        skills = job.get("extracted_skills", {})
        hard_skills_counter.update(skills.get("hard_skills", []))
        soft_skills_counter.update(skills.get("soft_skills", []))

    df_hard = pd.DataFrame(hard_skills_counter.items(), columns=["Skill", "Frequency"])
    df_soft = pd.DataFrame(soft_skills_counter.items(), columns=["Skill", "Frequency"])

    df_hard_sorted = df_hard.sort_values("Frequency", ascending=False)
    df_soft_sorted = df_soft.sort_values("Frequency", ascending=False)

    fig_hard = px.bar(
        df_hard_sorted,
        x="Skill",
        y="Frequency",
        title="Top Hard Skills",
        labels={"Skill": "Hard Skill", "Frequency": "Count"},
        color="Frequency",
        color_continuous_scale="Blues"
    )
    fig_hard.update_layout(xaxis_tickangle=-45)

    fig_soft = px.bar(
        df_soft_sorted,
        x="Skill",
        y="Frequency",
        title="Top Soft Skills",
        labels={"Skill": "Soft Skill", "Frequency": "Count"},
        color="Frequency",
        color_continuous_scale="Blues"
    )
    fig_soft.update_layout(xaxis_tickangle=-45)

    html_hard = fig_hard.to_html(full_html=False, include_plotlyjs="cdn")
    html_soft = fig_soft.to_html(full_html=False, include_plotlyjs="cdn")

    return {"hard_skills_graph": html_hard, "soft_skills_graph": html_soft}
