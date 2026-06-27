import pytest
from app.services.spell_corrector import SpellCorrector


def test_spell_corrector_init():
    corrector = SpellCorrector(["Python", "Deployment", "Docker"])
    assert corrector is not None


def test_spell_corrector_correct():
    corrector = SpellCorrector(["Python", "部署", "Docker"])
    result = corrector.correct("Pythn")
    assert result["has_correction"] is True
    assert result["corrected"] == "Python"


def test_spell_corrector_no_correction():
    corrector = SpellCorrector(["Python"])
    result = corrector.correct("Python")
    assert result["has_correction"] is False
    assert result["corrected"] is None


def test_spell_corrector_suggest_similar():
    corrector = SpellCorrector(["Python", "Pythonic", "Pytest"])
    suggestions = corrector.suggest_similar("Pythn")
    assert len(suggestions) > 0
    assert "Python" in suggestions


def test_edit_distance():
    corrector = SpellCorrector()
    assert corrector._edit_distance("Python", "Python") == 0
    assert corrector._edit_distance("Pythn", "Python") == 1
    assert corrector._edit_distance("Pthon", "Python") == 1


def test_add_to_dictionary():
    corrector = SpellCorrector()
    corrector.add_to_dictionary(["Kubernetes", "Container"])
    result = corrector.correct("Kubernets")
    assert result["has_correction"] is True
    assert result["corrected"] == "Kubernetes"
