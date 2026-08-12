from backend.services.starter_generator import StarterGenerator


def test_clean_candidates_filters_length():
    gen = StarterGenerator()
    text = (
        "Too short. "
        "This is a properly sized candidate sentence for testing purposes here. "
        "This one goes on for way too long and should be filtered out because it exceeds the thirty word ceiling that the cleaning function enforces on every single generated candidate sentence in this test case."
    )
    cleaned = gen._clean_candidates(text)
    assert len(cleaned) == 1
    assert 6 <= len(cleaned[0].split()) <= 31


def test_generate_starters_fallback_when_model_unavailable(monkeypatch):
    import backend.services.starter_generator as sg_module

    def fake_pipeline(*args, **kwargs):
        raise RuntimeError("model unavailable in this environment")

    monkeypatch.setattr(sg_module, "pipeline", fake_pipeline)

    gen = sg_module.StarterGenerator()
    starters = gen.generate_starters(["artificial intelligence"], ["climate change"], num_starters=3)

    assert len(starters) == 3
    assert all(isinstance(s, str) and s.strip() for s in starters)
    # fallback templates are personalized with the theme
    assert any("artificial intelligence" in s for s in starters)


def test_generate_starters_deduplicates(monkeypatch):
    import backend.services.starter_generator as sg_module

    class FakeTokenizer:
        eos_token_id = 0

    class FakeGenerator:
        tokenizer = FakeTokenizer()

        def __call__(self, prompt, **kwargs):
            n = kwargs.get("num_return_sequences", 1)
            # every generation is identical -> should be de-duplicated
            return [
                {"generated_text": prompt + "What excites you most about this topic?"}
                for _ in range(n)
            ]

    monkeypatch.setattr(sg_module, "pipeline", lambda *a, **k: FakeGenerator())
    monkeypatch.setattr(sg_module, "set_seed", lambda *a, **k: None)

    gen = sg_module.StarterGenerator()
    starters = gen.generate_starters(["AI"], ["data"], num_starters=3)

    assert len(starters) == 3
    # only one unique GPT-2 style starter should appear once, rest padded by fallback
    assert len([s for s in starters if "excites you most" in s]) == 1
