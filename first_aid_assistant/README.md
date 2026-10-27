# First Aid Awareness Assistant

Educational Python system: TF-IDF search over first-aid guides + rule-based inference engine
(burns, cuts, choking, fainting, nosebleed, allergic reaction, fractures, CPR) + text-to-speech.
**For awareness only - always contact emergency services in serious cases.**

## Run
    pip install pyttsx3          # optional, for voice
    streamlit run app.py         # WEB interface (recommended)
    python main.py               # command-line version
    python main.py --voice       # start with voice ON
    python demo.py               # non-interactive sample runs
Admin PIN: `1234` (change in `data/config.json`).

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit web interface (all features + TTS) |
| `main.py` | CLI: user mode + admin mode |
| `assistant.py` | Glue: retrieval + inference + rendering + logging |
| `ir_engine.py` | Tokenizer, stemmer, inverted index, TF-IDF, cosine similarity |
| `kb_engine.py` | Facts, IF-THEN rules, forward-chaining inference engine |
| `storage.py` | TXT / JSON / CSV reading+writing, query log |
| `tts.py` | Text-to-speech (pyttsx3 offline, gTTS fallback) |
| `data/guides/*.txt` | First-aid guides (title, source, body) |
| `data/rules.json` | Facts (symptoms + keywords) and rules |
| `data/emergency_contacts.csv`, `data/campus_clinic.csv` | Contacts - **edit with your campus data** |
| `data/queries.log` | Query log |
