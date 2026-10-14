from datetime import date

from scripts import buscar_portales as search


def test_ambiguous_geography_never_enters_fresh_queue(tmp_path):
    unverified = tmp_path / "unverified.tsv"
    job = {"fecha": "2026-10-14", "titulo": "AI Intern", "estado": "GEO_NO_VERIFICADA", "url": "https://example.com/job"}
    fresh, secondary = search._filter_fresh([job], "himalayas", today=date(2026, 10, 14), unverified_path=unverified)
    assert fresh == []
    assert secondary == []
    assert "elegibilidad geográfica" in unverified.read_text(encoding="utf-8")


def test_jobicy_keeps_argentina_and_worldwide_entry_roles(monkeypatch):
    def fake(url):
        return {"jobs": [
            {"id": 1, "jobTitle": "AI Intern", "companyName": "A", "jobGeo": "Anywhere", "pubDate": "2026-10-14T12:00:00Z", "jobType": ["Part-Time"], "url": "https://jobicy.com/jobs/1"},
            {"id": 2, "jobTitle": "QA Junior", "companyName": "B", "jobGeo": "Argentina", "pubDate": "2026-10-14", "url": "https://jobicy.com/jobs/2"},
            {"id": 3, "jobTitle": "Senior Engineer", "companyName": "C", "jobGeo": "USA", "pubDate": "2026-10-14", "url": "https://jobicy.com/jobs/3"},
        ], "nextCursor": None}

    monkeypatch.setattr(search, "_get_json", fake)
    jobs = search.scrape_jobicy()
    assert [job["job_id"] for job in jobs] == ["1", "2"]
    assert all(job["estado"] == "GEO_NO_VERIFICADA" for job in jobs)


def test_himalayas_rejects_restricted_countries_and_keeps_argentina(monkeypatch):
    def fake(url):
        return {"jobs": [
            {"guid": "ar", "title": "QA Intern", "companyName": "A", "locationRestrictions": ["AR"], "pubDate": "2026-10-14", "applicationLink": "https://himalayas.app/jobs/ar"},
            {"guid": "us", "title": "AI Intern", "companyName": "B", "locationRestrictions": ["US"], "pubDate": "2026-10-14", "applicationLink": "https://himalayas.app/jobs/us"},
        ]}

    monkeypatch.setattr(search, "_get_json", fake)
    jobs = search.scrape_himalayas()
    assert [job["job_id"] for job in jobs] == ["ar"]


def test_remotive_keeps_reachable_entry_role_and_source_link(monkeypatch):
    def fake(url):
        return {"jobs": [
            {"id": 10, "title": "Junior Data Analyst", "company_name": "A", "candidate_required_location": "LATAM", "publication_date": "2026-10-13", "url": "https://remotive.com/remote-jobs/10"},
            {"id": 11, "title": "Senior Data Analyst", "company_name": "B", "candidate_required_location": "USA", "publication_date": "2026-10-13", "url": "https://remotive.com/remote-jobs/11"},
        ]}

    monkeypatch.setattr(search, "_get_json", fake)
    jobs = search.scrape_remotive()
    assert [job["job_id"] for job in jobs] == ["10"]
    assert jobs[0]["url"].startswith("https://remotive.com/")


def test_arbeitnow_rejects_europe_only_role(monkeypatch):
    def fake(url):
        return {"data": [
            {"slug": "ar", "title": "QA Intern", "company_name": "A", "location": "Remote Worldwide", "remote": True, "created_at": 1791900000, "url": "https://www.arbeitnow.com/view/ar"},
            {"slug": "de", "title": "QA Intern", "company_name": "B", "location": "Berlin, Germany", "remote": True, "created_at": 1791900000, "url": "https://www.arbeitnow.com/view/de"},
        ]}

    monkeypatch.setattr(search, "_get_json", fake)
    jobs = search.scrape_arbeitnow()
    assert [job["job_id"] for job in jobs] == ["ar"]
