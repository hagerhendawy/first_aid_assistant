"""Information Retrieval: inverted index + TF-IDF weighting + cosine similarity."""
import math, re
from collections import defaultdict

STOPWORDS = set("""a an the and or of to in on is are was were be been being it its this that these those for with as at by
from my me i you your he she they them his her we our do does did what should how can will would could if then than so
there here also very just about into out up over after before when which who whom""".split())


def stem(w):
    for suf in ("ingly", "edly", "ing", "ed", "ly", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[: -len(suf)]
            break
    if len(w) > 3 and w.endswith("e"):
        w = w[:-1]
    return w


def tokenize(text):
    words = re.findall(r"[a-z0-9']+", text.lower().replace("\u2019", "'"))
    out = []
    for w in words:
        w = w.replace("'", "")
        if len(w) < 2 or w in STOPWORDS:
            continue
        out.append(stem(w))
    return out


class InvertedIndex:
    def __init__(self):
        self.postings = defaultdict(dict)   # term -> {doc_id: tf}
        self.docs = {}
        self.idf = {}
        self.norm = {}
        self.N = 0

    @staticmethod
    def _w(tf, idf):
        return (1 + math.log10(tf)) * idf

    def build(self, guides):
        self.postings.clear(); self.docs = dict(guides); self.idf = {}; self.norm = {}
        self.N = len(guides)
        for did, g in guides.items():
            tokens = tokenize((g["title"] + " ") * 3 + g["text"])   # title boosted x3
            counts = defaultdict(int)
            for t in tokens:
                counts[t] += 1
            for t, c in counts.items():
                self.postings[t][did] = c
        for t, plist in self.postings.items():
            self.idf[t] = math.log((1 + self.N) / (1 + len(plist))) + 1   # smoothed IDF
        sq = defaultdict(float)
        for t, plist in self.postings.items():
            for did, tf in plist.items():
                sq[did] += self._w(tf, self.idf[t]) ** 2
        self.norm = {d: math.sqrt(v) for d, v in sq.items()}

    def search(self, query, k=3, min_score=0.06):
        q_tokens = tokenize(query)
        if not q_tokens or not self.N:
            return []
        qtf = defaultdict(int)
        for t in q_tokens:
            qtf[t] += 1
        qw = {t: self._w(c, self.idf[t]) for t, c in qtf.items() if t in self.idf}
        qnorm = math.sqrt(sum(v * v for v in qw.values()))
        if qnorm == 0:
            return []
        scores = defaultdict(float)
        for t, wq in qw.items():
            for did, tf in self.postings[t].items():
                scores[did] += wq * self._w(tf, self.idf[t])
        ranked = sorted(((d, s / (qnorm * self.norm[d])) for d, s in scores.items()), key=lambda x: -x[1])
        results = []
        for did, sc in ranked[:k]:
            if sc < min_score:
                break
            g = self.docs[did]
            results.append({"doc_id": did, "title": g["title"], "score": round(sc, 4),
                            "snippet": self._snippet(g["text"], set(qw))})
        return results

    @staticmethod
    def _snippet(text, qterms):
        best, best_n = "", -1
        for line in text.splitlines():
            line = line.strip()
            if len(line) < 15 or line.endswith(':'):
                continue
            n = len(qterms & set(tokenize(line)))
            if n > best_n:
                best, best_n = line, n
        return best if len(best) <= 150 else best[:147] + "..."
