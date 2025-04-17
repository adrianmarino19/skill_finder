# SkillFinder 🔭

[![Demo](https://img.shields.io/badge/Demo-SkillFinder_Streamlit-blue)](https://skillfinder.streamlit.app/)

SkillFinder is an interactive Streamlit application that helps you discover in-demand skills by analyzing job postings from LinkedIn. Check it out [here](https://skillfinder.streamlit.app/)! 

With data visualizations and an interactive chat interface, SkillFinder empowers you to:

- **Discover In-Demand Skills:** Analyze job postings to extract top hard and soft skills.
- **Compare Job Requirements:** Visualize trends across different roles and industries.
- **Interactive Chat:** Ask questions about the job market or specific postings and receive data-driven insights.

## Features

- **Job Scraping Pipeline:**  
  - Scrapes job postings based on user-defined keywords, location, experience level, remote options, and more.
  - Fetches and cleans job descriptions using BeautifulSoup and custom stopword removal.
- **Skills Extraction:**  
  - Leverages a large language model (via `genai.Client`) to extract hard and soft skills from job descriptions.
  - Displays interactive Plotly bar charts for the most frequent skills.
- **Interactive Chat Interface:**  
  - Chat with SkillFinder for further insights or to execute SQL queries on job data.
  - Uses conversation history for context-aware responses.
- **Customizable Filters:**  
  - Advanced filtering options such as sort order, date posted, and benefits to refine job searches.

## Installation

### Prerequisites

- Python 3.7+
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/python/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- Other dependencies as listed in the `requirements.txt` file.

### Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/adrianmarino19/skill_finder.git
   cd skill_finder

2. **Create a Virtual Environment (Recommended)**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use: venv\Scripts\activate

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt

4. **Configure Environment Variables:**

    ```bash
    GEM_KEY=your_genai_api_key_here
