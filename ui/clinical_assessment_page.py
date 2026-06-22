"""
SMART conversational session (Groq-powered).

The patient describes themselves in natural language; Groq extracts the BASE
features. Missing ones are asked for. Then the system derives the engineered
features, runs the model, takes the decision, extracts the rules, and shows
the DECISION TREE. Falls back to a simple Q&A if Groq is unavailable.
"""
import os
import re
import json
import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv اختياري — لا نُسقط التطبيق إذا كان غير مثبّت
    def load_dotenv(*args, **kwargs):
        """Fallback: قراءة .env يدوياً إذا لم تكن مكتبة python-dotenv مثبّتة."""
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if not os.path.exists(path):
            return False
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
            return True
        except Exception:
            return False

from engine.domain_pipeline import domain_pipeline
from groq_api.groq_client import GroqClient

load_dotenv()


def _get_groq_api_key():
    """مصدر مفتاح Groq بترتيب: st.secrets (السحابة) ← .env / متغيّر البيئة (محلي).

    يدعم النشر على Streamlit Cloud (st.secrets) والتشغيل المحلي (.env) معاً.
    """
    # 1) Streamlit Cloud secrets
    try:
        key = st.secrets["GROQ_API_KEY"]
        if key:
            return key
    except Exception:
        pass
    # 2) متغيّر البيئة / ملف .env (load_dotenv حمّله مسبقاً)
    return os.getenv("GROQ_API_KEY")


def _get_groq_client():
    """يُرجع عميل Groq مهيّأً بأحدث مفتاح متاح (يُعيد التهيئة إذا توفّر المفتاح لاحقاً)."""
    global _groq
    if _groq is not None and _groq.is_available:
        return _groq
    key = _get_groq_api_key()
    if key and (_groq is None or not _groq.is_available):
        _groq = GroqClient(api_key=key)
    return _groq


_groq = GroqClient(api_key=_get_groq_api_key())

_COLOR = {"CRITICAL": "#c0392b", "HIGH": "#e74c3c", "MODERATE": "#f39c12", "LOW": "#2ecc71"}

REQUIRED = ["age", "gender", "height_cm", "weight_kg", "smoking_status", "workplace_type"]
OPTIONAL = ["environmental_hazards", "family_history"]
_LABELS_AR = {"age": "العمر", "gender": "الجنس", "height_cm": "الطول", "weight_kg": "الوزن",
              "smoking_status": "حالة التدخين", "workplace_type": "نوع العمل",
              "environmental_hazards": "المخاطر البيئية", "family_history": "التاريخ العائلي"}

_EXTRACT_SYS = (
    "You extract patient profile fields from free text (Arabic or English). "
    "Return ONLY a JSON object with these keys (use null if not mentioned): "
    "age (number), gender ('male'|'female'), height_cm (number), weight_kg (number), "
    "smoking_status ('non-smoker'|'ex-smoker'|'current smoker'), "
    "workplace_type ('office'|'factory'), "
    "environmental_hazards (array of any of: 'stress','pollution','noise','dust','chemicals','shift work'), "
    "family_history (true|false). Return JSON only, no prose."
)


def _normalize(data: dict) -> dict:
    out = {}
    for k, v in data.items():
        if v in (None, "", []):
            continue
        if k == "smoking_status":
            s = str(v).lower()
            if any(w in s for w in ["non", "never", "غير", "ما يدخن", "لا يدخن"]):
                v = "non-smoker"
            elif any(w in s for w in ["ex", "former", "quit", "سابق", "أقلع", "اقلع"]):
                v = "ex-smoker"
            elif any(w in s for w in ["current", "smok", "يدخن", "مدخن"]):
                v = "current smoker"
            else:
                continue
        elif k == "gender":
            s = str(v).lower()
            v = "female" if ("female" in s or "أنثى" in s or "انثى" in s) else \
                ("male" if ("male" in s or "ذكر" in s) else None)
            if v is None:
                continue
        elif k == "workplace_type":
            s = str(v).lower()
            v = "factory" if ("factory" in s or "مصنع" in s) else "office"
        elif k == "family_history":
            v = v if isinstance(v, bool) else (str(v).lower() in ("true", "yes", "1", "نعم", "موجود"))
        elif k in ("age", "height_cm", "weight_kg", "bmi"):
            mm = re.search(r"\d+\.?\d*", str(v))
            if not mm:
                continue
            v = float(mm.group())
        out[k] = v
    return out


def _groq_extract(text: str) -> dict:
    raw = _get_groq_client().chat(_EXTRACT_SYS, text, temperature=0.0) or ""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group())
    except Exception:
        return {}
    return _normalize(data)


def _reset_if_new(sid):
    if st.session_state.get("sm_sid") != sid:
        st.session_state.sm_sid = sid
        st.session_state.sm_answers = {}
        st.session_state.sm_log = []


def render_clinical_assessment_page(lang: str = "en"):
    ar = (lang == "ar")
    _reset_if_new(st.session_state.get("current_session_id"))
    answers = st.session_state.sm_answers

    smart = _get_groq_client().is_available
    title = ("🫀 جلسة تقييم القلب — حوار ذكي" if ar else "🫀 Heart Risk Session — Smart Chat") if smart \
        else ("🫀 جلسة تقييم القلب" if ar else "🫀 Heart Risk Session")
    st.markdown("## " + title)
    if smart:
        st.caption("صِف حالتك بكلماتك (العمر، الجنس، الطول، الوزن، التدخين، العمل، المخاطر، التاريخ العائلي)."
                   if ar else
                   "Describe yourself freely (age, gender, height, weight, smoking, work, hazards, family history).")

    # intro message
    if not st.session_state.sm_log:
        intro = ("مرحباً 👋 احكيلي عن حالتك: عمرك، جنسك، طولك، وزنك، تدخينك، عملك، أي مخاطر بالعمل، وتاريخ عائلي لأمراض القلب."
                 if ar else
                 "Hi 👋 tell me about yourself: age, gender, height, weight, smoking, job, any workplace hazards, and family history of heart disease.")
        st.session_state.sm_log.append(("bot", intro))

    for role, text in st.session_state.sm_log:
        with st.chat_message("assistant" if role == "bot" else "user"):
            st.markdown(text)

    missing = [f for f in REQUIRED if f not in answers]
    done = not missing

    if not done:
        user_msg = st.chat_input("اكتب هنا..." if ar else "Type here...")
        if user_msg:
            st.session_state.sm_log.append(("user", user_msg))
            if smart:
                extracted = _groq_extract(user_msg)
            else:
                extracted = _classic_parse(user_msg, missing[0])
            answers.update(extracted)
            still = [f for f in REQUIRED if f not in answers]
            if extracted:
                got = "، ".join(_LABELS_AR[k] if ar else k for k in extracted) if ar \
                    else ", ".join(extracted.keys())
                bot = (f"تمام، سجّلت: {got}." if ar else f"Got: {got}.")
            else:
                bot = ("ما قدرت أستخرج معلومة — جرّب توضّح أكثر." if ar
                       else "I couldn't extract anything — please clarify.")
            if still:
                ask = "، ".join(_LABELS_AR[f] if ar else f for f in still)
                bot += ("\n\nباقي أحتاج: " if ar else "\n\nStill need: ") + ask
            st.session_state.sm_log.append(("bot", bot))
            st.rerun()
        st.progress(len(answers) / (len(REQUIRED) + len(OPTIONAL)),
                    text=f"{len([f for f in REQUIRED if f in answers])}/{len(REQUIRED)}")
        return

    # ---- complete -> pipeline ----
    base = dict(answers)
    base.setdefault("environmental_hazards", [])
    base.setdefault("family_history", False)
    base.setdefault("bmi", None)
    res = domain_pipeline.assess(base)
    final = res["decision"]["final_risk_level"]
    col = _COLOR.get(final, "#888")

    st.success("اكتمل التقييم:" if ar else "Assessment complete:")
    st.markdown(
        f"<div style='padding:18px;border-radius:10px;background:{col}22;border-left:7px solid {col};'>"
        f"<span style='font-size:1.4em;font-weight:800;color:{col};'>"
        f"{'القرار النهائي' if ar else 'Final decision'}: {final}</span><br>"
        f"<span style='color:#555;'>{res['decision']['reasoning']}</span></div>",
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("ML", f"{res['ml'].get('probability', 0):.0%}", res["ml"].get("risk_level", ""))
    c2.metric(("القواعد" if ar else "Rules"), res["rules"]["risk_level"],
              f"{len(res['rules']['triggered'])} " + ("قاعدة" if ar else "rules"))

    st.markdown("#### " + ("🌳 شجرة القرار" if ar else "🌳 Decision tree"))
    st.markdown(" → ".join(
        f"<span style='background:#34495e;color:#fff;padding:4px 10px;border-radius:6px;'>{k}: <b>{v}</b></span>"
        for k, v in res["decision_tree_path"]), unsafe_allow_html=True)

    # Groq natural-language interpretation
    if smart:
        interp = _get_groq_client().chat(
            "You are a cardiologist assistant. Give a short, clear, empathetic explanation "
            + ("in Arabic." if ar else "in English."),
            f"Risk decision: {final}. Active factors: {', '.join(res['active_features'])}. "
            f"Give 2-3 sentences plus one recommendation.", temperature=0.3)
        if interp:
            st.markdown("#### " + ("🤖 تفسير الذكاء الاصطناعي" if ar else "🤖 AI interpretation"))
            st.info(interp)

    with st.expander("الميزات المشتقّة والقواعد" if ar else "Derived features & rules"):
        st.write(", ".join(res["active_features"]))
        top = res["rules"]["triggered"][:6]
        if top:
            st.table([{"Rule": r["rule_id"], "Condition": r["condition"]} for r in top])


def _classic_parse(answer, field):
    a = (answer or "").lower()
    if field in ("age", "height_cm", "weight_kg"):
        m = re.search(r"\d+\.?\d*", a)
        return {field: float(m.group())} if m else {}
    if field == "gender":
        if any(w in a for w in ["ذكر", "male", "رجل"]):
            return {"gender": "male"}
        if any(w in a for w in ["أنثى", "انثى", "female"]):
            return {"gender": "female"}
        return {}
    if field == "smoking_status":
        if any(w in a for w in ["حالي", "current", "نعم"]):
            return {"smoking_status": "current smoker"}
        if any(w in a for w in ["سابق", "ex"]):
            return {"smoking_status": "ex-smoker"}
        return {"smoking_status": "non-smoker"}
    if field == "workplace_type":
        return {"workplace_type": "factory" if any(w in a for w in ["مصنع", "factory"]) else "office"}
    return {}
