import streamlit as st
from backend import run_pipeline

def main():
    st.title("Job Helper")
    st.write("Enter parameters to run the pipeline:")

    keywords = st.text_input("Title, skill, or company", "software engineer")
    location = st.text_input("Location", "New York, USA")
    f_WT = st.text_input("Work Type (f_WT)", "2")
    pages_to_scrape = st.number_input("Pages to Scrape", value=1, min_value=1)

    if st.button("Run Pipeline"):
        with st.spinner("Running pipeline, please wait..."):
            fig_hard, fig_soft = run_pipeline(keywords, location, f_WT, pages_to_scrape)
        if fig_hard and fig_soft:
            st.plotly_chart(fig_hard)
            st.plotly_chart(fig_soft)
        else:
            st.error("No jobs found or an error occurred during processing.")

if __name__ == "__main__":
    main()
