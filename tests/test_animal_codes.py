import pytest

from lehr_eval.animal_codes import code_for_index


def test_first_forty_codes_are_plain_animals():
    codes = [code_for_index(i) for i in range(40)]

    assert len(set(codes)) == 40
    assert all(" " not in code for code in codes)


def test_codes_after_forty_use_positive_or_neutral_adjectives():
    code = code_for_index(40)

    assert " " in code
    assert not code.startswith("fauler ")


def test_negative_index_raises_clear_error():
    with pytest.raises(ValueError, match="negative index"):
        code_for_index(-1)
