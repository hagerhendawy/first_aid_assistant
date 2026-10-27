"""File handling: TXT guides, JSON rules, CSV contacts/clinic, query log."""
import csv, json, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
GUIDES_DIR = os.path.join(DATA, "guides")
RULES_FILE = os.path.join(DATA, "rules.json")
CONTACTS_FILE = os.path.join(DATA, "emergency_contacts.csv")
CLINIC_FILE = os.path.join(DATA, "campus_clinic.csv")
CONFIG_FILE = os.path.join(DATA, "config.json")
LOG_FILE = os.path.join(DATA, "queries.log")

CONTACT_FIELDS = ["name", "type", "phone", "notes"]
CLINIC_FIELDS = ["name", "location", "phone", "hours", "services"]


# ---------- guides (TXT) ----------
def load_guides():
    guides = {}
    os.makedirs(GUIDES_DIR, exist_ok=True)
    for fn in sorted(os.listdir(GUIDES_DIR)):
        if not fn.endswith(".txt"):
            continue
        gid = fn[:-4]
        with open(os.path.join(GUIDES_DIR, fn), encoding="utf-8") as f:
            raw = f.read()
        title, source, body = gid.replace("_", " ").title(), "", raw
        if "\n---\n" in raw:
            head, body = raw.split("\n---\n", 1)
            for line in head.splitlines():
                if line.upper().startswith("TITLE:"):
                    title = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SOURCE:"):
                    source = line.split(":", 1)[1].strip()
        guides[gid] = {"id": gid, "title": title, "source": source, "text": body.strip()}
    return guides


def save_guide(gid, title, source, text):
    os.makedirs(GUIDES_DIR, exist_ok=True)
    with open(os.path.join(GUIDES_DIR, gid + ".txt"), "w", encoding="utf-8") as f:
        f.write(f"TITLE: {title}\nSOURCE: {source}\n---\n{text.strip()}\n")


def delete_guide(gid):
    p = os.path.join(GUIDES_DIR, gid + ".txt")
    if os.path.exists(p):
        os.remove(p)
        return True
    return False


# ---------- rules (JSON) ----------
def load_rules():
    with open(RULES_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_rules(data):
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------- CSV ----------
def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


# ---------- config ----------
def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"admin_pin": "1234"}


# ---------- log ----------
def log_query(mode, text, situation, level, top_guide):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = " ".join(str(text).split())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {mode} | {text} | situation={situation} | level={level} | top_guide={top_guide}\n")


def read_log(last=20):
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, encoding="utf-8") as f:
        return f.read().splitlines()[-last:]
