import json
import logging
from pathlib import Path

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


class QueryEngine:
    def __init__(self):
        self._model = None
        self._index = None
        self._documents = {}

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            return True
        except ImportError:
            return False

    def index_notes(self, notes: list[dict]):
        if not self._load_model():
            return 0
        texts = []
        for n in notes:
            content = f"{n.get('title', '')} {n.get('content', '')} {n.get('path', '')}"
            texts.append(content)
            self._documents[n.get('path', '')] = n
        if texts:
            import faiss
            import numpy as np
            embeddings = self._model.encode(texts)
            dim = embeddings.shape[1]
            self._index = faiss.IndexFlatL2(dim)
            self._index.add(np.array(embeddings))
        return len(texts)

    def query(self, natural_query: str, top_k: int = 5) -> list[dict]:
        if self._index is None or self._model is None:
            return [{"error": "Index not initialized. Call index_notes first."}]
        import numpy as np
        query_vec = self._model.encode([natural_query])
        distances, indices = self._index.search(np.array(query_vec), top_k)
        results = []
        paths = list(self._documents.keys())
        for i, idx in enumerate(indices[0]):
            if idx < len(paths):
                path = paths[idx]
                doc = self._documents.get(path, {})
                results.append({
                    "path": path,
                    "title": doc.get("title", ""),
                    "score": float(1.0 / (1.0 + distances[0][i])),
                    "snippet": doc.get("content", "")[:300],
                })
        return results


_engine = QueryEngine()


AKATSUKI_QUERY_SCHEMA = {
    "name": "akatsuki_query",
    "description": "Natural Language Query Engine — search Obsidian notes using semantic similarity. Ask questions in natural language and find relevant notes, findings, and intelligence.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["query", "index"],
                "description": "query: search notes; index: re-index all notes",
            },
            "query": {
                "type": "string",
                "description": "Natural language query (required for query action)",
            },
            "notes_json": {
                "type": "string",
                "description": "JSON array of note dicts for indexing (required for index action)",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of top results to return (default: 5)",
            },
        },
        "required": ["action"],
    },
}


def akatsuki_query(action: str, query: str = "", notes_json: str = "[]",
                   top_k: int = 5) -> str:
    if action == "index":
        try:
            notes = json.loads(notes_json) if isinstance(notes_json, str) else notes_json
        except json.JSONDecodeError:
            return tool_error("Invalid notes_json")
        count = _engine.index_notes(notes)
        if count == 0:
            return tool_error("Failed to index notes (sentence-transformers required)")
        return tool_result({"indexed": count, "status": "ready"})

    if action == "query":
        if not query:
            return tool_error("query is required")
        results = _engine.query(query, top_k=min(top_k, 20))
        return tool_result({"query": query, "results": results, "count": len(results)})

    return tool_error(f"Unknown action: {action}")


def check_akatsuki_query_requirements() -> bool:
    try:
        import sentence_transformers
        import faiss
        return True
    except ImportError:
        return False


registry.register(
    name="akatsuki_query",
    toolset="akatsuki",
    schema=AKATSUKI_QUERY_SCHEMA,
    handler=lambda args, **kw: akatsuki_query(
        action=args["action"],
        query=args.get("query", ""),
        notes_json=args.get("notes_json", "[]"),
        top_k=args.get("top_k", 5),
    ),
    check_fn=check_akatsuki_query_requirements,
    emoji="🔎",
)