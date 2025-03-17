import streamlit as st
import requests
import json
import os
import time
import pandas as pd
import plotly.express as px
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from urllib.parse import quote
from collections import Counter
from bs4 import BeautifulSoup
from google import genai  # Make sure you have this installed
from dotenv import load_dotenv

# Load environment variables (ensure you have a .env file with GEM_KEY etc.)
load_dotenv()
GEM_KEY = os.environ.get("GEM_KEY")

# Initialize the Gemini client
client = genai.Client(api_key=GEM_KEY)

### Utility Functions ###

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
        st.write(f"Scraping job list page: {url}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.write(f"Failed to fetch page {page + 1}: {response.status_code}")
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
                st.write(f"Error parsing job: {e}")
        # Optional: Pause to avoid rate limiting
        time.sleep(2)
    return jobs

def clean_json_output(response_text: str) -> str:
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[len("```json"):].strip()
    if response_text.endswith("```"):
        response_text = response_text[:-len("```")].strip()
    return response_text

def run_pipeline(keywords: str, location: str, f_WT: str, pages_to_scrape: int):
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
    jobs = scrape_jobs_with_descriptions(keywords, location, f_WT, pages_to_scrape, headers)
    # For each job, extract skills using the Gemini API
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

    # Aggregate the skills across all jobs
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

    # Create Plotly figures
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

### Streamlit UI ###
def main():
    st.title("Job Helper Dashboard")
    st.write("Enter parameters to run the pipeline:")
    keywords = st.text_input("Keywords", "software engineer")
    location = st.text_input("Location", "New York, USA")
    f_WT = st.text_input("Work Type (f_WT)", "2")
    pages_to_scrape = st.number_input("Pages to Scrape", value=1, min_value=1)
    if st.button("Run Pipeline"):
        with st.spinner("Running pipeline, please wait..."):
            fig_hard, fig_soft = run_pipeline(keywords, location, f_WT, pages_to_scrape)
        st.plotly_chart(fig_hard)
        st.plotly_chart(fig_soft)

if __name__ == "__main__":
    main()
