import streamlit as st
import time
import pandas as pd
import plotly.express as px
from collections import Counter

# Import shared functions from backend.py
from backend import (
    scrape_jobs_with_descriptions,
    batch_extract_skills
)

def run_pipeline(keywords: str, location: str, f_WT: str, pages_to_scrape: int, batch_size: int):
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }

    # Scrape job postings
    jobs = scrape_jobs_with_descriptions(keywords, location, f_WT, pages_to_scrape, headers)

    if not jobs:
        st.error("No jobs found. Try different parameters.")
        return None, None

    # Batch extract skills from the scraped jobs
    extracted_skills = batch_extract_skills(jobs, batch_size)

    # Attach the extracted skills back to each job
    # (Assuming the batch_extract_skills returns a list with the same order and length as jobs)
    for job, skills in zip(jobs, extracted_skills):
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

def main():
    st.title("Job Helper")
    st.write("Enter parameters to run the pipeline:")

    keywords = st.text_input("Title, skill, or company", "software engineer")
    location = st.text_input("Location", "New York, USA")
    f_WT = st.text_input("Work Type (f_WT)", "2")
    pages_to_scrape = st.number_input("Pages to Scrape", value=1, min_value=1)

    # Add an input for batch size
    batch_size = st.number_input("Batch Size (number of job descriptions per API request)", value=5, min_value=1)

    if st.button("Run Pipeline"):
        with st.spinner("Running pipeline, please wait..."):
            fig_hard, fig_soft = run_pipeline(keywords, location, f_WT, pages_to_scrape, batch_size)
        if fig_hard and fig_soft:
            st.plotly_chart(fig_hard)
            st.plotly_chart(fig_soft)

if __name__ == "__main__":
    main()
