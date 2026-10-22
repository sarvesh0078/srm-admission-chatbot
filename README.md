# SRM Ramapuram Admission Assistant

A Streamlit chatbot that answers admission questions for SRM Institute of Science and Technology, Ramapuram Campus, Chennai.
**Unofficial student-support tool.** All data in `knowledge_base.json` is *unverified* until you confirm it on https://www.srmist.edu.in/ for the current admission year.

## Project structure (save every file exactly like this)
```
srm-admission-chatbot/
├── app.py                 # Streamlit UI
├── chatbot.py             # NLP + response logic
├── knowledge_base.json    # Editable admission data
├── requirements.txt
├── README.md
├── PROJECT_REPORT.md
├── .gitignore
└── tests/
    ├── __init__.py
    └── test_chatbot.py
```

## Install and run
Requires Python 3.9+.

**Windows (PowerShell)**
```
cd srm-admission-chatbot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
**macOS / Linux**
```
cd srm-admission-chatbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Streamlit opens http://localhost:8501 automatically; if not, open it in your browser.

Terminal-only mode: `python chatbot.py`

Optional semantic matching: `pip install sentence-transformers`, then set `SRM_USE_EMBEDDINGS=1`
(Windows: `set SRM_USE_EMBEDDINGS=1`, macOS/Linux: `export SRM_USE_EMBEDDINGS=1`) before `streamlit run app.py`.

## Run the tests
```
pytest -q
```

## Editing the knowledge base
- `courses` → per-programme eligibility, entrance, duration and `fee`. `fee` is `null` on purpose; fill it only with a figure verified on the official site, e.g. `"fee": "₹X per year (verified 2026-27 from official fee page)"`.
- `topics` → each has `keywords` (matching), `questions` (sample phrasings) and `answer` (markdown). Add a new topic by copying an existing block with a unique `id`.
- Restart the app after editing.

## Upload to GitHub
```
git init
git add .
git commit -m "Initial commit: SRM Ramapuram admission chatbot"
git branch -M main
git remote add origin https://github.com/<your-username>/srm-admission-chatbot.git
git push -u origin main
```
(Create the empty repository on github.com first.) Optionally deploy free on Streamlit Community Cloud by selecting the repo and `app.py`.

## Test cases and expected results
| # | Input | Expected |
|---|-------|----------|
| 1 | Hi, I need admission information. | Welcome message with topic list |
| 2 | What courses are available at Ramapuram? | UG/PG programme list |
| 3 | What are the B.Tech eligibility criteria? | B.Tech eligibility, entrance, "verify" note |
| 4 | What is the fee for CSE? | B.Tech/CSE note; says no verified fee; **no invented amount** |
| 5 | How do I apply for admission? | Step-by-step admission process |
| 6 | What documents should I bring? | Document checklist |
| 7 | Are scholarships available? | Scholarship types, no amounts |
| 8 | Is there a sports quota? | Sports quota info and certificates |
| 9 | What is the official admissions contact? | Address + official website, no unverified phone numbers |
| 10 | Tell me something unrelated to admissions. | Safe fallback with suggested topics |
| 11 | "Tell me about MBA" → "what is the eligibility?" | Follow-up answered for MBA |
| 12 | Reload the page / click Clear Chat | History persists in session; Clear Chat resets to welcome message |
