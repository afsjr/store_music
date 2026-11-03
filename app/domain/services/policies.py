from __future__ import annotations

from app.domain.models import Citation, PolicyChunk, StoreInfo
from app.domain.ports import PolicyRetriever, StoreInfoProvider


class PolicyService:
    def __init__(self, retriever: PolicyRetriever, store_info: StoreInfoProvider) -> None:
        self.retriever = retriever
        self.store_info_provider = store_info

    def search(self, question: str, k: int = 3) -> list[PolicyChunk]:
        return self.retriever.search(question, k=k)

    def citations(self, chunks: list[PolicyChunk]) -> list[Citation]:
        seen: set[tuple[str, int]] = set()
        citations: list[Citation] = []
        for chunk in chunks:
            key = (chunk.section, chunk.page)
            if key in seen:
                continue
            seen.add(key)
            citations.append(Citation(section=chunk.section, page=chunk.page))
        return citations

    def store_info(self) -> StoreInfo:
        return self.store_info_provider.get_store_info()

    def chunks_to_dict(self, chunks: list[PolicyChunk]) -> list[dict]:
        return [
            {
                "secao": chunk.section,
                "pagina": chunk.page,
                "titulo": chunk.title,
                "trecho": chunk.content,
                "score": chunk.score,
            }
            for chunk in chunks
        ]

    def store_info_to_dict(self) -> dict:
        info = self.store_info()
        return {
            "nome_fantasia": info.trade_name,
            "razao_social": info.legal_name,
            "cnpj": info.cnpj,
            "endereco": info.address,
            "telefone": info.phone,
            "whatsapp": info.whatsapp,
            "email": info.email,
            "horarios": info.hours,
            "fonte": info.source,
        }
