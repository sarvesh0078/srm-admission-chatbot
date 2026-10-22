import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chatbot import Chatbot  # noqa: E402

bot = Chatbot(use_embeddings=False)


def ask(q, ctx=None):
    return bot.respond(q, ctx if ctx is not None else {})


def test_greeting():
    r = ask("Hi, I need admission information.")
    assert r.intent == "welcome" and "Admission Assistant" in r.text


def test_courses():
    r = ask("What courses are available at Ramapuram?")
    assert r.intent == "courses" and "B.Tech" in r.text and "MBA" in r.text


def test_btech_eligibility():
    r = ask("What are the B.Tech eligibility criteria?")
    assert r.intent == "eligibility" and r.course == "btech" and "10+2" in r.text


def test_fee_cse_never_invents_numbers():
    r = ask("What is the fee for CSE?")
    assert r.intent == "fees" and r.course == "btech"
    assert not re.search(r"(₹|rs\.?\s?\d|inr|lakh|\d{4,})", r.text, re.I)
    assert "srmist.edu.in" in r.text


def test_varied_fee_wording_and_typos():
    assert ask("How much does engineering cost?").intent == "fees"
    assert ask("Tell me the fees for CSE").course == "btech"
    assert ask("enginering fees").course == "btech"
    assert ask("scholorship available?").intent == "scholarships"


def test_apply_documents_scholarship_sports_contact():
    assert ask("How do I apply for admission?").intent == "admission_process"
    assert ask("What documents should I bring?").intent == "documents"
    assert ask("Are scholarships available?").intent == "scholarships"
    assert ask("Is there a sports quota?").intent == "sports_quota"
    r = ask("What is the official admissions contact?")
    assert r.intent == "contact" and "srmist.edu.in" in r.text


def test_unrelated_question_falls_back_safely():
    for q in ["Tell me something unrelated to admissions.", "Who won the cricket world cup in 2011 final", "asdfgh"]:
        r = ask(q)
        assert r.intent == "fallback" and "srmist.edu.in" in r.text


def test_follow_up_uses_conversation_context():
    ctx = {}
    assert ask("Tell me about MBA", ctx).course == "mba"
    r = ask("what is the eligibility?", ctx)
    assert r.intent == "eligibility" and r.course == "mba"


def test_no_phone_numbers_anywhere():
    for t in bot.topics:
        assert not re.search(r"\b\d{10}\b|\+91", t["answer"])


def test_knowledge_base_schema():
    kb = json.load(open(Path(__file__).resolve().parents[1] / "knowledge_base.json", encoding="utf-8"))
    for t in kb["topics"]:
        assert t["id"] and t["answer"] and t["keywords"] and t["questions"]
    for c in kb["courses"].values():
        assert c["name"] and c["eligibility"] and "fee" in c
