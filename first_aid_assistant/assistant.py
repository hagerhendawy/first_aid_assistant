"""Glue layer: IR + knowledge base + storage + rendering (used by the CLI and the demo)."""
import textwrap
import storage
from ir_engine import InvertedIndex
from kb_engine import KnowledgeBase

NOTICE = ("[!] FOR AWARENESS ONLY - this is NOT a substitute for professional medical care.\n"
          "    In any serious case CONTACT EMERGENCY SERVICES IMMEDIATELY "
          "(Egypt ambulance: 123 | International: 112).")


def wrap(text, indent="", width=78, hang="   "):
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent + hang)


class Assistant:
    def __init__(self):
        self.reload()

    def reload(self):
        self.guides = storage.load_guides()
        self.index = InvertedIndex()
        self.index.build(self.guides)
        self.kb = KnowledgeBase(storage.load_rules())

    # ---- queries ----
    def search(self, query, k=3):
        res = self.index.search(query, k)
        storage.log_query("SEARCH", query, "-", "-", res[0]["doc_id"] if res else "none")
        return res

    def from_symptoms(self, facts):
        facts = set(facts)
        result = self.kb.infer(facts)
        labels = " ".join(self.kb.symptoms[f]["label"] for f in facts if f in self.kb.symptoms)
        result["guides"] = self.index.search(labels, 2)
        result["query"] = ", ".join(sorted(facts))
        self._log("SYMPTOMS", result)
        return result

    def from_text(self, question):
        facts = self.kb.extract_facts(question)
        result = self.kb.infer(facts)
        result["guides"] = self.index.search(question, 3)
        result["query"] = question
        self._log("QUESTION", result)
        return result

    def _log(self, mode, r):
        storage.log_query(mode, r["query"], ",".join(r["situations"]) or "unknown", r["level"],
                          r["guides"][0]["doc_id"] if r["guides"] else "none")

    # ---- rendering ----
    def render(self, r):
        L = ["=" * 78, NOTICE, "=" * 78]
        names = [self.kb.symptoms[f]["label"] for f in sorted(r["facts"]) if f in self.kb.symptoms]
        L.append("Understood facts : " + (", ".join(names) if names else "(none detected)"))
        L.append("")
        L.append("DOES THIS CASE NEED A HOSPITAL?")
        L.append(wrap(r["verdict"], "  ", hang=""))
        if r["steps"]:
            L.append("")
            L.append("WHAT SHOULD I DO?")
            for i, s in enumerate(r["steps"], 1):
                L.append(wrap(f"{i}. {s}", "  "))
        L.append("")
        L.append("WHY (rules fired):")
        shown = [x for x in r["fired"]]
        for x in shown:
            cond = " AND ".join(x["if"])
            res = x["level"].upper() if x["level"] else "derive " + ",".join(x["derive"])
            L.append(wrap(f"[{x['id']}] IF {cond} THEN {res} - {x['why']}", "  "))
        if not shown:
            L.append("  No rule matched. Try selecting symptoms or describing the situation in more detail.")
        if r["guides"]:
            L.append("")
            L.append("RELATED GUIDES (TF-IDF / cosine ranking):")
            for g in r["guides"]:
                L.append(f"  - {g['title']}  (score {g['score']:.3f})")
                L.append(wrap(g["snippet"], "      ", hang=""))
        if r["level"] in ("emergency", "clinic"):
            L.append("")
            L.append("CONTACTS:")
            for c in storage.read_csv(storage.CONTACTS_FILE):
                L.append(f"  {c['name']}: {c['phone']}")
            for c in storage.read_csv(storage.CLINIC_FILE):
                L.append(f"  {c['name']}: {c['location']} | Tel {c['phone']} | {c['hours']}")
        L.append("=" * 78)
        return "\n".join(L)

    def speech(self, r):
        parts = ["This information is for awareness only. In serious cases contact emergency services immediately.",
                 r["verdict"]]
        if r["steps"]:
            parts.append("Here is what you should do.")
            parts += [f"Step {i}. {s}" for i, s in enumerate(r["steps"], 1)]
        return " ".join(parts)
