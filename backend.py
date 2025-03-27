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
import re  # For stripping out code fences

# Ensure necessary NLTK resources are downloaded
nltk.download('punkt')
nltk.download('stopwords')

load_dotenv()
GEM_KEY = os.environ.get("GEM_KEY")
client = genai.Client(api_key=GEM_KEY)

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

conn = sqlite3.connect(':memory:', check_same_thread=False)
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
        job["db_id"] = cur.lastrowid
    conn.commit()

def update_job_skills(job, extracted_skills):
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
    base_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords_encoded}&location={location_encoded}"
    if remote:
        rem_values = ",".join([remote_mapping.get(r, "") for r in remote])
        base_url += f"&f_Rem={rem_values}"
    if experience_level:
        exp_values = ",".join([experience_mapping.get(e, "") for e in experience_level])
        base_url += f"&f_E={exp_values}"
    if benefits:
        ben_values = ",".join([benefits_mapping.get(b, "") for b in benefits])
        base_url += f"&f_BEN={ben_values}"
    if date_posted:
        dp_value = date_posted_mapping.get(date_posted, "")
        if dp_value:
            base_url += f"&f_TPR={dp_value}"
    if sortby:
        sb_value = sortby_mapping.get(sortby, "")
        if sb_value:
            base_url += f"&sortBy={sb_value}"
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

def batch_jobs(jobs, batch_size):
    for i in range(0, len(jobs), batch_size):
        yield jobs[i:i + batch_size]

def batch_extract_skills(jobs, batch_size):
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
    if pages_to_scrape <= 0:
        return len(jobs)
    jobs_per_page = len(jobs) // pages_to_scrape
    if jobs_per_page <= 0:
        return len(jobs)
    return jobs_per_page * 2

def run_pipeline(keywords: str, location: str, pages_to_scrape: int,
                 experience_level=[], remote=[], sortby="", date_posted="",
                 easy_apply=False, benefits=[]):
    if date_posted == "Any time":
        date_posted = ""

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
    jobs = scrape_jobs_with_descriptions(keywords, location, pages_to_scrape, headers,
                                         experience_level, remote, date_posted, benefits,
                                         easy_apply, sortby)
    if not jobs:
        return None, None

    create_jobs_table()
    insert_jobs(jobs, experience_level, remote, benefits, easy_apply, sortby, date_posted)

    batch_size = compute_batch_size(jobs, pages_to_scrape)
    extracted_skills = batch_extract_skills(jobs, batch_size)

    for job, skills in zip(jobs, extracted_skills):
        job["extracted_skills"] = skills
        update_job_skills(job, skills)

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

# ---------------------------------------------------------------------------
#   NEW: SQL-DRIVEN QUESTION ANSWERING
#   1) LLM generates a strict SQL query.
#   2) We execute the SQL query.
#   3) We ask the LLM to summarize the results in natural language.
# ---------------------------------------------------------------------------
def answer_user_question(question: str):
    # Define the database schema for context.
    schema = """
    The SQLite database has a table called 'jobs' with the following schema:
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
    soft_skills_count INTEGER.
    """

    # First prompt: Force the LLM to generate only an SQL query.
    prompt = f"""
    You are an expert SQL query generator.
    Given the following database schema:
    {schema}
    Write an SQL query that retrieves the answer to the following question:
    "{question}"
    ONLY output the SQL query. Do not include any explanations or additional text.
    """
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    answer_raw = response.text.strip()
    # Strip out any code fences or markdown.
    answer_stripped = re.sub(r"```[a-zA-Z]*", "", answer_raw).replace("```", "").strip()

    # Check if the output appears to be an SQL query (i.e., contains SELECT).
    if "SELECT" in answer_stripped.upper():
        try:
            cur = conn.cursor()
            cur.execute(answer_stripped)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=columns)

            # Second prompt: Ask the LLM to summarize the query results.
            prompt2 = f"""
            You are an expert data analyst.
            The following JSON array represents the result of an SQL query executed on a database:
            {df.to_json(orient='records')}
            Based on this data, provide a clear, concise, natural language answer to the user's question:
            "{question}"
            Do NOT include any SQL code in your response.
            """
            response2 = client.models.generate_content(model="gemini-2.0-flash", contents=prompt2)
            final_answer = response2.text.strip()

            if not final_answer or "SELECT" in final_answer.upper():
                final_answer = "I'm sorry, I could not generate a proper summary from the query result."
            return final_answer, df

        except Exception as e:
            return f"Error executing SQL query: {e}", None
    else:
        # If no valid SQL query is generated, ask the user to rephrase.
        return "Could not generate a valid SQL query from your question. Please try rephrasing your question.", None
