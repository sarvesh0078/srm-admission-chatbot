"""Streamlit front-end for the SRM Ramapuram Admission Assistant."""
import streamlit as st

from chatbot import OFFICIAL_URL, SUGGESTED_QUESTIONS, Chatbot

st.set_page_config(
    page_title="SRM Ramapuram Admission Assistant",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

NAVY, GOLD, LIGHT = "#0B2E59", "#F2A900", "#F4F7FB"
st.markdown(
    f"""
<style>
html, body, [class*="css"] {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
.stApp {{ background: {LIGHT}; }}
.hero {{ background: linear-gradient(135deg, {NAVY}, #1B4F9C); color: #fff; padding: 1.2rem 1.4rem;
        border-radius: 14px; border-bottom: 4px solid {GOLD}; margin-bottom: 1rem; }}
.hero h1 {{ color: #fff; font-size: 1.6rem; margin: 0; padding: 0; }}
.hero p {{ margin: .2rem 0 0; opacity: .9; font-size: 1rem; }}
[data-testid="stChatMessage"] {{ background: #fff; border-radius: 12px; padding: .8rem 1rem;
        box-shadow: 0 1px 4px rgba(11,46,89,.10); margin-bottom: .5rem; }}
.stButton > button {{ width: 100%; border-radius: 20px; border: 1px solid {NAVY}; color: {NAVY};
        background: #fff; font-weight: 600; }}
.stButton > button:hover {{ background: {NAVY}; color: #fff; border-color: {GOLD}; }}
[data-testid="stSidebar"] {{ background: #E8EEF7; }}
.disclaimer {{ font-size: .78rem; color: #555; }}
@media (max-width: 640px) {{ .hero h1 {{ font-size: 1.25rem; }} }}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_bot() -> Chatbot:
    return Chatbot()


bot = get_bot()


def reset_chat() -> None:
    st.session_state.messages = [{"role": "assistant", "content": bot.welcome()}]
    st.session_state.ctx = {}
    st.session_state.pending = None
    st.session_state.last = None


def ask(question: str) -> None:
    st.session_state.pending = question


if "messages" not in st.session_state:
    reset_chat()

# ------------------------------- Sidebar ---------------------------------- #
with st.sidebar:
    st.markdown("### 🎓 Admission Topics")
    for label, question in SUGGESTED_QUESTIONS.items():
        st.button(label, key=f"side_{label}", on_click=ask, args=(question,))
    st.button("🏅 Sports Quota", key="side_sports", on_click=ask, args=("Is there a sports quota?",))
    st.button("💼 Placements", key="side_place", on_click=ask, args=("How are the placements?",))
    st.button("📞 Contact", key="side_contact", on_click=ask, args=("What is the official admissions contact?",))
    st.divider()
    st.markdown("### 🔗 Official Links")
    st.markdown(f"- [SRMIST Official Website]({OFFICIAL_URL})")
    st.divider()
    st.button("🗑️ Clear Chat", key="clear", on_click=reset_chat)
    show_debug = st.checkbox("Show matching details")
    st.markdown(
        '<p class="disclaimer">This is an <b>unofficial</b> student-support assistant and not an official '
        "SRMIST service. Always confirm fees, eligibility, dates and contacts on the official website.</p>",
        unsafe_allow_html=True,
    )

# ------------------------------- Main page -------------------------------- #
st.markdown(
    '<div class="hero"><h1>🎓 SRM Ramapuram Admission Assistant</h1>'
    "<p>Your guide to courses and admissions</p></div>",
    unsafe_allow_html=True,
)

st.caption("Quick questions")
items = list(SUGGESTED_QUESTIONS.items())
for row in (items[:3], items[3:]):
    cols = st.columns(3)
    for col, (label, question) in zip(cols, row):
        col.button(label, key=f"main_{label}", on_click=ask, args=(question,))

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🎓"):
        st.markdown(msg["content"])

typed = st.chat_input("Ask about courses, fees, eligibility, scholarships...")
query = typed or st.session_state.pending
st.session_state.pending = None

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(query)
    response = bot.respond(query, st.session_state.ctx)
    st.session_state.last = (response.intent, response.confidence, response.course)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    with st.chat_message("assistant", avatar="🎓"):
        st.markdown(response.text)

if show_debug and st.session_state.get("last"):
    intent, conf, course = st.session_state.last
    st.sidebar.info(f"Intent: **{intent}** · Confidence: **{conf}** · Course: **{course}**")
