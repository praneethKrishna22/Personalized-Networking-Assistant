from backend.services.fact_checker import FactChecker


def test_fact_check_empty_query():
    checker = FactChecker()
    result = checker.check("")
    assert result["found"] is False
    assert result["summary"] is None


def test_fact_check_success_mocked(monkeypatch):
    import backend.services.fact_checker as fc_module

    class FakePage:
        url = "https://en.wikipedia.org/wiki/Blockchain"

    monkeypatch.setattr(
        fc_module.wikipedia,
        "summary",
        lambda query, sentences, auto_suggest: "Blockchain is a distributed ledger technology.",
    )
    monkeypatch.setattr(fc_module.wikipedia, "page", lambda query, auto_suggest: FakePage())

    checker = FactChecker()
    result = checker.check("blockchain")

    assert result["found"] is True
    assert "Blockchain" in result["summary"]
    assert result["url"].startswith("https://en.wikipedia.org")


def test_fact_check_disambiguation_mocked(monkeypatch):
    import backend.services.fact_checker as fc_module

    def raise_disambiguation(query, sentences, auto_suggest):
        raise fc_module.wikipedia.exceptions.DisambiguationError("mercury", ["Mercury (planet)", "Mercury (element)"])

    monkeypatch.setattr(fc_module.wikipedia, "summary", raise_disambiguation)

    checker = FactChecker()
    result = checker.check("mercury")

    assert result["found"] is False
    assert len(result["options"]) > 0
