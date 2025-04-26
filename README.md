# SkillFinder 🔭

SkillFinder is an interactive Streamlit application that helps you discover in-demand skills by analyzing job postings from LinkedIn. Check it out [here](https://skillfinder.streamlit.app/)! 

With data visualizations and an interactive chat interface, SkillFinder empowers you to:

- **Discover In-Demand Skills:** Analyze job postings to extract top hard and soft skills.
- **Compare Job Requirements:** Visualize trends across different roles and industries.
- **Interactive Chat:** Ask questions about the job market or specific postings and receive data-driven insights.

<br>

## Data Flow & Features

1. User inputs job search filters/parameters (job title, location, remote, etc) in Streamlit UI.
2. Backend scrapes LinkedIn job listings.
3. Job descriptions are cleaned and processed.
4. large language model (via Google's Gemini 2.0 Flash) to extract hard and soft skills from job descriptions.
5. Skills are stored in SQLite database.
6. Visualizations are generated and displayed.
7. Chat interface enables natural language querying for the specific scraped data (using RAG and LLM).

 
<br>

## 🛠️ Tech Stack

| Component          | Technology                               |
|--------------------|------------------------------------------|
| **Frontend**       | Streamlit, Plotly, Streamlit-chat        |
| **Backend**        | Python, NLTK, Google Generative AI (Gemini 2.0) |
| **Web Scraping**   | BeautifulSoup4, Requests                 |
| **Database**       | SQLite (in-memory)                       |
| **API**            | FastAPI, Pydantic                        |
| **Data Processing**| Pandas, Collections (Counter)            |
| **Environment**    | Python 3.7+, python-dotenv               |

<br>

## 🛤️ Architecture

- **Frontend (Streamlit):**  
  `frontend.py` provides the user interface for inputting search parameters, displaying visualizations, and hosting the interactive chat.

- **Backend Processing:**  
  `backend.py` contains core logic for:
  - Web scraping LinkedIn job listings
  - NLP text cleaning using NLTK
  - AI-powered skill extraction via Gemini 2.0 Flash
  - Database operations with SQLite
  - Visualization generation with Plotly

- **API Layer:**  
  `main.py` implements a FastAPI server with endpoints for:
  - `/scrape-jobs`: Job listing extraction
  - `/extract-skills`: Skill identification from descriptions
  - `/pipeline`: Full end-to-end processing

- **App Entry Point:**  
  `app.py` provides a simplified interface to the backend pipeline for direct application usage.

<br>

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
