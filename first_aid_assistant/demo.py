"""Non-interactive demo: runs sample scenarios and prints the output (used for the report)."""
from assistant import Assistant

app = Assistant()
print(f"Index: {app.index.N} guides, {len(app.index.postings)} distinct terms | KB: {len(app.kb.symptoms)} facts, {len(app.kb.rules)} rules\n")

def title(t): print("\n" + "#" * 78 + f"\n# {t}\n" + "#" * 78)

title("RUN 1 - IR search: 'how to stop bleeding from a deep cut'")
for g in app.search("how to stop bleeding from a deep cut", 3):
    print(f"  {g['score']:.3f}  {g['title']}\n         {g['snippet']}")

title("RUN 2 - Typed question: 'My friend has a burn with large blisters, what should I do?'")
print(app.render(app.from_text("My friend has a burn with large blisters, what should I do?")))

title("RUN 3 - Symptom selection: choking + cannot breathe/speak + baby")
print(app.render(app.from_symptoms({"choking", "cannot_breathe_speak", "infant"})))

title("RUN 4 - Typed question: 'She fainted but woke up after a few seconds, does she need a hospital?'")
print(app.render(app.from_text("She fainted but woke up after a few seconds, does she need a hospital?")))

title("RUN 5 - Typed question: 'I got a small cut on my finger'")
print(app.render(app.from_text("I got a small cut on my finger")))
