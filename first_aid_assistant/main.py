"""First Aid Awareness Assistant - command-line interface (user mode + admin mode)."""
import os, sys
import storage
from assistant import Assistant, NOTICE, wrap
from tts import Speaker


def ask(prompt, default=None):
    try:
        v = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print(); return "0"
    return v if v else (default or "")


def read_block(prompt):
    print(prompt + " (finish with a line containing only END)")
    lines = []
    while True:
        try:
            l = input()
        except EOFError:
            break
        if l.strip() == "END":
            break
        lines.append(l)
    return "\n".join(lines)


def pick(options, title):
    """options: list of (key,label). Returns key or None."""
    print(f"\n{title}")
    for i, (_, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    print("  0. Back")
    c = ask("> ")
    return options[int(c) - 1][0] if c.isdigit() and 1 <= int(c) <= len(options) else None


# ============================ USER MODE ============================
def show_result(app, speaker, r):
    print("\n" + app.render(r))
    if speaker.enabled:
        speaker.speak(app.speech(r))
    elif ask("Read this aloud? (y/N) ").lower() == "y":
        speaker.enabled = True; speaker.speak(app.speech(r)); speaker.enabled = False
    if ask("Save as audio file? (y/N) ").lower() == "y" and speaker.available:
        ext = ".mp3" if "gTTS" in (speaker.engine_name or "") else ".wav"
        try:
            print("Saved:", speaker.save(app.speech(r), os.path.join(storage.BASE, "answer_audio" + ext)))
        except Exception as e:
            print("Could not save audio:", e)


def by_symptoms(app, speaker):
    sits = [(k, v["label"]) for k, v in app.kb.situations().items()]
    s = pick(sits, "What happened?")
    if not s:
        return
    syms = list(app.kb.symptoms_for(s).items())
    print("\nSelect ALL that apply (comma separated numbers, Enter for none):")
    for i, (_, v) in enumerate(syms, 1):
        print(f"  {i}. {v['label']}")
    chosen = {s}
    for tok in ask("> ").replace(" ", "").split(","):
        if tok.isdigit() and 1 <= int(tok) <= len(syms):
            chosen.add(syms[int(tok) - 1][0])
    show_result(app, speaker, app.from_symptoms(chosen))


def by_question(app, speaker):
    q = ask("\nDescribe the situation or type your question:\n> ")
    if q in ("", "0"):
        return
    show_result(app, speaker, app.from_text(q))


def by_search(app):
    q = ask("\nSearch the guides: ")
    if q in ("", "0"):
        return
    res = app.search(q, 5)
    print("\n" + NOTICE)
    if not res:
        print("No matching guide.")
    for i, g in enumerate(res, 1):
        print(f"\n{i}. {g['title']}  (cosine score {g['score']:.3f})")
        print(wrap(g["snippet"], "   ", hang=""))
    if res:
        c = ask("\nOpen a guide (number) or Enter: ")
        if c.isdigit() and 1 <= int(c) <= len(res):
            gd = app.guides[res[int(c) - 1]["doc_id"]]
            print(f"\n=== {gd['title']} ===\nSource: {gd['source']}\n\n{gd['text']}")


def show_contacts():
    print("\n" + NOTICE + "\n\nEMERGENCY CONTACTS")
    for c in storage.read_csv(storage.CONTACTS_FILE):
        print(f"  {c['name']:<32} {c['phone']:<12} {c['notes']}")
    print("\nCAMPUS CLINIC")
    for c in storage.read_csv(storage.CLINIC_FILE):
        print(f"  {c['name']} | {c['location']} | Tel {c['phone']} | {c['hours']}\n  Services: {c['services']}")


def user_menu(app, speaker):
    while True:
        print("\n" + "-" * 78 + "\nUSER MENU        voice: " + ("ON" if speaker.enabled else "OFF")
              + f"  (engine: {speaker.engine_name or 'none installed'})\n" + "-" * 78)
        print("  1. Describe a situation by selecting symptoms\n  2. Type a question (e.g. 'my friend has a burn with large blisters')"
              "\n  3. Search first-aid guides\n  4. Emergency contacts & campus clinic\n  5. Toggle voice (text-to-speech)\n  0. Back")
        c = ask("> ")
        if c == "1": by_symptoms(app, speaker)
        elif c == "2": by_question(app, speaker)
        elif c == "3": by_search(app)
        elif c == "4": show_contacts()
        elif c == "5":
            speaker.enabled = not speaker.enabled
            if speaker.enabled and not speaker.available:
                print("No TTS engine installed -> pip install pyttsx3")
            print("Voice is now", "ON" if speaker.enabled else "OFF")
        elif c == "0": return


# ============================ ADMIN MODE ============================
def manage_guides(app):
    while True:
        print("\nGUIDES:", ", ".join(app.guides))
        c = ask("1 add/replace  2 append text  3 delete  0 back > ")
        if c == "1":
            gid = ask("id (file name, e.g. poisoning): ").lower().replace(" ", "_")
            if not gid: continue
            old = app.guides.get(gid, {})
            title = ask(f"title [{old.get('title','')}]: ", old.get("title", gid.title()))
            src = ask(f"source [{old.get('source','')}]: ", old.get("source", ""))
            body = read_block("Guide text") or old.get("text", "")
            storage.save_guide(gid, title, src, body); app.reload(); print("Saved + index rebuilt.")
        elif c == "2":
            gid = ask("guide id: ")
            if gid in app.guides:
                g = app.guides[gid]
                storage.save_guide(gid, g["title"], g["source"], g["text"] + "\n" + read_block("Text to append"))
                app.reload(); print("Updated.")
        elif c == "3":
            gid = ask("guide id to delete: ")
            if storage.delete_guide(gid): app.reload(); print("Deleted.")
        elif c == "0": return


def manage_rules(app):
    data = storage.load_rules()
    while True:
        print(f"\nRULES: {len(data['rules'])} | SYMPTOMS/FACTS: {len(data['symptoms'])}")
        c = ask("1 list rules  2 add rule  3 edit rule  4 delete rule  5 add symptom/fact  0 back > ")
        if c == "1":
            for r in data["rules"]:
                print(f"  {r['id']:<4} IF {' AND '.join(r['if'])} -> {r['level'] or 'derive'}")
        elif c in ("2", "3"):
            old = None
            rid = ask("rule id: ")
            if c == "3":
                old = next((r for r in data["rules"] if r["id"] == rid), None)
                if not old: print("Not found."); continue
            print("Known fact ids:", ", ".join(data["symptoms"]))
            cond = ask("IF facts (comma separated)" + (f" [{','.join(old['if'])}]" if old else "") + ": ")
            cond = [x.strip() for x in cond.split(",") if x.strip()] or (old["if"] if old else [])
            if any(x not in data["symptoms"] for x in cond):
                print("Unknown fact id - add it first (option 5)."); continue
            level = ask("level (self_care/clinic/emergency/none): ", old["level"] if old and old["level"] else "self_care")
            why = ask("why: ", old["why"] if old else "")
            acts = read_block("Actions, one per line").splitlines() or (old["actions"] if old else [])
            new = {"id": rid, "if": cond, "level": None if level == "none" else level, "why": why, "actions": acts,
                   "derive": old["derive"] if old else []}
            data["rules"] = [r for r in data["rules"] if r["id"] != rid] + [new]
            storage.save_rules(data); app.reload(); print("Rule saved.")
        elif c == "4":
            rid = ask("rule id: ")
            data["rules"] = [r for r in data["rules"] if r["id"] != rid]
            storage.save_rules(data); app.reload(); print("Deleted (if it existed).")
        elif c == "5":
            sid = ask("fact id (e.g. poison_swallowed): ")
            label = ask("label: ")
            typ = ask("type (situation/symptom): ", "symptom")
            f = [x.strip() for x in ask("applies to situations (comma, blank = all): ").split(",") if x.strip()]
            kws = [x.strip().lower() for x in ask("keywords (comma separated): ").split(",") if x.strip()]
            data["symptoms"][sid] = {"label": label, "type": typ, "for": f, "keywords": kws}
            storage.save_rules(data); app.reload(); print("Added.")
        elif c == "0": return


def manage_csv(path, fields, title):
    while True:
        rows = storage.read_csv(path)
        print(f"\n{title}")
        for i, r in enumerate(rows, 1):
            print(f"  {i}. " + " | ".join(r.get(f, "") for f in fields))
        c = ask("1 add  2 edit  3 delete  0 back > ")
        if c == "1":
            rows.append({f: ask(f"{f}: ") for f in fields})
        elif c in ("2", "3"):
            n = ask("row number: ")
            if not (n.isdigit() and 1 <= int(n) <= len(rows)): continue
            if c == "3": rows.pop(int(n) - 1)
            else:
                row = rows[int(n) - 1]
                for f in fields:
                    row[f] = ask(f"{f} [{row.get(f,'')}]: ", row.get(f, ""))
        elif c == "0": return
        storage.write_csv(path, rows, fields)


def admin_menu(app):
    if ask("Admin PIN: ") != storage.load_config().get("admin_pin", "1234"):
        print("Wrong PIN."); return
    while True:
        print("\n" + "-" * 78 + "\nADMIN MENU\n" + "-" * 78)
        print("  1. Guides (TXT)\n  2. Rules & facts (JSON)\n  3. Emergency contacts (CSV)\n  4. Campus clinic (CSV)"
              "\n  5. View query log\n  6. Rebuild search index\n  0. Back")
        c = ask("> ")
        if c == "1": manage_guides(app)
        elif c == "2": manage_rules(app)
        elif c == "3": manage_csv(storage.CONTACTS_FILE, storage.CONTACT_FIELDS, "EMERGENCY CONTACTS")
        elif c == "4": manage_csv(storage.CLINIC_FILE, storage.CLINIC_FIELDS, "CAMPUS CLINIC")
        elif c == "5": print("\n" + "\n".join(storage.read_log(30) or ["(log is empty)"]))
        elif c == "6": app.reload(); print(f"Index rebuilt: {app.index.N} guides, {len(app.index.postings)} terms.")
        elif c == "0": return


def main():
    app = Assistant()
    speaker = Speaker(enabled="--voice" in sys.argv)
    while True:
        print("\n" + "=" * 78 + "\n   FIRST AID AWARENESS ASSISTANT\n" + "=" * 78 + "\n" + NOTICE)
        print("\n  1. User mode\n  2. Admin mode\n  0. Exit")
        c = ask("> ")
        if c == "1": user_menu(app, speaker)
        elif c == "2": admin_menu(app)
        elif c == "0": print("Stay safe!"); return


if __name__ == "__main__":
    main()
