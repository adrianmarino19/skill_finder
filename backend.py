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
import pandas as pd
import plotly.express as px
from collections import Counter

# Ensure necessary NLTK resources are downloaded
nltk.download('punkt')
nltk.download('stopwords')

# Load environment variables and initialize Gemini client
load_dotenv()
GEM_KEY = os.environ.get("GEM_KEY")
client = genai.Client(api_key=GEM_KEY)

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

def extract_skills(job_description: str) -> dict:
    """
    Extract skills from a single job description using the Gemini API.
    """
    prompt = (
        "Extract the relevant hard skills and soft skills from the following job description. "
        "Return a JSON object with exactly two keys: 'hard_skills' and 'soft_skills', mapping to arrays of strings.\n\n"
        f"Job Description: {job_description}"
    )
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    cleaned = clean_json_output(response.text)
    try:
        skills = json.loads(cleaned)
    except Exception as e:
        skills = {"hard_skills": [], "soft_skills": []}
    return skills

# --- Batching Functions (all logic resides here) ---

def batch_jobs(jobs, batch_size):
    """Yield successive batches from the jobs list."""
    for i in range(0, len(jobs), batch_size):
        yield jobs[i:i + batch_size]

def batch_extract_skills(jobs, batch_size):
    """
    Batch multiple job descriptions into one API call.
    Returns a list of extracted skills corresponding to each job in the batches.
    """
    extracted_skills = []
    for batch in batch_jobs(jobs, batch_size):
        # Combine job descriptions with a clear delimiter.
        descriptions = "\n---\n".join(job['description'] for job in batch)
        prompt = (
            "Below are several job descriptions separated by '---'. "
            "For each job description, extract the relevant hard skills and soft skills. "
            "For hard skills, include programming languages, libraries, and technologies mentioned. "
            "Return a JSON array where each element is an object with exactly two keys: "
            "'hard_skills' and 'soft_skills', mapping to arrays of strings. "
            "Only output the JSON array with no extra text or markdown formatting.\n\n" +
            descriptions
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        cleaned = clean_json_output(response.text)
        try:
            # Expecting a JSON array with one element per job description in the batch.
            batch_parsed = json.loads(cleaned)
            if not isinstance(batch_parsed, list) or len(batch_parsed) != len(batch):
                print("Warning: Parsed output count does not match number of job descriptions in the batch.")
            # Normalize skills to lowercase for consistency.
            for job_skills in batch_parsed:
                if "hard_skills" in job_skills:
                    job_skills["hard_skills"] = [skill.lower() for skill in job_skills["hard_skills"]]
                if "soft_skills" in job_skills:
                    job_skills["soft_skills"] = [skill.lower() for skill in job_skills["soft_skills"]]
            extracted_skills.extend(batch_parsed)
        except Exception as e:
            print("Error parsing batched JSON:", e)
    return extracted_skills

def compute_batch_size(jobs, pages_to_scrape):
    """
    Compute batch size based on the notebook logic:
      - jobs_per_page = len(jobs) // pages_to_scrape
      - batch_size = jobs_per_page * 2  (two pages per batch)
    """
    if pages_to_scrape <= 0:
        return len(jobs)
    jobs_per_page = len(jobs) // pages_to_scrape
    if jobs_per_page <= 0:
        return len(jobs)
    return jobs_per_page * 2

def run_pipeline(keywords: str, location: str, f_WT: str, pages_to_scrape: int):
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
    # Scrape job postings
    jobs = scrape_jobs_with_descriptions(keywords, location, f_WT, pages_to_scrape, headers)
    if not jobs:
        return None, None

    # Compute batch size based on scraped jobs and pages to scrape
    batch_size = compute_batch_size(jobs, pages_to_scrape)

    # Batch extract skills using the computed batch size
    extracted_skills = batch_extract_skills(jobs, batch_size)

    # Attach the extracted skills back to each job (assuming order is preserved)
    for job, skills in zip(jobs, extracted_skills):
        job["extracted_skills"] = skills

    # Aggregate the skills across all jobs.
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

    # Create Plotly figures.
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

    return fig_hard, fig_soft
