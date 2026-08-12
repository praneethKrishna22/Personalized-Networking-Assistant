import pytest

from backend.services.theme_extractor import ThemeExtractor


def test_extract_themes_empty_text():
    extractor = ThemeExtractor()
    assert extractor.extract_themes("") == []
    assert extractor.extract_themes("   ") == []


@pytest.mark.slow
def test_extract_themes_real_model():
    """Loads the actual DistilBERT NLI model - slow, run explicitly with:
    pytest -m slow
    """
    extractor = ThemeExtractor()
    themes = extractor.extract_themes(
        "AI for Sustainable Cities", extra_labels=["climate change", "urban planning"]
    )
    assert isinstance(themes, list)
    assert len(themes) > 0
    assert all(isinstance(t, str) for t in themes)
