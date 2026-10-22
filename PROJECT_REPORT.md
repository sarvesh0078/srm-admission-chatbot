# Project Report: SRM Ramapuram Admission Assistant

## 1. Overview
A web-based chatbot that helps prospective students and parents understand courses, eligibility, fees, scholarships, documents and the admission process for SRM Institute of Science and Technology, Ramapuram Campus, Chennai. It is an unofficial, informational tool.

## 2. Objectives
- Give instant, consistent answers to common admission questions.
- Handle varied wording and spelling mistakes.
- Avoid misinformation: never invent fees, dates, scores, contact numbers or scholarship amounts.
- Provide a clean, mobile-friendly interface.

## 3. Methodology
1. **Knowledge base:** admission content stored in editable JSON (`courses` and `topics`).
2. **Pre-processing:** lower-casing, normalising course names (B.Tech → btech), stop-word removal, light stemming.
3. **Spelling correction:** fuzzy matching (difflib) against the knowledge-base vocabulary.
4. **Course detection:** alias matching (e.g. CSE, engineering → B.Tech) for course-specific answers.
5. **Scoring:** keyword hits combined with similarity to sample questions; optional sentence-transformer embeddings.
6. **Confidence threshold (0.35):** below it, the bot returns a safe fallback and points to the official website.
7. **Context:** the last course is remembered so follow-ups work without restarting.
8. **UI:** Streamlit chat components, sidebar topics, suggested-question buttons, session-state history, clear-chat button.
9. **Testing:** automated pytest cases covering the required questions, typos, follow-ups and safety checks.

## 4. Features
Welcome message, course information, eligibility, fee guidance, admission process, document checklist, scholarships, sports quota, placements, rules, contact details, follow-ups, suggested questions, fallback handling, chat history, reset button, themed responsive UI.

## 5. Limitations
- Data is unverified and must be confirmed against official SRMIST sources each year.
- Fees, dates and contact numbers are intentionally not provided.
- Keyword/fuzzy matching can misread very long or ambiguous queries.
- Single-language (English) and no persistent storage across sessions.
- Unofficial; not integrated with the university's application portal.

## 6. Future Enhancements
- Add verified fee tables, dates and contacts after official confirmation.
- Embedding-based retrieval by default, or an LLM with retrieval over official documents.
- Tamil and Hindi support; voice input.
- Admin page to edit the knowledge base; analytics on unanswered questions.
- Human hand-off (email / call-back request) and deployment with the university's authorisation.
