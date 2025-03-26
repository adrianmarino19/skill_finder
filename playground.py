import streamlit as st
from backend import run_pipeline, answer_user_question

# Set page configuration.
st.set_page_config(
    page_title="Job Helper",
    layout="wide",
)

# Initialize session state for conversation history and pipeline flag.
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [
        {"role": "assistant", "content": "Hello! I am Job Helper. How can I assist you with your job search today?"}
    ]
if "pipeline_ran" not in st.session_state:
    st.session_state.pipeline_ran = False

# Sidebar mode selection: Job Search vs. Chat.
mode = st.sidebar.radio("Select Mode:", options=["Job Search", "Chat with Job Helper"])

# ================================
# Job Search Interface
# ================================
if mode == "Job Search":
    st.title("Job Helper")
    st.write("Enter parameters to run the pipeline:")

    # Row 1: Job title, Location, Experience Level
    col1, col2, col3 = st.columns(3)
    keywords = col1.text_input("Job title, skill, or company", "software engineer")
    location = col2.text_input("Location", "New York, USA")
    exp_options = ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
    experience_level = col3.multiselect("Experience Level", options=exp_options)

    # Row 2: Remote Options and Pages to Scrape
    col4, col5, col6 = st.columns(3)
    remote_options = ["Onsite", "Remote", "Hybrid"]
    remote = col4.multiselect("Remote Options", options=remote_options)
    pages_to_scrape = col5.number_input("Pages to Scrape", value=1, min_value=1)
    col6.empty()

    # Row 3: Advanced Filters (Sort By, Date Posted, Easy Apply, Benefits)
    with st.expander("Advanced Filters"):
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
            st.session_state.fig_hard = fig_hard
            st.session_state.fig_soft = fig_soft
            st.session_state.pipeline_ran = True

    if st.session_state.pipeline_ran:
        st.plotly_chart(st.session_state.fig_hard)
        st.plotly_chart(st.session_state.fig_soft)

    st.markdown("---")
    st.subheader("Ask JobHelper a question about your query:")
    user_question = st.text_input("Enter your question here", key="job_question")
    if st.button("Submit Question", key="job_submit"):
        with st.spinner("Processing your question..."):
            answer, df_result = answer_user_question(user_question)
        st.write("### Answer:")
        st.write(answer)
        if df_result is not None and not df_result.empty:
            st.write("### Query Result Data:")
            st.dataframe(df_result)

# ================================
# Chat Interface
# ================================
elif mode == "Chat with Job Helper":
    st.title("Interactive Chat with Job Helper")
    st.write("You can ask any question about your job search or the underlying data.")

    # Use the native chat input (available in newer versions of Streamlit).
    chat_input = st.chat_input("Type your message here:")
    if chat_input:
        st.session_state.conversation_history.append({"role": "user", "content": chat_input})
        with st.spinner("Processing..."):
            answer, _ = answer_user_question(chat_input)
        st.session_state.conversation_history.append({"role": "assistant", "content": answer})

    # Display the chat history (limit to the last 20 messages).
    for msg in st.session_state.conversation_history[-20:]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])
