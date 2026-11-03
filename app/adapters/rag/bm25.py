from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable

from app.adapters.rag.pdf_loader import normalize_text
from app.domain.models import PolicyChunk

TOKEN_RE = re.compile(r"(?u)\b\w+\b")
STOPWORDS = {
    "a",
    "o",
    "as",
    "os",
    "de",
    "da",
    "do",
    "das",
    "dos",
    "e",
    "em",
    "na",
    "no",
    "nas",
    "nos",
    "para",
    "por",
    "com",
    "um",
    "uma",
    "que",
    "se",
    "ao",
    "aos",
    "ou",
    "como",
    "mais",
    "foi",
    "ser",
    "sua",
    "seu",
    "suas",
    "seus",
    "pelo",
    "pela",
    "este",
    "esta",
    "isso",
    "tem",
    "ter",
    "voce",
    "voces",
    "qual",
    "quais",
    "quando",
    "onde",
    "porque",
    "sobre",
    "entre",
    "sem",
    "ate",
    "apos",
    "antes",
    "posso",
    "poderia",
    "gostaria",
}

QUERY_EXPANSIONS = {
    "devolv": "devolução devolver arrependimento reembolso troca",
    "arrepend": "arrependimento devolução reembolso",
    "troc": "troca defeito preferência",
    "garant": "garantia defeito fabricante",
    "pagament": "pagamento pix cartão crédito débito boleto parcelamento",
    "parcel": "parcelamento cartão crédito sem juros",
    "horari": "horário funcionamento aberto fechado",
    "fret": "frete entrega prazo correios sedex pac jadlog",
    "entreg": "entrega frete prazo rastreamento",
    "enderec": "endereço rua centro campo grande",
    "promoc": "promoção desconto black friday",
    "descont": "desconto promoção pix",
    "acessori": "acessório cordas palhetas cabos cases pedais amplificadores",
    "privacidade": "lgpd dados pessoais privacidade",
}


def expand_query(query: str) -> str:
    normalized = normalize_text(query)
    additions = [text for key, text in QUERY_EXPANSIONS.items() if key in normalized]
    return f"{query} {' '.join(additions)}".strip()


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_RE.findall(normalize_text(text))
        if len(token) > 1 and token not in STOPWORDS
    ]


class BM25PolicyRetriever:
    """BM25 lexical para o manual de políticas, sem dependências pesadas."""

    def __init__(self, chunks: Iterable[PolicyChunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = list(chunks)
        self.k1 = k1
        self.b = b
        self.documents = [tokenize(f"{chunk.title} {chunk.content}") for chunk in self.chunks]
        self.doc_freqs = [Counter(document) for document in self.documents]
        self.avgdl = (
            sum(len(document) for document in self.documents) / len(self.documents)
            if self.documents
            else 0.0
        )
        document_frequency: Counter = Counter()
        for document in self.documents:
            for term in set(document):
                document_frequency[term] += 1
        total = len(self.documents)
        self.idf = {
            term: math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def _score(self, query_tokens: list[str], document_index: int) -> float:
        document = self.documents[document_index]
        frequencies = self.doc_freqs[document_index]
        document_length = len(document)
        score = 0.0
        for token in query_tokens:
            frequency = frequencies.get(token, 0)
            if frequency == 0:
                continue
            idf = self.idf.get(token, 0.0)
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * document_length / (self.avgdl or 1.0)
            )
            score += idf * (frequency * (self.k1 + 1)) / denominator
        return score

    def search(self, query: str, k: int = 3) -> list[PolicyChunk]:
        if not self.chunks:
            return []
        query_tokens = tokenize(expand_query(query))
        if not query_tokens:
            return []
        scored = [(index, self._score(query_tokens, index)) for index in range(len(self.chunks))]
        scored.sort(key=lambda item: item[1], reverse=True)
        results: list[PolicyChunk] = []
        for index, score in scored[:k]:
            if score <= 0:
                continue
            results.append(self.chunks[index].model_copy(update={"score": round(float(score), 4)}))
        return results

    def count(self) -> int:
        return len(self.chunks)
