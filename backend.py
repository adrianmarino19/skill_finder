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
            # Optional: check that the parsed array length matches the batch.
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
