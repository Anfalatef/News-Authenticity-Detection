
# 📰 News Authenticity Detection
### AI-Powered News Verification & Bias Analysis | Graduation Project

An Artificial Intelligence graduation project that analyzes user-submitted news text, assesses its authenticity, retrieves supporting sources, and estimates author bias using NLP and Retrieval-Augmented Generation (RAG).

---

## 🎯 Project Overview

News Authenticity Detection is an AI-powered web application developed to help users evaluate the credibility of news content.

Users submit news text through a web interface. The system analyzes the content and provides an AI-generated authenticity assessment, supporting information sources, and an estimated author bias percentage.

The project combines Natural Language Processing (NLP), Retrieval-Augmented Generation (RAG), Python backend services, and a React/TypeScript frontend.

## ✨ Key Features

### 📰 News Authenticity Assessment
- Accepts news text submitted by the user.
- Analyzes the content to assess whether the news is authentic or false.
- Presents the AI-generated assessment through the web interface.

### 🔍 Evidence-Based Verification
- Retrieves relevant information to support the news assessment.
- Provides supporting sources for users to review.
- Helps users examine the evidence behind the generated result.

### ⚖️ Author Bias Analysis
- Analyzes potential bias reflected in the submitted news text.
- Displays an estimated author bias percentage.
- Provides an additional perspective on the article's content.

### 🤖 NLP & RAG Integration
- Uses Natural Language Processing for news content analysis.
- Incorporates Retrieval-Augmented Generation to support evidence-informed assessments.
- Connects information retrieval with AI-powered analysis.

### 💻 Interactive Web Interface
- Built using React and TypeScript.
- Allows users to submit news text and review analysis results.
- Communicates with Python backend APIs.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python, TypeScript |
| Artificial Intelligence | NLP, RAG |
| Backend | Python APIs, FastAPI |
| Frontend | React, TypeScript |
| Information Retrieval | Search and retrieval components |
| Development | Modular application architecture |

---

## 🔄 How It Works

1. **News Submission:** The user enters the text of a news article.
2. **Content Processing:** The backend processes the submitted text.
3. **Information Retrieval:** The system retrieves relevant supporting information.
4. **AI Analysis:** NLP and RAG components support the authenticity and bias assessment.
5. **Results:** The interface displays the authenticity assessment, supporting sources, and estimated author bias percentage.

---

## 📁 Project Structure

```text
News-Authenticity-Detection/
├── app/                # Backend APIs, news processing, retrieval and RAG
├── ui/                 # React and TypeScript frontend
├── scripts/            # Utility scripts
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

---

## ⚙️ Local Setup

### Backend

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables locally.

### Frontend

Navigate to the frontend directory:

```bash
cd ui
npm install
```

Review the available scripts and configuration before starting the backend and frontend services.

**Note:** The public repository is a cleaned distribution. Local databases, search indexes, environment files, logs, and credentials are excluded. The cleaned version has not been fully tested and may require additional configuration, data ingestion, and API credentials.

---

## 🔐 Privacy & Responsible AI

- API credentials and sensitive information should not be committed.
- News authenticity results are AI-generated assessments and should not be treated as guaranteed facts.
- Author bias percentages are model-generated estimates, not definitive measurements.
- Users should independently review supporting sources when verifying news.

---

## 🚀 Future Improvements

- Evaluate authenticity classification using labeled news datasets.
- Improve retrieval quality and source relevance.
- Validate bias estimates against clearly defined evaluation criteria.
- Expand automated testing and error handling.
- Improve deployment documentation.

---

## 👩‍💻 Project Information

**Project:** News Authenticity Detection  
**Type:** Artificial Intelligence Graduation Project  
**University:** Al-Zaytoonah University of Jordan  
**Developer:** Anfal Atef Abu Samhadana

---

## 📫 Contact

**GitHub:** [Anfalatef](https://github.com/Anfalatef)

**LinkedIn:** [Anfal Abu Samhadana](https://www.linkedin.com/in/anfal-a-b11231308/)

---

⭐ Thanks for exploring my graduation project!
