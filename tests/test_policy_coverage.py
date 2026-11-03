from __future__ import annotations

import pytest

from app.agent.guardrails import needs_policy_retrieval
from app.domain.text import normalize_text

POLICY_CASES = [
    ("qual o horário de funcionamento?", "2", ["09:00", "18:00"]),
    ("quais as formas de pagamento?", "3", ["PIX", "12x", "boleto"]),
    ("como funciona o parcelamento em 6x?", "3.1", ["R$ 80,00", "R$ 100,00"]),
    ("posso devolver em 7 dias por arrependimento?", "4.1", ["7", "sete"]),
    ("meu instrumento deu defeito, posso trocar?", "4.2", ["30", "fabricante"]),
    ("quero trocar por outra cor", "4.3", ["preferência", "7 dias"]),
    ("instrumento com setup pode ser trocado?", "4.4", ["setup", "regulagem"]),
    ("frete grátis em Campo Grande", "5.1", ["R$ 500,00", "R$ 35,00"]),
    ("prazo de entrega para Dourados", "5.2", ["PAC", "SEDEX", "Jadlog"]),
    ("como funciona o rastreamento?", "5.3", ["rastreamento", "BR"]),
    ("quais promoções vocês fazem?", "6.1", ["Black Friday", "Aniversário"]),
    ("promoção é cumulativa com PIX?", "6.2", ["cumulativas", "rain check"]),
    ("qual o tempo de resposta no WhatsApp?", "7.1", ["5 minutos"]),
    ("e se o produto estiver esgotado?", "7.3", ["fora de estoque", "descontinuado"]),
    ("qual a garantia legal?", "8.1", ["90"]),
    ("qual a garantia do fabricante?", "8.2", ["6 meses", "2 anos"]),
    ("o que não cobre a garantia?", "8.3", ["desgaste natural", "mau uso"]),
    ("como vocês tratam meus dados?", "9", ["LGPD", "exclusão"]),
    ("quando a loja foi fundada?", "1.2", ["2008"]),
]


@pytest.mark.parametrize(("query", "expected_section", "key_facts"), POLICY_CASES)
def test_policy_question_recovers_expected_section(policies, query, expected_section, key_facts):
    chunks = policies.search(query, k=3)
    assert chunks, f"Nenhum trecho recuperado para: {query}"

    sections = [chunk.section for chunk in chunks]
    assert expected_section in sections, f"{query!r} recuperou {sections}"

    section_chunk = next(chunk for chunk in chunks if chunk.section == expected_section)
    content = normalize_text(section_chunk.content)
    for fact in key_facts:
        assert normalize_text(fact) in content, f"{fact!r} ausente na seção {expected_section}"


POLICY_TRIGGERS = [
    "meu instrumento deu defeito",
    "quanto tempo tenho de garantia?",
    "qual o prazo de entrega?",
    "aceita cartão de crédito?",
    "posso pagar no boleto?",
    "tem desconto no PIX?",
    "posso parcelar em 6x?",
    "a loja está aberta agora?",
    "quando a loja foi fundada?",
    "como vocês tratam meus dados?",
    "quero excluir meus dados",
    "vocês dão rain check?",
    "qual o prazo do SEDEX?",
    "o frete tem seguro contra avaria?",
    "boquilha pode ser trocada?",
    "produto de venda final tem troca?",
    "instrumento com regulagem pode ser devolvido?",
    "posso trocar por preferência?",
    "qual o tempo de resposta fora do expediente?",
]


@pytest.mark.parametrize("message", POLICY_TRIGGERS)
def test_policy_terms_trigger_retrieval(message):
    assert needs_policy_retrieval(message) is True


PRODUCT_QUERIES = [
    "Quanto custa o Takamine GD20?",
    "Quais violões custam até R$ 1000?",
    "Vocês têm o Giannini GF-3D?",
    "Quero comprar uma guitarra",
    "Me mostra o Kalani KAL-700T",
]


@pytest.mark.parametrize("message", PRODUCT_QUERIES)
def test_product_queries_do_not_trigger_policy_retrieval(message):
    assert needs_policy_retrieval(message) is False
