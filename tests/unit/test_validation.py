import pytest

from src.actions.api.validation import reject_blank_text


@pytest.mark.parametrize("value", ["hello", " hello ", "0"])
def test_reject_blank_text_accepts_non_blank_strings(value):
    assert reject_blank_text(value) == value


@pytest.mark.parametrize("value", [None, 0, 12, 1.5, True, ["x"], {"a": 1}])
def test_reject_blank_text_passes_through_non_strings(value):
    assert reject_blank_text(value) is value


@pytest.mark.parametrize("value", ["", " ", "\t", "\n", "   \n\t  "])
def test_reject_blank_text_rejects_blank_strings(value):
    with pytest.raises(ValueError, match="must not be empty"):
        reject_blank_text(value)
