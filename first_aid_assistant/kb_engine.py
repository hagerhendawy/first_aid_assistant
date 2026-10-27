"""Knowledge representation: facts + IF-THEN rules + forward-chaining inference engine."""
import re

LEVELS = {"self_care": 1, "clinic": 2, "emergency": 3}
VERDICTS = {
    "emergency": "YES - this may need EMERGENCY / hospital care. Call emergency services now.",
    "clinic": "Medical check recommended - visit the campus clinic or a doctor (not necessarily an ambulance).",
    "self_care": "Probably manageable with first aid on the spot, but get medical help if it gets worse.",
    None: "Not enough information to decide. If in doubt, treat it as serious and call emergency services.",
}
NEG = re.compile(r"\b(no|not|without|never|isn't|isnt|doesn't|doesnt|hasn't|hasnt)\s+(?:\w+\s+)?$")


class KnowledgeBase:
    def __init__(self, data):
        self.symptoms = data["symptoms"]
        self.rules = data["rules"]
        self._pats = {}
        for sid, s in self.symptoms.items():
            self._pats[sid] = [(kw, re.compile(r"\b" + re.escape(kw.lower()) + r"(?:s|es|ed|ing)?\b"))
                               for kw in s.get("keywords", [])]

    def situations(self):
        return {k: v for k, v in self.symptoms.items() if v["type"] == "situation"}

    def symptoms_for(self, situation):
        return {k: v for k, v in self.symptoms.items()
                if v["type"] == "symptom" and (not v.get("for") or situation in v["for"])}

    # ---- natural-language -> facts ----
    def extract_facts(self, text):
        t = text.lower().replace("\u2019", "'")
        facts = set()
        for sid, pats in self._pats.items():
            for kw, pat in pats:
                hit = False
                for m in pat.finditer(t):
                    if NEG.search(t[:m.start()][-20:]) and not kw.startswith(("no ", "not ")):
                        continue
                    hit = True
                    break
                if hit:
                    facts.add(sid)
                    break
        return facts

    # ---- forward chaining ----
    def infer(self, facts):
        facts = set(facts)
        fired, done, changed = [], set(), True
        while changed:
            changed = False
            for r in self.rules:
                if r["id"] in done or not set(r["if"]) <= facts:
                    continue
                done.add(r["id"])
                fired.append(r)
                new = set(r.get("derive", [])) - facts
                if new:
                    facts |= new
                    changed = True
        acting = [r for r in fired if r.get("level")]
        acting.sort(key=lambda r: (-LEVELS[r["level"]], -len(r["if"]) if r["level"] == "emergency" else len(r["if"])))
        level = acting[0]["level"] if acting else None
        overridden = {o for r in acting for o in r.get("overrides", [])}
        acting = [r for r in acting if r["id"] not in overridden]
        steps, seen = [], set()
        for r in acting:
            for a in r.get("actions", []):
                if a not in seen:
                    seen.add(a); steps.append(a)
        situations = [s for s in facts if self.symptoms.get(s, {}).get("type") == "situation"]
        return {"facts": facts, "fired": fired, "level": level, "verdict": VERDICTS[level],
                "needs_hospital": level == "emergency", "steps": steps, "situations": situations}
