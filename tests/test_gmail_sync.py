def test_parse_tetra_thankyou():
    from scripts.gmail_sync import parse_gmail_to_status
    assert parse_gmail_to_status("Thank you for your interest! Tetra Pak", "myLink.noreply@mylink.tetrapak.com") == "aplicada"

def test_parse_bumeran_aplicada():
    from scripts.gmail_sync import parse_gmail_to_status
    assert parse_gmail_to_status("Ya recibieron tu postulación — Pasante Digital", "no_reply@bumeran.com") == "aplicada"

def test_parse_wetcom_waiting():
    from scripts.gmail_sync import parse_gmail_to_status
    assert parse_gmail_to_status("seguimos avanzando con el proceso", "rrhh@wetcom.com") == "entrevista"
