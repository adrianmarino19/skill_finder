import streamlit as st
from streamlit_chat import message
from backend import run_pipeline, answer_user_question

# -------------------
# Midnight Scout Theme
# -------------------
st.set_page_config(
    page_title="Job Helper",
    page_icon="🎒",  # Boy scout-inspired icon
    layout="wide",
)

# Inject CSS for a black background with dark brown and light brown accents.
st.markdown(
    """
    <style>
    :root {
        --primary-color: #4E342E;           /* Dark brown for buttons */
        --background-color: #000000;        /* Black background */
        --secondary-background-color: #333333; /* Dark gray for header/containers */
        --text-color: #BDB76B;              /* Light brown text for contrast */
    }

    div[data-testid="stAppViewContainer"] {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    div[data-testid="stHeader"] {
        background-color: var(--secondary-background-color);
    }

    .stButton>button {
        background-color: var(--primary-color) !important;
        color: var(--text-color) !important;
        border: none;
    }
    .stButton>button:hover {
        filter: brightness(1.15);
    }

    input, .stTextInput input, .stMultiSelect>div>div>div {
        background-color: #222222 !important;
        color: var(--text-color) !important;
        border: 1px solid #555555;
    }

    /* Override focus/hover outlines for textboxes */
    input:focus, .stTextInput input:focus, .stMultiSelect>div>div>div:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 1px var(--primary-color) !important;
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

with st.expander("Interactive Chat with JobHelper", expanded=True):
    # Display chat messages with an assistant avatar icon.
    for msg in st.session_state.conversation_history[-20:]:
        if msg["role"] == "assistant":
            st.chat_message("assistant", avatar="🎒").write(msg["content"])
        else:
            st.chat_message("user").write(msg["content"])

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
