"""Knowledge base with keyword-based context retrieval from .md files."""

import os
import re
import glob


class KnowledgeBase:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")
        self.base_dir = base_dir
        self._documents = []
        self._load_documents()

    def _load_documents(self):
        if not os.path.isdir(self.base_dir):
            return
        for path in sorted(glob.glob(os.path.join(self.base_dir, "**", "*.md"), recursive=True)):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                rel = os.path.relpath(path, self.base_dir)
                chunks = self._chunk_content(content)
                for i, chunk in enumerate(chunks):
                    self._documents.append({
                        "source": rel,
                        "chunk": i,
                        "content": chunk,
                    })
            except Exception:
                pass

    def _chunk_content(self, text, max_chars=1000):
        chunks = []
        paragraphs = text.split("\n\n")
        current = ""
        for para in paragraphs:
            if len(current) + len(para) > max_chars and current:
                chunks.append(current.strip())
                current = para
            else:
                current += "\n\n" + para if current else para
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [text.strip()]

    def query(self, query: str, top_k: int = 5):
        if not self._documents:
            return []
        query_lower = query.lower()
        query_terms = set(re.findall(r"\w+", query_lower))

        scored = []
        for doc in self._documents:
            content_lower = doc["content"].lower()
            term_matches = sum(1 for t in query_terms if t in content_lower)
            if term_matches > 0:
                score = term_matches / len(query_terms)
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"score": s, "source": d["source"], "content": d["content"][:500]}
            for s, d in scored[:top_k]
        ]
