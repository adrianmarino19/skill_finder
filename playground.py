## OPTION 1

import streamlit as st
from backend import run_pipeline, answer_user_question

# Set page configuration.
st.set_page_config(page_title="Job Helper", layout="wide")

# Initialize session state for conversation history.
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [
        {"role": "assistant", "content": "Hello! I am Job Helper. How can I assist you with your job search today?"}
    ]

# Main Job Search UI at the top
st.title("Job Helper")
st.write("Enter parameters to run the pipeline:")

# Job Search Parameters
col1, col2, col3 = st.columns(3)
keywords = col1.text_input("Job title, skill, or company", "software engineer")
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
    with st.spinner("Running pipeline, please wait..."):
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

# Integrated Chat Section (placed below the job search interface)
with st.expander("Interactive Chat with Job Helper", expanded=True):
    chat_input = st.chat_input("Type your message here:")
    if chat_input:
        st.session_state.conversation_history.append({"role": "user", "content": chat_input})
        with st.spinner("Processing..."):
            answer, _ = answer_user_question(chat_input)
        st.session_state.conversation_history.append({"role": "assistant", "content": answer})

    # Display the last 20 messages
    for msg in st.session_state.conversation_history[-20:]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

# ---- Integrated Chat Section with Input at the Bottom ----
with st.expander("Interactive Chat with JobHelper", expanded=True):
    for msg in st.session_state.conversation_history[-20:]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    # Chat input appears below the chat messages.
    if st.button("Send", key="send_bottom"):
        if chat_input:
            st.session_state.conversation_history.append({"role": "user", "content": chat_input})
            with st.spinner("Processing..."):
                answer, _ = answer_user_question(chat_input)
            st.session_state.conversation_history.append({"role": "assistant", "content": answer})
            st.experimental_rerun()

### OPTION 2

# import streamlit as st
# from backend import run_pipeline, answer_user_question

# # Set page configuration.
# st.set_page_config(page_title="Job Helper", layout="wide")

# # Initialize session state for conversation and pipeline state.
# if "conversation_history" not in st.session_state:
#     st.session_state.conversation_history = [
#         {"role": "assistant", "content": "Hello! I am Job Helper. How can I assist you with your job search today?"}
#     ]
# if "pipeline_ran" not in st.session_state:
#     st.session_state.pipeline_ran = False

# # ---- Job Search Interface ----
# st.title("Job Helper")
# st.write("Enter parameters to run the pipeline:")

# col1, col2, col3 = st.columns(3)
# keywords = col1.text_input("Job title, skill, or company", "software engineer")
# location = col2.text_input("Location", "New York, USA")
# exp_options = ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
# experience_level = col3.multiselect("Experience Level", options=exp_options)

# col4, col5, col6 = st.columns(3)
# remote_options = ["Onsite", "Remote", "Hybrid"]
# remote = col4.multiselect("Remote Options", options=remote_options)
# pages_to_scrape = col5.number_input("Pages to Scrape", value=1, min_value=1)
# col6.empty()

# with st.expander("Advanced Filters"):
#     sortby_options = ["Relevance", "Date Posted"]
#     sortby = st.selectbox("Sort By", options=sortby_options)
#     date_posted_options = ["Any time", "Past 24 hours", "Past week", "Past month"]
#     date_posted = st.selectbox("Date Posted", options=date_posted_options)
#     easy_apply = st.checkbox("Easy Apply Only")
#     benefits_options = [
#         "Medical insurance", "Vision insurance", "Dental insurance", "401k",
#         "Pension plan", "Paid maternity leave", "Paid paternity leave",
#         "Commuter benefits", "Student loan assistance", "Tuition assistance",
#         "Disability insurance"
#     ]
#     benefits = st.multiselect("Benefits", options=benefits_options)

# if st.button("Run Pipeline"):
#     with st.spinner("Running pipeline, please wait..."):
#         fig_hard, fig_soft = run_pipeline(
#             keywords, location, pages_to_scrape,
#             experience_level, remote, sortby, date_posted, easy_apply, benefits
#         )
#         st.session_state.fig_hard = fig_hard
#         st.session_state.fig_soft = fig_soft
#         st.session_state.pipeline_ran = True

# if st.session_state.get("pipeline_ran"):
#     st.plotly_chart(st.session_state.fig_hard)
#     st.plotly_chart(st.session_state.fig_soft)

# st.markdown("---")

# # ---- Integrated Chat Section with Input at the Bottom ----
# with st.expander("Interactive Chat with JobHelper", expanded=True):
#     for msg in st.session_state.conversation_history[-20:]:
#         if msg["role"] == "user":
#             st.chat_message("user").write(msg["content"])
#         else:
#             st.chat_message("assistant").write(msg["content"])

#     # Chat input appears below the chat messages.
#     chat_input = st.text_input("Type your message here...", key="chat_input_bottom")
#     if st.button("Send", key="send_bottom"):
#         if chat_input:
#             st.session_state.conversation_history.append({"role": "user", "content": chat_input})
#             with st.spinner("Processing..."):
#                 answer, _ = answer_user_question(chat_input)
#             st.session_state.conversation_history.append({"role": "assistant", "content": answer})
#             st.experimental_rerun()
