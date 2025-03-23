import streamlit as st
from backend import run_pipeline

def main():
    col1, col2 = st.columns([2, 1])  # Adjust column widths to give more space to filters

    with col1:
        st.markdown("<div style='display: flex; justify-content: center; align-items: center; height: 30vh;'><div><h1>Job Helper</h1><p>Helping job seekers find the job of their dreams.</p></div></div>", unsafe_allow_html=True)

    with col2:
        st.header("Filters")
        keywords = st.text_input("Title, skill, or company", "software engineer")
        location = st.text_input("Location", "New York, USA")
        f_WT = st.text_input("Work Type (f_WT)", "2")
        pages_to_scrape = st.number_input("Pages to Scrape", value=1, min_value=1)

        if st.button("Run Pipeline"):
            with st.spinner("Running pipeline, please wait..."):
                fig_hard, fig_soft = run_pipeline(keywords, location, f_WT, pages_to_scrape)
            if fig_hard and fig_soft:
                st.plotly_chart(fig_hard, use_container_width=True) # full width
                st.plotly_chart(fig_soft, use_container_width=True) # full width
            else:
                st.error("No jobs found or an error occurred during processing.")

if __name__ == "__main__":
    main()
