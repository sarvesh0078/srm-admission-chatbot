"""NLP and response-generation logic for the SRM Ramapuram Admission Assistant.

Matching pipeline
-----------------
1. Normalise text (lower-case, "B.Tech" -> "btech"), drop stop-words, light stemming.
2. Correct spelling mistakes against the knowledge-base vocabulary (difflib).
3. Detect the course mentioned (B.Tech / CSE / MBA ...), also from earlier turns.
4. Score every topic: keyword hits + fuzzy similarity to sample questions
   (+ optional sentence-transformer embeddings).
5. If the best score is below CONFIDENCE_THRESHOLD, return a safe fallback.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher, get_close_matches
from pathlib import Path
from typing import Optional

KB_PATH = Path(__file__).with_name("knowledge_base.json")
OFFICIAL_URL = "https://www.srmist.edu.in/"
CONFIDENCE_THRESHOLD = 0.35
MAX_QUERY_CHARS = 500

SUGGESTED_QUESTIONS = {
    "📚 Courses": "What courses are available at Ramapuram?",
    "✅ Eligibility": "What are the B.Tech eligibility criteria?",
    "💰 Fees": "What is the B.Tech fee?",
    "🎖️ Scholarships": "Are scholarships available?",
    "📄 Documents": "What documents should I bring?",
    "📝 Apply Now": "How do I apply for admission?",
}

VERIFY_NOTE = (
    "\n\n> ℹ️ Admission details change every year. Please verify on the official "
    f"SRMIST website: {OFFICIAL_URL}"
)

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "am", "do", "does", "did",
    "i", "me", "my", "we", "you", "your", "us", "our", "it", "its", "to", "of", "in", "on",
    "at", "for", "from", "with", "by", "and", "or", "but", "if", "so", "this", "that",
    "these", "those", "what", "which", "who", "whom", "how", "when", "where", "why", "can",
    "could", "would", "should", "will", "shall", "may", "might", "please", "tell", "give",
    "show", "need", "want", "know", "get", "have", "has", "had", "there", "about", "any",
    "some", "something", "also", "just", "like", "kindly", "into", "than", "then",
}


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
def _stem(tok: str) -> str:
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith(("ss", "us", "is")):
        return tok[:-1]
    return tok


def _tokens(text: str, drop_stop: bool = True) -> list[str]:
    text = text.lower()
    text = re.sub(r"[.\-]", "", text)          # b.tech / b-tech -> btech
    words = re.findall(r"[a-z0-9]+", text)
    if drop_stop:
        words = [w for w in words if w not in STOPWORDS]
    return [_stem(w) for w in words]


def _similarity(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    jac = len(set(a) & set(b)) / len(set(a) | set(b))
    seq = SequenceMatcher(None, " ".join(a), " ".join(b)).ratio()
    return 0.5 * jac + 0.5 * seq


@dataclass
class Response:
    text: str
    intent: str
    confidence: float
    course: Optional[str] = None


# --------------------------------------------------------------------------- #
# Chatbot
# --------------------------------------------------------------------------- #
class Chatbot:
    def __init__(self, kb_path: Path | str = KB_PATH, use_embeddings: Optional[bool] = None):
        with open(kb_path, encoding="utf-8") as f:
            self.kb = json.load(f)
        self.meta = self.kb["meta"]
        self.courses: dict = self.kb["courses"]
        self.topics: list[dict] = self.kb["topics"]
        self.by_id = {t["id"]: t for t in self.topics}
        self._prepare()
        self._model = None
        if use_embeddings is None:
            use_embeddings = os.getenv("SRM_USE_EMBEDDINGS") == "1"
        if use_embeddings:
            self._load_embeddings()

    # ----- preparation ---------------------------------------------------- #
    def _prepare(self) -> None:
        vocab: set[str] = set()
        for t in self.topics:
            t["_kw"] = {" ".join(_tokens(k)) for k in t.get("keywords", [])} - {""}
            t["_q"] = [_tokens(q) for q in t.get("questions", [])]
            for k in t["_kw"]:
                vocab.update(k.split())
            for q in t["_q"]:
                vocab.update(q)
        self.alias_to_course: dict[str, str] = {}
        for key, c in self.courses.items():
            for alias in c.get("aliases", []) + list(c.get("branches", {})):
                norm = " ".join(_tokens(alias))
                if norm:
                    self.alias_to_course[norm] = key
                    vocab.update(norm.split())
        self.aliases_sorted = sorted(self.alias_to_course, key=len, reverse=True)
        self.vocab = vocab
        self.vocab_list = sorted(vocab)

    def _load_embeddings(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer, util  # type: ignore

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._util = util
            for t in self.topics:
                t["_emb"] = self._model.encode(t["questions"], convert_to_tensor=True)
        except Exception as exc:  # library missing or model not downloadable
            print(f"[chatbot] Embeddings disabled ({exc}); using fuzzy matching only.")
            self._model = None

    # ----- NLP steps ------------------------------------------------------ #
    def _correct(self, toks: list[str]) -> list[str]:
        out = []
        for tok in toks:
            if tok in self.vocab or len(tok) < 4 or tok.isdigit():
                out.append(tok)
                continue
            match = get_close_matches(tok, self.vocab_list, n=1, cutoff=0.8)
            out.append(match[0] if match else tok)
        return out

    def _detect_course(self, toks: list[str]) -> tuple[Optional[str], Optional[str]]:
        padded = " " + " ".join(toks) + " "
        for alias in self.aliases_sorted:
            if f" {alias} " in padded:
                return self.alias_to_course[alias], alias
        return None, None

    def _semantic(self, query: str) -> dict[str, float]:
        if self._model is None:
            return {}
        q = self._model.encode(query, convert_to_tensor=True)
        scores = {}
        for t in self.topics:
            raw = float(self._util.cos_sim(q, t["_emb"]).max())
            scores[t["id"]] = max(0.0, min(1.0, (raw - 0.3) / 0.5))
        return scores

    def _score_all(self, query: str, toks: list[str]) -> dict[str, float]:
        padded = " " + " ".join(toks) + " "
        semantic = self._semantic(query)
        scores = {}
        for t in self.topics:
            hits = sum(1 for k in t["_kw"] if f" {k} " in padded)
            kw = 1 - 0.35 ** hits if hits else 0.0
            sim = max((_similarity(toks, q) for q in t["_q"]), default=0.0)
            sem = semantic.get(t["id"], 0.0)
            score = 0.65 * kw + 0.35 * max(sim, sem)
            if sem > 0.6:
                score = max(score, 0.9 * sem)
            scores[t["id"]] = score
        return scores

    # ----- response composition ------------------------------------------ #
    def welcome(self) -> str:
        return self.by_id["welcome"]["answer"]

    def _compose(self, topic: dict, course: Optional[str], alias: Optional[str]) -> str:
        dynamic = topic.get("dynamic")
        if not dynamic or not course:
            if dynamic == "courses":
                return topic["answer"]
            return topic["answer"]
        c = self.courses[course]
        branch = c.get("branches", {}).get(alias or "")
        intro = f"You asked about **{branch}**, a branch under **{c['name']}**.\n\n" if branch else ""
        head = f"**{c['name']}** · {c['level']} · {c['duration']}\n\n"
        if dynamic == "eligibility":
            return (intro + head + f"**Eligibility:** {c['eligibility']}\n\n"
                    f"**Minimum marks:** {c['minimum_marks']}\n\n**Entrance / selection:** {c['entrance']}")
        if dynamic == "fees":
            fee = c.get("fee")
            if fee:
                body = f"**Fee (as recorded in this knowledge base, unverified):** {fee}\n\n"
            else:
                body = ("I don't have a **verified fee figure** for this programme, so I won't guess one.\n\n")
            return intro + head + body + topic["answer"].split("\n\n", 1)[0] + (
                "\n\nPlease check the official fee structure for your course and admission year.")
        # courses
        spec = f"**Specialisations:** {c['specialisations']}\n\n" if c.get("specialisations") else ""
        fee = c.get("fee") or ("Not verified here. See the official fee structure / admission brochure: "
                               + self.meta.get("official_brochure", OFFICIAL_URL))
        return (intro + head + f"**Eligibility:** {c['eligibility']}\n\n**Entrance / selection:** {c['entrance']}\n\n"
                f"{spec}**Fee:** {fee}\n\n"
                "Ask me about eligibility details, scholarships or the admission process.")

    def _fallback(self, query: str = "") -> Response:
        text = (
            "I'm sorry, I couldn't find a confident answer to that. 🤔 I can only help with "
            "SRM Ramapuram admissions.\n\n"
            "Try asking about: **Courses**, **Eligibility**, **Fees**, **Scholarships**, **Documents**, "
            "**Admission process**, **Sports quota**, **Placements**, **Rules** or **Contact details**.\n\n"
            f"For anything else, please contact the admissions office via the official website: {OFFICIAL_URL}"
        )
        return Response(text, "fallback", 0.0)

    def respond(self, query: str, ctx: Optional[dict] = None) -> Response:
        """Answer a query. `ctx` (a dict) carries conversation context between turns."""
        ctx = ctx if ctx is not None else {}
        query = (query or "").strip()[:MAX_QUERY_CHARS]
        toks = self._correct(_tokens(query))
        if not toks:
            return self._fallback(query)

        course, alias = self._detect_course(toks)
        scores = self._score_all(query, toks)
        topic_id, score = max(scores.items(), key=lambda kv: kv[1])
        if course and score < CONFIDENCE_THRESHOLD:       # e.g. just "tell me about MBA"
            topic_id, score = "courses", 0.5
        if score < CONFIDENCE_THRESHOLD:
            return self._fallback(query)

        topic = self.by_id[topic_id]
        note = ""
        if topic.get("dynamic") and not course and ctx.get("course") and len(toks) <= 5:
            course = ctx["course"]                          # follow-up question
            note = f"_(Continuing with {self.courses[course]['name']}; ask about another course any time.)_\n\n"

        text = note + self._compose(topic, course, alias)
        if topic.get("verify", True):
            text += VERIFY_NOTE
        if course:
            ctx["course"] = course
        ctx["intent"] = topic_id
        return Response(text, topic_id, round(score, 2), course)

    # ----- terminal mode (kept from the original run_chat idea) ---------- #
    def run_chat(self) -> None:
        print(self.welcome().replace("**", "").replace("_", ""))
        ctx: dict = {}
        while True:
            try:
                q = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in {"quit", "exit"}:
                break
            r = self.respond(q, ctx)
            print(f"\nBot [{r.intent}, {r.confidence}]: {r.text}")


if __name__ == "__main__":
    Chatbot().run_chat()
