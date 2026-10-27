"""First Aid Awareness Assistant - Streamlit web interface (all features + text-to-speech).
Visual style: burgundy "grand rounds" medical presentation look (web interface only).
Run:  streamlit run app.py
"""
import html as _h
import io, json
from contextlib import contextmanager
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import storage
from assistant import Assistant
from tts import clean_for_speech

st.set_page_config(page_title="First Aid Awareness Assistant", page_icon="🩺", layout="wide")

if "app" not in st.session_state:
    st.session_state.app = Assistant()
app: Assistant = st.session_state.app
st.session_state.setdefault("result", None)
st.session_state.setdefault("admin_ok", False)

E = lambda s: _h.escape(str(s))

# ------------------------------------------------------------------ theme (CSS)
LOGO_W = ('<svg viewBox="0 0 40 40" width="38" height="38"><circle cx="20" cy="20" r="18" fill="none" stroke="#fff" stroke-width="2"/>'
          '<path d="M20 8l9 3v8c0 5-4 9-9 11-5-2-9-6-9-11v-8z" fill="#fff"/><path d="M18.4 14h3.2v3.4H25v3.2h-3.4V24h-3.2v-3.4H15v-3.2h3.4z" fill="#8c1d2f"/></svg>')
LOGO_R = LOGO_W.replace('stroke="#fff"', 'stroke="#8c1d2f"').replace('fill="#fff"', 'fill="#8c1d2f"').replace('fill="#8c1d2f"/></svg>', 'fill="#fff"/></svg>')
BUILDING = ('<svg viewBox="0 0 520 330" preserveAspectRatio="xMidYMid slice" width="100%" height="100%"><defs>'
            '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3f86d6"/><stop offset="1" stop-color="#b9d8f5"/></linearGradient>'
            '<pattern id="w" width="26" height="22" patternUnits="userSpaceOnUse"><rect width="26" height="22" fill="#cfd8e3"/><rect x="2" y="2" width="22" height="18" fill="#7fa6cf"/></pattern></defs>'
            '<rect width="520" height="330" fill="url(#sky)"/><polygon points="250,40 520,0 520,330 250,330" fill="#e8ecf1"/>'
            '<polygon points="250,40 360,28 360,330 250,330" fill="url(#w)" opacity=".9"/><rect x="80" y="150" width="180" height="180" fill="url(#w)"/>'
            '<rect x="372" y="60" width="130" height="62" rx="4" fill="#f7f9fb"/><text x="437" y="86" font-size="14" font-weight="800" text-anchor="middle" fill="#13294b" font-family="sans-serif">FIRST AID</text>'
            '<text x="437" y="106" font-size="14" font-weight="800" text-anchor="middle" fill="#13294b" font-family="sans-serif">CENTER</text>'
            '<rect x="0" y="300" width="520" height="30" fill="#c9ccd1"/></svg>')

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, button, input, textarea { font-family: 'Plus Jakarta Sans', sans-serif !important; }
.stApp { background: radial-gradient(circle at 20% 10%, #efedea 0, #e4e2de 45%, #dcdad6 100%); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1120px; padding-top: 1.4rem; }
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid #e3dfe0; }
.fa-side-brand { display:flex; align-items:center; gap:10px; padding:4px 0 10px; }
.fa-side-brand b { color:#8c1d2f; font-size:15px; line-height:1.15; letter-spacing:.3px; }

/* ---------- hero (cover slide) ---------- */
.fa-hero { border-radius:22px; overflow:hidden; box-shadow:0 10px 30px rgba(60,20,25,.18); background:#fff; margin-bottom:18px; }
.fa-hero-top { display:grid; grid-template-columns: 1.15fr 1fr; min-height:330px; position:relative; }
.fa-hero-left { background:#fff; padding:34px 40px; border-top-right-radius:70% 100%; border-bottom-right-radius:30% 20%; position:relative; z-index:2; }
.fa-brand { display:flex; align-items:center; gap:12px; color:#8c1d2f; font-weight:700; font-size:13px; letter-spacing:.4px; margin-bottom:26px; }
.fa-brand i { width:1px; height:30px; background:#cfcfcf; display:inline-block; }
.fa-hero h1 { font-size:54px; line-height:1.05; font-weight:800; color:#0d0d10; margin:0; padding:0; letter-spacing:-1px; }
.fa-hero-right { position:absolute; right:0; top:0; bottom:0; width:56%; z-index:1; }
.fa-hero-band { background:#8c1d2f; color:#fff; padding:20px 40px 24px; border-top-left-radius:50% 22px; margin-top:-22px; position:relative; z-index:3; }
.fa-hero-band b { font-size:17px; } .fa-hero-band span { opacity:.88; font-size:15px; display:block; margin-top:3px; }

/* ---------- section card with curved banner ---------- */
[class*="st-key-card_"] { background:#fff; border-radius:20px; box-shadow:0 6px 20px rgba(60,20,25,.12); padding:0 !important; gap:0 !important; overflow:hidden; margin-bottom:20px; }
[class*="st-key-body_"] { padding:14px 30px 22px !important; }
.fa-banner { background:linear-gradient(135deg,#6f1424 0%,#9b2335 55%,#8c1d2f 100%); color:#fff; display:flex; align-items:center; justify-content:center; position:relative;
  padding:15px 80px 30px; border-bottom-left-radius:50% 22px; border-bottom-right-radius:50% 22px; box-shadow:0 6px 12px rgba(111,20,36,.25); }
.fa-banner .lg { position:absolute; left:22px; top:12px; }
.fa-banner .tt { font-size:23px; font-weight:700; letter-spacing:.2px; }
.fa-h { font-weight:800; font-size:16px; color:#1d1d22; padding-bottom:7px; border-bottom:2px solid #8c1d2f; margin:6px 0 12px; }
.fa-arrows { list-style:none; padding:0; margin:0; } .fa-arrows li { padding:6px 0 6px 28px; position:relative; font-size:15px; color:#2a2a30; }
.fa-arrows li::before { content:'\\2192'; position:absolute; left:4px; color:#8c1d2f; font-weight:800; }
.fa-chip { display:inline-block; background:#f6e9eb; color:#8c1d2f; border-radius:20px; padding:3px 12px; margin:3px 6px 3px 0; font-size:13px; font-weight:600; }

/* verdict */
.fa-verdict { display:flex; gap:16px; align-items:center; border-radius:14px; padding:18px 22px; color:#fff; font-weight:700; font-size:18px; line-height:1.35; }
.fa-verdict .ic { font-size:34px; } .fa-v-emergency { background:linear-gradient(135deg,#a3162b,#7d1020); } .fa-v-clinic { background:linear-gradient(135deg,#d98a1c,#b36a0c); }
.fa-v-self_care { background:linear-gradient(135deg,#2c8f7d,#1f6f60); } .fa-v-none { background:linear-gradient(135deg,#5b6572,#434b56); }

/* numbered step rows (history & physical style) */
.fa-row { display:flex; gap:16px; align-items:flex-start; background:#faf9f8; border-left:4px solid #8c1d2f; border-radius:6px; padding:14px 18px; margin:10px 0; box-shadow:0 2px 6px rgba(0,0,0,.06); font-size:15px; color:#222; }
.fa-num { flex:0 0 32px; height:32px; border-radius:50%; background:#8c1d2f; color:#fff; font-weight:800; display:flex; align-items:center; justify-content:center; font-size:14px; }
.fa-rid { flex:0 0 52px; font-weight:800; color:#8c1d2f; }
.fa-first { border-left-color:#a3162b; background:#fdf1f2; }

/* 3 / 4 column cards (learning objectives, take-home, differential dx) */
.fa-cols { display:grid; gap:16px; } .fa-c3 { grid-template-columns:repeat(3,1fr); } .fa-c4 { grid-template-columns:repeat(4,1fr); }
.fa-col { background:#f7f6f5; border-radius:10px; padding:16px; border:1px solid #eceae8; min-height:110px; }
.fa-col .ct { font-weight:800; font-size:17px; color:#1d1d22; padding-bottom:8px; border-bottom:2px solid #8c1d2f; margin-bottom:10px; }
.fa-col .cb { font-size:14px; color:#4a4a52; line-height:1.5; }
.fa-badge { display:inline-block; background:#8c1d2f; color:#fff; font-weight:800; border-radius:6px; padding:2px 10px; font-size:13px; margin-bottom:8px; }
.fa-score { height:6px; border-radius:4px; background:#eadbdd; margin:8px 0; } .fa-score div { height:6px; border-radius:4px; background:#8c1d2f; }

/* contact table (clinical progress style) */
.fa-table { width:100%; border-collapse:collapse; font-size:15px; } .fa-table th { text-align:left; color:#6a6a72; font-weight:700; padding:8px 10px; border-bottom:2px solid #eee; }
.fa-table td { padding:11px 10px; border-bottom:1px solid #eee; } .fa-dot { display:inline-block; width:12px; height:12px; border-radius:50%; background:#8c1d2f; margin-right:10px; vertical-align:middle; }

/* disclosure notice bar */
.fa-notice { background:#8c1d2f; color:#fff; border-radius:12px; padding:12px 18px; margin-bottom:16px; font-size:14.5px; font-weight:600; box-shadow:0 4px 12px rgba(111,20,36,.25); }

/* tabs + widgets */
[role="tab"] { background:#fff !important; border-radius:12px 12px 0 0 !important; padding:10px 20px !important; margin-right:6px; }
[role="tab"] p { font-weight:700 !important; color:#5b1320 !important; }
[role="tab"][aria-selected="true"] { background:#8c1d2f !important; } [role="tab"][aria-selected="true"] p { color:#fff !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none !important; } [role="tablist"] { gap:6px; margin-bottom:12px; }
div.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button { border-radius:10px; font-weight:700; border:1px solid #8c1d2f; }
div.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:#8c1d2f; color:#fff; }
[data-testid="stExpander"] { background:#fff; border-radius:12px; border:1px solid #e5e1e2; }
@media (max-width: 800px) { .fa-hero-top { grid-template-columns:1fr; } .fa-hero-right { display:none; } .fa-hero h1 { font-size:38px; } .fa-c3, .fa-c4 { grid-template-columns:1fr; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

_ctr = [0]


@contextmanager
def card(title):
    """A white rounded card with a curved burgundy title banner (like a presentation slide)."""
    _ctr[0] += 1
    with st.container(key=f"card_{_ctr[0]}"):
        st.markdown(f'<div class="fa-banner"><span class="lg">{LOGO_W}</span><span class="tt">{E(title)}</span></div>', unsafe_allow_html=True)
        with st.container(key=f"body_{_ctr[0]}"):
            yield


def heading(t):
    st.markdown(f'<div class="fa-h">{E(t)}</div>', unsafe_allow_html=True)


def arrows(items):
    st.markdown('<ul class="fa-arrows">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>", unsafe_allow_html=True)


def cols_html(items, n):
    return f'<div class="fa-cols fa-c{n}">' + "".join(f'<div class="fa-col"><div class="ct">{t}</div><div class="cb">{b}</div></div>' for t, b in items) + "</div>"


def contacts_table(rows, cols):
    head = "".join(f"<th>{E(c)}</th>" for c in cols)
    body = "".join("<tr>" + "".join((f'<td><span class="fa-dot"></span><b>{E(r.get(c, ""))}</b></td>' if i == 0 else f'<td>{E(r.get(c, ""))}</td>')
                                    for i, c in enumerate(cols)) + "</tr>" for r in rows)
    st.markdown(f'<table class="fa-table"><tr>{head}</tr>{body}</table>', unsafe_allow_html=True)


LEVEL_UI = {"emergency": "🚨", "clinic": "🏥", "self_care": "🩹", None: "❓"}

# ------------------------------------------------------------------ text to speech
@st.cache_data(show_spinner=False)
def gtts_mp3(text: str, lang: str) -> bytes:
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buf)
    return buf.getvalue()


def speak_ui(text: str, key: str, autoplay: bool):
    """Render the text-to-speech controls for `text` according to the sidebar settings."""
    mode = st.session_state.get("voice_mode", "Off")
    if mode == "Off":
        return
    clean = clean_for_speech(text)
    lang = st.session_state.get("voice_lang", "en-US")
    rate = st.session_state.get("voice_rate", 1.0)
    if mode.startswith("Browser"):
        safe_text = json.dumps(clean).replace("</", "<\\/")
        auto_js = "setTimeout(say, 300);" if autoplay else ""
        lang_js = json.dumps(lang)
        html = f"""
        <div style="font-family:sans-serif">
          <button id="p" style="padding:9px 18px;font-size:15px;cursor:pointer;border:0;border-radius:10px;background:#8c1d2f;color:#fff;font-weight:600">🔊 Read aloud</button>
          <button id="s" style="padding:9px 18px;font-size:15px;cursor:pointer;border:0;border-radius:10px;background:#8c1d2f;color:#fff;font-weight:600">⏹ Stop</button>
          <span id="m" style="color:#b00;font-size:13px"></span>
        </div>
        <script>
          const text = {safe_text};
          function say() {{
            if (!('speechSynthesis' in window)) {{ document.getElementById('m').innerText = 'Browser has no speech support'; return; }}
            speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.lang = {lang_js}; u.rate = {rate};
            speechSynthesis.speak(u);
          }}
          document.getElementById('p').onclick = say;
          document.getElementById('s').onclick = () => speechSynthesis.cancel();
          {auto_js}
        </script>""".strip()
        if hasattr(st, "iframe"):          # newer Streamlit
            st.iframe(html, height=60)
        else:                              # older Streamlit
            components.html(html, height=60)
    else:
        try:
            with st.spinner("Generating audio..."):
                mp3 = gtts_mp3(clean, lang[:2])
            st.audio(mp3, format="audio/mp3", autoplay=autoplay)
            st.download_button("⬇ Download audio (mp3)", mp3, file_name="first_aid_answer.mp3", mime="audio/mpeg", key="dl_" + key)
        except Exception as e:
            st.warning(f"Server voice (gTTS) needs internet and `pip install gTTS`. Error: {e}")


# ------------------------------------------------------------------ result rendering
def show_result(r, key="res", autoplay=False):
    lvl = r["level"] or "none"
    names = [app.kb.symptoms[f]["label"] for f in sorted(r["facts"]) if f in app.kb.symptoms]

    with card("Hospital Decision"):
        st.markdown(f'<div class="fa-verdict fa-v-{lvl}"><span class="ic">{LEVEL_UI[r["level"]]}</span><span>{E(r["verdict"])}</span></div>', unsafe_allow_html=True)
        heading("Understood facts")
        st.markdown("".join(f'<span class="fa-chip">{E(n)}</span>' for n in names) or "<i>none detected</i>", unsafe_allow_html=True)
        if st.session_state.get("voice_mode", "Off") != "Off":
            heading("Voice")
            speak_ui(app.speech(r), key, autoplay)

    if r["steps"]:
        with card("What Should I Do?"):
            st.markdown("".join(f'<div class="fa-row{" fa-first" if i == 1 and r["level"] == "emergency" else ""}"><div class="fa-num">{i}</div><div>{E(s)}</div></div>'
                                for i, s in enumerate(r["steps"], 1)), unsafe_allow_html=True)

    with card("Why? Rules Fired"):
        if not r["fired"]:
            st.write("No rule matched. Select more symptoms or describe the situation in more detail.")
        rows = ""
        for x in r["fired"]:
            res = x["level"].upper() if x["level"] else "derive " + ",".join(x["derive"])
            rows += (f'<div class="fa-row"><div class="fa-rid">{E(x["id"])}</div><div><b>IF</b> {E(" AND ".join(x["if"]))} '
                     f'<b style="color:#8c1d2f">THEN {E(res)}</b><br><span style="color:#666">{E(x["why"])}</span></div></div>')
        st.markdown(rows, unsafe_allow_html=True)

    if r["guides"]:
        with card("Related Guides"):
            st.caption("Ranked with TF-IDF and cosine similarity")
            st.markdown(cols_html([(E(g["title"]), f'<div class="fa-score"><div style="width:{min(100, int(g["score"] * 100))}%"></div></div>'
                                   f'Cosine score <b>{g["score"]:.3f}</b><br>{E(g["snippet"])}') for g in r["guides"]], max(2, min(3, len(r["guides"])))),
                        unsafe_allow_html=True)

    if r["level"] in ("emergency", "clinic"):
        with card("Contacts"):
            contacts_table(storage.read_csv(storage.CONTACTS_FILE), storage.CONTACT_FIELDS)
            heading("Campus clinic")
            contacts_table(storage.read_csv(storage.CLINIC_FILE), storage.CLINIC_FIELDS)


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown(f'<div class="fa-side-brand">{LOGO_R}<b>FIRST AID<br>ASSISTANT</b></div>', unsafe_allow_html=True)
    page = st.radio("Mode", ["User", "Admin"], horizontal=True)
    st.divider()
    st.subheader("🔊 Text-to-speech")
    st.radio("Voice", ["Off", "Browser voice (offline, recommended)", "Server MP3 (gTTS, internet)"], key="voice_mode",
             help="Browser voice uses your device's built-in voices. Server MP3 generates an audio file you can download.")
    st.selectbox("Language", ["en-US", "en-GB", "ar-EG", "ar-SA"], key="voice_lang")
    st.slider("Speed", 0.6, 1.5, 1.0, 0.1, key="voice_rate")
    st.checkbox("Auto-play answers", value=True, key="voice_auto")
    st.divider()
    st.caption(f"Index: {app.index.N} guides · {len(app.index.postings)} terms  \nKB: {len(app.kb.symptoms)} facts · {len(app.kb.rules)} rules")

AUTO = lambda: st.session_state.get("voice_auto", True)

# ================================================================== USER MODE
if page == "User":
    st.markdown(f"""
    <div class="fa-hero"><div class="fa-hero-top">
      <div class="fa-hero-left"><div class="fa-brand">{LOGO_R}<i></i><span>EDUCATIONAL<br>HEALTH PROJECT</span></div>
        <h1>First Aid<br>Awareness<br>Assistant</h1></div>
      <div class="fa-hero-right">{BUILDING}</div></div>
      <div class="fa-hero-band"><b>Information retrieval · Knowledge-based inference · Text-to-speech</b>
      <span>Describe a situation, get the right first-aid steps, and know when to call for help</span></div></div>""", unsafe_allow_html=True)

    with card("Disclosure"):
        heading("Awareness only")
        arrows(["<b>For awareness only</b> - this is NOT a substitute for professional medical care.",
                "In any serious case <b>contact emergency services immediately</b> - Egypt ambulance <b>123</b> · International <b>112</b>.",
                "Guides are summaries of public guidance (NHS, Red Cross, AHA, Mayo Clinic). The rule engine does not diagnose."])

    with card("How It Works"):
        st.markdown(cols_html([("1. Describe", "Select the situation and symptoms, or type a question in your own words."),
                               ("2. Understand", "The inference engine decides: self-care, clinic or hospital, and explains why."),
                               ("3. Act", "Follow numbered steps, listen to them read aloud, find contacts.")], 3), unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["Select symptoms", "Ask a question", "Search guides", "Contacts & clinic"])

    with t1:
        with card("Symptom Selection"):
            sits = {k: v["label"] for k, v in app.kb.situations().items()}
            s = st.selectbox("What happened?", list(sits), format_func=lambda k: sits[k])
            syms = app.kb.symptoms_for(s)
            chosen = st.multiselect("Select all that apply", list(syms), format_func=lambda k: syms[k]["label"])
            if st.button("Get advice", type="primary", key="b_sym"):
                st.session_state.result = ("sym", app.from_symptoms({s, *chosen}))
        if st.session_state.result and st.session_state.result[0] == "sym":
            show_result(st.session_state.result[1], "sym", AUTO())

    with t2:
        with card("Case Overview"):
            st.caption("Examples: my friend has a burn with large blisters · a baby is choking and turning blue · she fainted but woke up quickly")
            q = st.text_area("Describe the situation or type your question", height=100)
            if st.button("Ask", type="primary", key="b_q") and q.strip():
                st.session_state.result = ("q", app.from_text(q))
        if st.session_state.result and st.session_state.result[0] == "q":
            show_result(st.session_state.result[1], "q", AUTO())

    with t3:
        with card("Search Guides"):
            sq = st.text_input("Search first-aid guides (TF-IDF + cosine similarity)")
            if sq:
                res = app.search(sq, 5)
                if not res:
                    st.info("No matching guide.")
                for g in res:
                    with st.expander(f"{g['title']}  -  score {g['score']:.3f}"):
                        st.caption(g["snippet"])
                        full = app.guides[g["doc_id"]]
                        st.markdown(f"*Source: {full['source']}*")
                        st.text(full["text"])
                        speak_ui(full["title"] + ". " + full["text"], "g_" + g["doc_id"], False)

    with t4:
        with card("Emergency Contacts"):
            contacts_table(storage.read_csv(storage.CONTACTS_FILE), storage.CONTACT_FIELDS)
            heading("Campus clinic")
            contacts_table(storage.read_csv(storage.CLINIC_FILE), storage.CLINIC_FIELDS)

    with card("Take-home Messages"):
        st.markdown(cols_html([('<span class="fa-badge">01</span><br>Call early', "In a serious case, call emergency services first."),
                               ('<span class="fa-badge">02</span><br>Stay calm', "Calm, clear actions help the person most."),
                               ('<span class="fa-badge">03</span><br>Follow steps', "Use the numbered steps and the voice guide."),
                               ('<span class="fa-badge">04</span><br>Get checked', "Even mild cases may need a doctor to confirm.")], 4), unsafe_allow_html=True)

else:
    st.markdown('<div class="fa-notice">⚠ For awareness only - not a substitute for professional medical care. In any serious case contact emergency services immediately (Egypt 123 · International 112).</div>', unsafe_allow_html=True)

    if not st.session_state.admin_ok:
        with card("Admin Login"):
            pin = st.text_input("Admin PIN", type="password")
            if st.button("Login", type="primary"):
                if pin == storage.load_config().get("admin_pin", "1234"):
                    st.session_state.admin_ok = True
                    st.rerun()
                else:
                    st.error("Wrong PIN")
        st.stop()

    c1, c2 = st.columns([6, 1])
    c1.markdown('<div class="fa-h" style="font-size:22px;border:0">🛠 Admin panel</div>', unsafe_allow_html=True)
    if c2.button("Logout"):
        st.session_state.admin_ok = False
        st.rerun()
    a1, a2, a3, a4, a5 = st.tabs(["📄 Guides", "📐 Rules", "🏷 Facts / symptoms", "📇 Contacts & clinic", "📜 Query log"])

    with a1:
        with card("Guides (TXT)"):
            ids = ["<new guide>"] + list(app.guides)
            sel = st.selectbox("Guide", ids)
            old = app.guides.get(sel, {})
            with st.form("guide_form"):
                gid = st.text_input("ID (file name)", value=old.get("id", ""), disabled=bool(old))
                title = st.text_input("Title", value=old.get("title", ""))
                src = st.text_input("Source", value=old.get("source", ""))
                body = st.text_area("Guide text", value=old.get("text", ""), height=300)
                save = st.form_submit_button("💾 Save guide", type="primary")
            if save:
                gid = (old.get("id") or gid).strip().lower().replace(" ", "_")
                if gid and title and body:
                    storage.save_guide(gid, title, src, body)
                    app.reload(); st.success("Saved and search index rebuilt."); st.rerun()
                else:
                    st.error("ID, title and text are required.")
            if old and st.button("🗑 Delete this guide"):
                storage.delete_guide(old["id"]); app.reload(); st.rerun()

    with a2:
        with card("Rules (JSON)"):
            data = storage.load_rules()
            rids = ["<new rule>"] + [r["id"] for r in data["rules"]]
            rs = st.selectbox("Rule", rids)
            r0 = next((r for r in data["rules"] if r["id"] == rs), None)
            facts = list(data["symptoms"])
            with st.form("rule_form"):
                rid = st.text_input("Rule ID", value=r0["id"] if r0 else "", disabled=bool(r0))
                conds = st.multiselect("IF (all facts must be true)", facts, default=r0["if"] if r0 else [])
                levels = ["self_care", "clinic", "emergency", "none (derive only)"]
                lv = st.selectbox("THEN level", levels, index=levels.index(r0["level"]) if r0 and r0["level"] else (3 if r0 else 0))
                why = st.text_input("Why (explanation)", value=r0["why"] if r0 else "")
                acts = st.text_area("Actions (one per line)", value="\n".join(r0["actions"]) if r0 else "", height=160)
                der = st.multiselect("Derive facts", facts, default=r0.get("derive", []) if r0 else [])
                ovr = st.multiselect("Overrides rules", [r["id"] for r in data["rules"] if r["id"] != (r0 or {}).get("id")], default=r0.get("overrides", []) if r0 else [])
                ok = st.form_submit_button("💾 Save rule", type="primary")
            if ok:
                rid = (r0["id"] if r0 else rid).strip()
                if rid and conds:
                    new = {"id": rid, "if": conds, "level": None if lv.startswith("none") else lv, "why": why,
                           "actions": [a.strip() for a in acts.splitlines() if a.strip()], "derive": der, "overrides": ovr}
                    data["rules"] = [x for x in data["rules"] if x["id"] != rid] + [new]
                    storage.save_rules(data); app.reload(); st.success("Rule saved."); st.rerun()
                else:
                    st.error("Rule ID and at least one IF fact are required.")
            if r0 and st.button("🗑 Delete this rule"):
                data["rules"] = [x for x in data["rules"] if x["id"] != r0["id"]]
                storage.save_rules(data); app.reload(); st.rerun()
            with st.expander("All rules"):
                st.dataframe(pd.DataFrame([{"id": r["id"], "IF": " AND ".join(r["if"]), "level": r["level"], "why": r["why"]} for r in data["rules"]]),
                             hide_index=True)

    with a3:
        with card("Facts & Symptoms"):
            data = storage.load_rules()
            fs = st.selectbox("Fact", ["<new fact>"] + list(data["symptoms"]))
            f0 = data["symptoms"].get(fs)
            sit_ids = [k for k, v in data["symptoms"].items() if v["type"] == "situation"]
            with st.form("fact_form"):
                fid = st.text_input("Fact ID", value=fs if f0 else "", disabled=bool(f0))
                label = st.text_input("Label", value=f0["label"] if f0 else "")
                typ = st.selectbox("Type", ["symptom", "situation"], index=0 if not f0 or f0["type"] == "symptom" else 1)
                fo = st.multiselect("Applies to situations (empty = all)", sit_ids, default=f0["for"] if f0 else [])
                kws = st.text_area("Keywords (comma separated)", value=", ".join(f0["keywords"]) if f0 else "")
                okf = st.form_submit_button("💾 Save fact", type="primary")
            if okf:
                fid = (fs if f0 else fid).strip()
                if fid and label:
                    data["symptoms"][fid] = {"label": label, "type": typ, "for": fo, "keywords": [k.strip().lower() for k in kws.split(",") if k.strip()]}
                    storage.save_rules(data); app.reload(); st.success("Fact saved."); st.rerun()

    with a4:
        with card("Contacts & Clinic (CSV)"):
            for title, path, fields in (("Emergency contacts (CSV)", storage.CONTACTS_FILE, storage.CONTACT_FIELDS),
                                        ("Campus clinic (CSV)", storage.CLINIC_FILE, storage.CLINIC_FIELDS)):
                st.markdown(f"**{title}** - edit cells, add rows at the bottom, select a row and press Delete to remove")
                df = pd.DataFrame(storage.read_csv(path), columns=fields).fillna("")
                edited = st.data_editor(df, num_rows="dynamic", key="ed_" + path)
                if st.button("💾 Save " + title, key="sv_" + path):
                    storage.write_csv(path, edited.fillna("").to_dict("records"), fields)
                    st.success("Saved.")

    with a5:
        with card("Query Log"):
            lines = storage.read_log(200)
            st.code("\n".join(lines) or "(log is empty)", language="text")
            if lines:
                st.download_button("⬇ Download log", "\n".join(lines), file_name="queries.log")
            if st.button("🔄 Rebuild search index"):
                app.reload(); st.success(f"Index rebuilt: {app.index.N} guides, {len(app.index.postings)} terms.")
