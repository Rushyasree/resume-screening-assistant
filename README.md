# 🧠 AI Resume Classifier

This project is an AI-powered resume screening assistant that allows users to upload resumes in PDF format and automatically classifies them into job roles (e.g., Data Science, Software Development, HR, etc.) using AI/ML models.

> 🔍 Built with IBM watsonx.ai and enhanced with drag & drop file upload, classification history, export, filtering, and dark mode.

---

## 🚀 Features

- 📂 Drag & Drop resume upload (PDF only)
- 🤖 AI classification of resumes into job roles
- 🌙 Dark mode toggle for better readability
- 🕘 Classification history with timestamps
- 🔍 Search and 📅 filter by filename/date
- 📥 Export classification history to CSV
- 🧾 Download previously uploaded resumes
- 📌 Sort by name/date (ascending/descending)
- 🧹 Clear history with one click
- ✅ Success/Error notifications

---

## 🛠️ Tech Stack

- Frontend: HTML5, CSS3, JavaScript
- Backend: Flask (Python)
- Resume Parsing: PDF text extraction
- AI/ML: IBM watsonx.ai for classification
- Hosting: Run locally

---

## 📦 Installation

1. Clone the repo

```bash
git clone https://github.com/your-username/resume-screening-assistant.git
cd resume-screening-assistant

2.Setup virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3.Install dependencies

```bash
pip install -r requirements.txt

4.Run the backend:

```bash
cd backend
python main.py

5.Open the frontend:

```bash
Open index.html from the frontend folder in your browser
(or go to http://localhost:5000 if served via Flask)

📁 Folder Structure

resume-screening-assistant/
│
├── backend/
│   ├── main.py
│   ├── resume_parser.py
│   ├── classifier.py
│   └── prompts/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── data/
├── README.md
├── .gitignore
└── requirements.txt


🧠 Powered By
IBM watsonx.ai – AI model used for classification
OpenAI (ChatGPT) – Ideation & logic development support

📃 License
This project is licensed under the MIT License.

✨ Contributor
Rushya Sree (Project Lead)