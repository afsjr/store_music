from __future__ import annotations


def test_retrieves_return_policy(policies):
    chunks = policies.search("posso devolver um pedido?")
    assert chunks
    assert chunks[0].section == "4.1"
    assert "7" in chunks[0].content or "sete" in chunks[0].content.lower()


def test_retrieves_hours(policies):
    chunks = policies.search("qual o horário de funcionamento?")
    assert chunks
    assert chunks[0].section == "2"


def test_retrieves_payment(policies):
    chunks = policies.search("quais as formas de pagamento?")
    assert chunks
    assert chunks[0].section == "3"


def test_retrieves_shipping_for_other_cities(policies):
    chunks = policies.search("como funciona o frete para outras cidades?")
    assert chunks
    assert chunks[0].section in {"5", "5.1", "5.2"}


def test_retrieves_warranty(policies):
    chunks = policies.search("qual a garantia para defeito?")
    assert chunks
    assert chunks[0].section in {"8", "4.2"}


def test_citations_are_unique(policies):
    chunks = policies.search("devolução e troca", k=3)
    citations = policies.citations(chunks)
    assert citations
    keys = {(citation.section, citation.page) for citation in citations}
    assert len(keys) == len(citations)


def test_store_info(policies):
    info = policies.store_info_to_dict()
    assert info["nome_fantasia"] == "Empório da Música"
    assert "14 de Maio" in info["endereco"]
    assert info["horarios"]["domingo_e_feriados"] == "Fechado"
