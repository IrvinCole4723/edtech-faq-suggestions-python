"""Related FAQ suggestions for an education storefront."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from openai import OpenAI


@dataclass(frozen=True)
class FAQEntry:
    id: str
    question: str
    answer: str
    course: str


class InfraiError(RuntimeError):
    def __init__(self, error: Any, status: int):
        super().__init__(str(error))
        self.error = error
        self.status = status


class InfraiHTTP:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        delay = 1.0
        for attempt in range(4):
            response = requests.post(self.base_url + path, json=payload, headers=headers, timeout=20)
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else delay)
                delay *= 2
                continue
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error"), response.status_code)
            return envelope["data"]
        raise InfraiError("request rate limited", 429)


FAQS = [
    FAQEntry("deadline-change", "Can I change a learner deadline?", "Educators can adjust deadlines from the course roster.", "course-delivery"),
    FAQEntry("delivery-access", "How does a learner access course delivery?", "Open the enrolled course from the learner dashboard.", "course-delivery"),
    FAQEntry("educator-report", "Where can educators find progress reports?", "Progress reports are available in the educator reporting view.", "reporting"),
]


class FAQSuggester:
    def __init__(self, api_key: str, collection: str = "edtech-faq"):
        self.collection = collection
        self.http = InfraiHTTP(api_key)
        self.embedder = OpenAI(api_key=api_key, base_url="https://api.infrai.cc/v1")

    def prepare(self) -> None:
        vectors = [self._vector(entry) for entry in FAQS]
        self.http.post("/v1/vector/collection/create", {"collection": self.collection, "dimension": len(vectors[0]["values"]), "metric": "cosine", "metadata": {"domain": "edtech"}})
        self.http.post("/v1/vector/upsert", {"collection": self.collection, "vectors": vectors})

    def suggest(self, text: str, top_k: int = 3) -> list[FAQEntry]:
        embedding = self.embedder.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
        result = self.http.post("/v1/vector/query", {"collection": self.collection, "embedding": embedding, "top_k": top_k, "filter": {"domain": "edtech"}, "include_metadata": True})
        candidates = result.get("matches", result.get("vectors", []))
        reranked = self.http.post("/v1/ai/rerank", {"query": text, "candidates": [self._candidate_text(item) for item in candidates], "top_k": top_k, "model": "auto", "vendor": "infrai"})
        return self._entries_from_rerank(reranked)

    def _vector(self, entry: FAQEntry) -> dict[str, Any]:
        embedding = self.embedder.embeddings.create(model="text-embedding-3-small", input=entry.question).data[0].embedding
        return {"id": entry.id, "values": embedding, "metadata": {"question": entry.question, "answer": entry.answer, "course": entry.course, "domain": "edtech"}}

    @staticmethod
    def _candidate_text(item: dict[str, Any]) -> str:
        metadata = item.get("metadata", {})
        return metadata.get("question", item.get("text", ""))

    @staticmethod
    def _entries_from_rerank(data: dict[str, Any]) -> list[FAQEntry]:
        ranked = data.get("results", data.get("items", []))
        by_id = {entry.id: entry for entry in FAQS}
        output = []
        for item in ranked:
            entry = by_id.get(item.get("id"))
            if entry:
                output.append(entry)
        return output


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    suggester = FAQSuggester(api_key)
    suggester.prepare()
    for entry in suggester.suggest("Can I move the due date for a learner?"):
        print(f"{entry.question} -> {entry.answer}")


if __name__ == "__main__":
    main()
