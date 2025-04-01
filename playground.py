import streamlit as st
from streamlit_chat import message
from backend import run_pipeline, answer_user_question

# -------------------
# 1) FOREST SCOUT THEME
# -------------------
st.set_page_config(
    page_title="Job Helper",
    page_icon="🌲",
    layout="wide",
)

# Inject CSS for theming.
# Adjust selectors or add additional styling rules as needed.
st.markdown(
    """
    <style>
    :root {
        --primary-color: #2F4F4F;            /* Deep forest green */
        --background-color: #F5F5DC;         /* Beige/tan */
        --secondary-background-color: #E0DAB8; /* Slightly darker tan */
        --text-color: #333333;               /* Dark gray text */
    }

    /* Main app background and text */
    div[data-testid="stAppViewContainer"] {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    /* Header or top area */
    div[data-testid="stHeader"] {
        background-color: var(--secondary-background-color);
    }

    /* Buttons */
    .stButton>button {
        background-color: var(--primary-color) !important;
        color: #FFFFFF !important;
        border: none;
    }
    .stButton>button:hover {
        filter: brightness(1.1);
    }

    /* Text inputs, multiselects, etc. */
    input, .stTextInput input, .stMultiSelect>div>div>div {
        background-color: #FFFFFF !important;
        color: var(--text-color) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------
# App Logic
# -------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [
        {"role": "assistant", "content": "Hello! I am JobHelper. How can I assist you?"}
    ]
if "pipeline_ran" not in st.session_state:
    st.session_state.pipeline_ran = False

# ---- Job Search Interface ----
st.title("Job Helper")
st.write("Enter parameters to run the pipeline:")

col1, col2, col3 = st.columns(3)
keywords = col1.text_input("Job title, skill, or company", "data scientist")
location = col2.text_input("Location", "New York, USA")
exp_options = ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
experience_level = col3.multiselect("Experience Level", options=exp_options)

col4, col5, col6 = st.columns(3)
remote_options = ["Onsite", "Remote", "Hybrid"]
remote = col4.multiselect("Remote Options", options=remote_options)
pages_to_scrape = col5.number_input("Pages to Scrape", value=1, min_value=1)
col6.empty()

with st.expander("Advanced Filters"):
    sortby_options = ["Relevance", "Date Posted"]
    sortby = st.selectbox("Sort By", options=sortby_options)
    date_posted_options = ["Any time", "Past 24 hours", "Past week", "Past month"]
    date_posted = st.selectbox("Date Posted", options=date_posted_options)
    easy_apply = st.checkbox("Easy Apply Only")
    benefits_options = [
        "Medical insurance", "Vision insurance", "Dental insurance", "401k",
        "Pension plan", "Paid maternity leave", "Paid paternity leave",
        "Commuter benefits", "Student loan assistance", "Tuition assistance",
        "Disability insurance"
    ]
    benefits = st.multiselect("Benefits", options=benefits_options)

if st.button("Run Pipeline"):
    with st.spinner("Running pipeline..."):
        fig_hard, fig_soft = run_pipeline(
            keywords, location, pages_to_scrape,
            experience_level, remote, sortby, date_posted, easy_apply, benefits
        )
        st.session_state.fig_hard = fig_hard
        st.session_state.fig_soft = fig_soft
        st.session_state.pipeline_ran = True

if st.session_state.get("pipeline_ran"):
    st.plotly_chart(st.session_state.fig_hard)
    st.plotly_chart(st.session_state.fig_soft)

st.markdown("---")

# ---- Integrated Chat Section ----
with st.expander("Interactive Chat with JobHelper", expanded=True):

    for msg in st.session_state.conversation_history[-20:]:
        st.chat_message(msg["role"]).write(msg["content"])

    def process_chat():
        user_msg = st.session_state.get("chat_input")
        if user_msg:
            st.session_state.conversation_history.append({"role": "user", "content": user_msg})
            with st.spinner("Processing..."):
                answer, _ = answer_user_question(
                    user_msg, conversation_history=st.session_state.conversation_history
                )
            st.session_state.conversation_history.append({"role": "assistant", "content": answer})
            if "chat_input" in st.session_state:
                del st.session_state["chat_input"]

    st.chat_input("Type your message here...", key="chat_input", on_submit=process_chat)
