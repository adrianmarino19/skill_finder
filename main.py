from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import json
from google import genai
from collections import Counter

# Load environment variables from .env file
load_dotenv()

# Load your API keys from environment variables
GEM_KEY = os.environ.get("GEM_KEY")
# (Set your other keys similarly, e.g., DEEP_APIKEY, HF_API_TOKEN, etc.)

# Initialize FastAPI app
app = FastAPI(title="Job Helper API")


### Middleware

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Job Helper API")

# Add CORS middleware so your frontend can access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Utility Functions
# ----------------------------

def remove_stopwords(text: str) -> str:
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
    return ' '.join(filtered_tokens)

def fetch_job_description(job_url: str, headers: dict) -> str:
    try:
        response = requests.get(job_url, headers=headers)
        if response.status_code != 200:
            return "Failed to fetch job description"
        soup = BeautifulSoup(response.content, "html.parser")
        description_div = soup.find("div", class_="show-more-less-html__markup")
        if description_div:
            return description_div.get_text(strip=True).replace("\n", " ")
        return "No description available"
    except Exception as e:
        return f"Error fetching job description: {e}"

def scrape_jobs_with_descriptions(keywords: str, location: str, f_WT: str, pages_to_scrape: int, headers: dict):
    keywords_encoded = quote(keywords)
    location_encoded = quote(location)
    jobs = []
    for page in range(pages_to_scrape):
        url = (f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/"
               f"search?keywords={keywords_encoded}&location={location_encoded}&f_WT={f_WT}&start={25 * page}")
        print(f"Scraping job list page: {url}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch page {page + 1}: {response.status_code}")
            continue
        soup = BeautifulSoup(response.content, "html.parser")
        divs = soup.find_all("div", class_="base-card")
        for div in divs:
            try:
                title = div.find("h3", class_="base-search-card__title").text.strip()
                company = div.find("h4", class_="base-search-card__subtitle").text.strip()
                loc = div.find("span", class_="job-search-card__location").text.strip()
                job_link_tag = div.find("a", class_="base-card__full-link")
                job_url = job_link_tag["href"] if job_link_tag else "No URL found"
                job_description = (fetch_job_description(job_url, headers)
                                   if job_url != "No URL found" else "No description available")
                job_description = remove_stopwords(job_description)
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": loc,
                    "url": job_url,
                    "description": job_description
                })
            except Exception as e:
                print(f"Error parsing job: {e}")
    return jobs

def clean_json_output(response_text: str) -> str:
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[len("```json"):].strip()
    if response_text.endswith("```"):
        response_text = response_text[:-len("```")].strip()
    return response_text


# Initialize the Gemini client (from Google GenAI)
client = genai.Client(api_key=GEM_KEY)

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
    prompt = (
        "Extract the relevant hard skills and soft skills from the following job description. "
        "Return a JSON object with exactly two keys: 'hard_skills' and 'soft_skills', mapping to arrays of strings.\n\n"
        f"Job Description: {req.job_description}"
    )
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    cleaned = clean_json_output(response.text)
    try:
        skills = json.loads(cleaned)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing skills: {e}")
    return skills

@app.post("/pipeline")
def pipeline_endpoint(req: PipelineRequest):
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
    jobs = scrape_jobs_with_descriptions(req.keywords, req.location, req.f_WT, req.pages_to_scrape, headers)
    # Example: For each job, extract skills using the Gemini API
    for job in jobs:
        prompt = (
            "Extract the relevant hard skills and soft skills from the following job description. "
            "Return a JSON object with exactly two keys: 'hard_skills' and 'soft_skills', mapping to arrays of strings.\n\n"
            f"Job Description: {job['description']}"
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        cleaned = clean_json_output(response.text)
        try:
            skills = json.loads(cleaned)
        except Exception as e:
            skills = {"hard_skills": [], "soft_skills": []}
        job["extracted_skills"] = skills
    return {"jobs": jobs}
