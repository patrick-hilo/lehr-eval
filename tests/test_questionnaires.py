from lehr_eval.questionnaires import questionnaire_for_grade


def test_grades_one_to_six_use_lower_questionnaire():
    assert questionnaire_for_grade(1).kind == "unterstufe"
    assert questionnaire_for_grade(6).kind == "unterstufe"


def test_grades_seven_to_ten_use_upper_questionnaire():
    assert questionnaire_for_grade(7).kind == "oberstufe"
    assert questionnaire_for_grade(10).kind == "oberstufe"


def test_questionnaire_has_ten_items():
    assert len(questionnaire_for_grade(4).items) == 10
    assert len(questionnaire_for_grade(9).items) == 10
