def test_morning_ok_evening_blocked():
    from scripts.calendar_fit import score_compat
    # 9-13 L-V pisa Ritual Vie 10-12:30 → 80, 14-18 L-V pisa Psicóloga Lun 14:15 → 70, 18-22 veto UADE
    assert score_compat("9-13 L-V") == 80
    assert score_compat("14-18 L-V") <= 70
    assert score_compat("18-22 L-V") == 0

def test_friday_ritual():
    from scripts.calendar_fit import score_compat
    assert score_compat("10-14 Vie") <= 80
