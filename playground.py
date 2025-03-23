# frontend.py
import streamlit as st
from backend import run_pipeline

def main():
    st.title("Job Helper")
    st.write("Enter parameters to run the pipeline:")

    col1, col2, col3 = st.columns(3)
    keywords = col1.text_input("Title, skill, or company", "software engineer")
    location = col2.text_input("Location", "New York, USA")
    experience_level = col3.text_input("Experience Level")

    col4, col5, col6 = st.columns(3)
    f_WT = col4.text_input("Work Type (f_WT)", "2")
    pages_to_scrape = col5.number_input("Pages to Scrape", value=1, min_value=1)
    empty_col = col6.empty() #empty column for spacing

    expand_filters = st.expander("Advanced Filters")
    with expand_filters:
        benefits = st.text_input("Benefits (e.g., Health insurance, 401k)")
        easy_apply = st.checkbox("Easy Apply Only")

    if st.button("Run Pipeline"):
        with st.spinner("Running pipeline, please wait..."):
            fig_hard, fig_soft = run_pipeline(keywords, location, f_WT, pages_to_scrape, experience_level, benefits, easy_apply)
        if fig_hard and fig_soft:
            st.plotly_chart(fig_hard)
            st.plotly_chart(fig_soft)
        else:
            st.error("No jobs found or an error occurred during processing.")

if __name__ == "__main__":
    main()
