import streamlit as st
import base64
from streamlit_chat import message
from backend import run_pipeline, answer_user_question

def img_to_base64(image_path):
    """Convert an image file to a base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Page config
st.set_page_config(
    page_title="SkillFinder",
    page_icon="🔭",
    layout="wide",
)

# CSS for a larger, curved rectangle icon with a glow effect.
st.markdown(
    """
    <style>
    .cover-glow {
        width: 90%;              /* Make it nearly full-width in the sidebar */
        max-width: 300px;        /* Cap the width so it doesn't become too large on wide screens */
        height: auto;            /* Keep aspect ratio */
        border-radius: 15px;     /* Curved corners */
        margin: 0 auto;          /* Center horizontally */
        display: block;          /* So margin: 0 auto works */
        box-shadow:
            0 0 5px  #1E90FF,
            0 0 10px #1E90FF,
            0 0 15px #1E90FF,
            0 0 20px #1E90FF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

import streamlit as st



# --- SIDEBAR ---
img_base64 = img_to_base64("img/icon1.png")
st.sidebar.markdown(
    f'''
    <div style="text-align: center; padding: 1rem 0;">
        <img src="data:image/png;base64,{img_base64}" class="cover-glow" alt="SkillFinder Icon" />
    </div>
    ''',
    unsafe_allow_html=True
)
st.sidebar.title("About SkillFinder")
st.sidebar.markdown(
    """
- **Discover In-Demand Skills:** Analyze job postings to identify top hard and soft skills.
- **Compare Job Requirements:** Understand trends across roles and industries.3
- **Interactive Chat:** Ask questions and get instant insights.
    """
)

# --- MAIN APP ---
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [
        {"role": "assistant", "content": "Hello! I am SkillFinder. How can I help you?"}
    ]
if "pipeline_ran" not in st.session_state:
    st.session_state.pipeline_ran = False

st.title("SkillFinder🔭")
st.markdown("<br><br>", unsafe_allow_html=True)
st.write("Enter parameters to run the pipeline:")



col1, col2, col3 = st.columns(3)
keywords = col1.text_input("Job title, skill, or company", "Data scientist")
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

with st.expander("Interactive Chat with SkillFinder🔭", expanded=True):
    for msg in st.session_state.conversation_history[-20:]:
        if msg["role"] == "assistant":
            st.chat_message("assistant", avatar="img/icon.png").write(msg["content"])
        else:
            st.chat_message("user").write(msg["content"])

    # st.markdown("<br><br>", unsafe_allow_html=True)

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
