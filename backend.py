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
import sqlite3

# Ensure necessary NLTK resources are downloaded
nltk.download('punkt')
nltk.download('stopwords')

# Load environment variables and initialize Gemini client
load_dotenv()
GEM_KEY = os.environ.get("GEM_KEY")
client = genai.Client(api_key=GEM_KEY)

# --- Mapping dictionaries for filters ---
remote_mapping = {"Onsite": "1", "Remote": "2", "Hybrid": "3"}
experience_mapping = {
    "Internship": "1",
    "Entry level": "2",
    "Associate": "3",
    "Mid-Senior level": "4",
    "Director": "5",
    "Executive": "6"
}
benefits_mapping = {
    "Medical insurance": "1",
    "Vision insurance": "2",
    "Dental insurance": "3",
    "401k": "4",
    "Pension plan": "5",
    "Paid maternity leave": "6",
    "Paid paternity leave": "7",
    "Commuter benefits": "8",
    "Student loan assistance": "9",
    "Tuition assistance": "10",
    "Disability insurance": "11"
}
sortby_mapping = {"Relevance": "r", "Date Posted": "DD"}
date_posted_mapping = {"Past 24 hours": "r86400", "Past week": "r604800", "Past month": "r2592000"}

### SQLite Setup ###
# Create an in-memory SQLite database.
conn = sqlite3.connect(':memory:', check_same_thread=False)
# conn = sqlite3.connect('jobs.db', check_same_thread=False)
cur = conn.cursor()

def create_jobs_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company TEXT,
            location TEXT,
            job_url TEXT,
            job_description TEXT,
            experience_level TEXT,
            remote TEXT,
            benefits TEXT,
            easy_apply INTEGER,
            date_posted TEXT,
            sortby TEXT,
            extracted_hard_skills TEXT,
            extracted_soft_skills TEXT,
            hard_skills_count INTEGER,
            soft_skills_count INTEGER
        )
    """)
    conn.commit()

def insert_jobs(jobs, experience_level, remote, benefits, easy_apply, sortby, date_posted):
    """
    Insert scraped jobs into the database.
    The filter parameters (experience, remote, benefits, easy_apply, sortby, date_posted)
    are saved with each job.
    """
    for job in jobs:
        cur.execute("""
            INSERT INTO jobs (
                job_title, company, location, job_url, job_description,
                experience_level, remote, benefits, easy_apply, date_posted, sortby
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("title"),
            job.get("company"),
            job.get("location"),
            job.get("url"),
            job.get("description"),
            ",".join(experience_level) if experience_level else "",
            ",".join(remote) if remote else "",
            ",".join(benefits) if benefits else "",
            1 if easy_apply else 0,
            date_posted,
            sortby
        ))
        # Save the DB row ID with the job record for later updates.
        job["db_id"] = cur.lastrowid
    conn.commit()

def update_job_skills(job, extracted_skills):
    """
    Update a job record with the extracted skills and their counts.
    """
    hard_skills = extracted_skills.get("hard_skills", [])
    soft_skills = extracted_skills.get("soft_skills", [])
    hard_count = len(hard_skills)
    soft_count = len(soft_skills)
    cur.execute("""
        UPDATE jobs
        SET extracted_hard_skills = ?,
            extracted_soft_skills = ?,
            hard_skills_count = ?,
            soft_skills_count = ?
        WHERE id = ?
    """, (
        json.dumps(hard_skills),
        json.dumps(soft_skills),
        hard_count,
        soft_count,
        job["db_id"]
    ))
    conn.commit()

### End SQLite Setup ###

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

def scrape_jobs_with_descriptions(keywords: str, location: str, pages_to_scrape: int, headers: dict,
                                  experience_level=[], remote=[], date_posted="", benefits=[],
                                  easy_apply=False, sortby=""):
    keywords_encoded = quote(keywords)
    location_encoded = quote(location)

    # Build base URL with mandatory parameters.
    base_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords_encoded}&location={location_encoded}"

    # Append remote filter if provided.
    if remote:
        rem_values = ",".join([remote_mapping.get(r, "") for r in remote])
        base_url += f"&f_Rem={rem_values}"

    # Append experience level filter if provided.
    if experience_level:
        exp_values = ",".join([experience_mapping.get(e, "") for e in experience_level])
        base_url += f"&f_E={exp_values}"

    # Append benefits filter if provided.
    if benefits:
        ben_values = ",".join([benefits_mapping.get(b, "") for b in benefits])
        base_url += f"&f_BEN={ben_values}"

    # Append date posted filter if provided.
    if date_posted:
        dp_value = date_posted_mapping.get(date_posted, "")
        if dp_value:
            base_url += f"&f_TPR={dp_value}"

    # Append sort by filter if provided.
    if sortby:
        sb_value = sortby_mapping.get(sortby, "")
        if sb_value:
            base_url += f"&sortBy={sb_value}"

    # Append easy apply filter if true.
    if easy_apply:
        base_url += "&f_EA=true"

    jobs = []
    for page in range(pages_to_scrape):
        url = base_url + f"&start={25 * page}"
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
            batch_parsed = json.loads(cleaned)
            if not isinstance(batch_parsed, list) or len(batch_parsed) != len(batch):
                print("Warning: Parsed output count does not match number of job descriptions in the batch.")
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

def run_pipeline(keywords: str, location: str, pages_to_scrape: int,
                 experience_level=[], remote=[], sortby="", date_posted="",
                 easy_apply=False, benefits=[]):
    # If "Any time" is selected, remove date filter.
    if date_posted == "Any time":
        date_posted = ""

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }

    # Scrape jobs
    jobs = scrape_jobs_with_descriptions(keywords, location, pages_to_scrape, headers,
                                         experience_level, remote, date_posted, benefits,
                                         easy_apply, sortby)
    if not jobs:
        return None, None

    # Create the in-memory database and table, then insert scraped jobs.
    create_jobs_table()
    insert_jobs(jobs, experience_level, remote, benefits, easy_apply, sortby, date_posted)

    # Batch extract skills using LLM.
    batch_size = compute_batch_size(jobs, pages_to_scrape)
    extracted_skills = batch_extract_skills(jobs, batch_size)

    # Update each job record with extracted skills.
    for job, skills in zip(jobs, extracted_skills):
        job["extracted_skills"] = skills
        update_job_skills(job, skills)

    # Aggregate skills across jobs.
    hard_skills_counter = Counter()
    soft_skills_counter = Counter()
    for job in jobs:
        skills = job.get("extracted_skills", {})
        hard_skills_counter.update(skills.get("hard_skills", []))
        soft_skills_counter.update(skills.get("soft_skills", []))

    df_hard = pd.DataFrame(hard_skills_counter.items(), columns=["Skill", "Frequency"])
    df_soft = pd.DataFrame(soft_skills_counter.items(), columns=["Skill", "Frequency"])

    df_hard_sorted = df_hard.sort_values("Frequency", ascending=False).head(15)
    df_soft_sorted = df_soft.sort_values("Frequency", ascending=False).head(15)

    total_hard = df_hard_sorted["Frequency"].sum()
    total_soft = df_soft_sorted["Frequency"].sum()
    df_hard_sorted["Percentage"] = df_hard_sorted["Frequency"] / total_hard * 100
    df_soft_sorted["Percentage"] = df_soft_sorted["Frequency"] / total_soft * 100

    fig_hard = px.bar(
        df_hard_sorted,
        x="Frequency",
        y="Skill",
        orientation='h',
        title="Top 15 Hard Skills",
        labels={"Skill": "Hard Skills", "Frequency": "Count"},
        color="Frequency",
        color_continuous_scale="Blues",
        text=df_hard_sorted["Percentage"].apply(lambda x: f"{x:.1f}%")
    )
    fig_hard.update_traces(textposition='outside')
    fig_hard.update_layout(yaxis={'categoryorder':'total ascending'})

    fig_soft = px.bar(
        df_soft_sorted,
        x="Frequency",
        y="Skill",
        orientation='h',
        title="Top 15 Soft Skills",
        labels={"Skill": "Soft Skills", "Frequency": "Count"},
        color="Frequency",
        color_continuous_scale="Blues",
        text=df_soft_sorted["Percentage"].apply(lambda x: f"{x:.1f}%")
    )
    fig_soft.update_traces(textposition='outside')
    fig_soft.update_layout(yaxis={'categoryorder':'total ascending'})

    return fig_hard, fig_soft
