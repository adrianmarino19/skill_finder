import streamlit as st
from backend import run_pipeline

# Inject CSS for uniform input widths.
st.markdown(
    """
    <style>
    .stTextInput>div>div>input {
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def main():
    st.title("Job Helper")
    st.write("Enter parameters to run the pipeline:")

    # Row 1: Job title, Location, Experience Level (multiselect)
    col1, col2, col3 = st.columns(3)
    keywords = col1.text_input("Job title, skill, or company", "software engineer")
    location = col2.text_input("Location", "New York, USA")
    exp_options = ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
    experience_level = col3.multiselect("Experience Level", options=exp_options)

    # Row 2: Remote Options (multiselect) and Pages to Scrape
    col4, col5, col6 = st.columns(3)
    remote_options = ["On-site", "Remote", "Hybrid"]
    remote = col4.multiselect("Remote Options", options=remote_options)
    pages_to_scrape = col5.number_input("Pages to Scrape", value=1, min_value=1)
    col6.empty()  # Empty for spacing

    # Row 3: Advanced Filters (Sort By, Date Posted, Easy Apply, Benefits)
    expand_filters = st.expander("Advanced Filters")
    with expand_filters:
        sortby_options = ["Relevance", "Date Posted"]
        sortby = st.selectbox("Sort By", options=sortby_options)

        date_posted_options = ["Any time", "Past 24 hours", "Past week", "Past month"]
        date_posted = st.selectbox("Date Posted", options=date_posted_options)
        if date_posted == "Choose an option":
            date_posted = ""

        easy_apply = st.checkbox("Easy Apply Only")

        benefits_options = [
            "Medical insurance", "Vision insurance", "Dental insurance", "401k",
            "Pension plan", "Paid maternity leave", "Paid paternity leave",
            "Commuter benefits", "Student loan assistance", "Tuition assistance",
            "Disability insurance"
        ]
        benefits = st.multiselect("Benefits", options=benefits_options)

    if st.button("Run Pipeline"):
        with st.spinner("Running pipeline, please wait..."):
            fig_hard, fig_soft = run_pipeline(
                keywords, location, pages_to_scrape,
                experience_level, remote, sortby, date_posted, easy_apply, benefits
            )
        if fig_hard and fig_soft:
            st.plotly_chart(fig_hard)
            st.plotly_chart(fig_soft)
        else:
            st.error("No jobs found or an error occurred during processing.")

if __name__ == "__main__":
    main()
