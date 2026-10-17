"""Stdlib-only regression tests for identity, ranking and date evidence."""

import csv
import tempfile
import unittest
from datetime import date, time
from pathlib import Path

from scripts.opportunity_identity import identity_key
from scripts.calendar_fit import parse_jornada, score_compat
from scripts.opportunity_pipeline import build_pipeline, key_for, verified_publication_evidence
from scripts.opportunity_rank import deduplicate, rank


class OpportunityIdentityTests(unittest.TestCase):
    def test_same_stable_id_merges_but_different_ids_do_not(self):
        first = {"portal": "Greenhouse", "job_id": "123", "empresa": "Acme", "titulo": "Intern", "ubicacion": "CABA"}
        same = {**first, "url": "https://jobs.example/123?utm_source=li"}
        different = {**first, "job_id": "124"}
        self.assertEqual(identity_key(first)[0], identity_key(same)[0])
        self.assertNotEqual(key_for(first), key_for(different))

    def test_title_company_location_alone_do_not_merge_distinct_descriptions(self):
        first = {"portal": "linkedin", "empresa": "Acme", "titulo": "Analyst", "ubicacion": "Remote", "descripcion": "Python, reporting"}
        second = {**first, "descripcion": "Support tickets and Linux"}
        self.assertNotEqual(key_for(first), key_for(second))
        self.assertEqual(len(deduplicate([first, second])), 2)

    def test_same_canonical_url_preserves_all_source_records_and_ids(self):
        first = {"portal": "linkedin", "job_id": "li-1", "url": "https://jobs.example/role?utm_source=li", "titulo": "Intern"}
        second = {"portal": "greenhouse", "job_id": "gh-2", "url": "https://jobs.example/role", "titulo": "Intern"}
        merged = deduplicate([first, second])
        self.assertEqual(len(merged), 1)
        self.assertEqual(set(merged[0]["source_job_ids"]), {"li-1", "gh-2"})
        self.assertEqual(len(merged[0]["source_records"]), 2)

    def test_same_canonical_url_merges_across_sources_even_when_numeric_ids_match(self):
        a = {"portal": "uade", "job_id": "123", "url": "https://jobs.example/role", "titulo": "Intern"}
        b = {"portal": "company", "job_id": "123", "url": "https://jobs.example/role?utm_source=x", "titulo": "Intern"}
        self.assertEqual(len(deduplicate([a, b])), 1)

    def test_same_source_different_ids_remain_separate_even_with_same_url(self):
        a = {"portal": "uade", "job_id": "123", "url": "https://jobs.example/role", "titulo": "Intern"}
        b = {**a, "job_id": "124"}
        self.assertEqual(len(deduplicate([a, b])), 2)

    def test_richer_description_wins_but_both_source_observations_remain(self):
        short = {"portal": "uade", "job_id": "123", "url": "https://jobs.example/role", "titulo": "IT Intern", "descripcion": "IT support."}
        rich = {"portal": "company", "job_id": "456", "url": "https://jobs.example/role", "titulo": "IT Intern", "descripcion": "IT support, Windows, Microsoft 365, account management, tickets and inventory."}
        merged = deduplicate([short, rich])[0]
        self.assertEqual(merged["descripcion"], rich["descripcion"])
        self.assertEqual(len(merged["source_records"]), 2)


class OpportunityRankingTests(unittest.TestCase):
    def test_calendar_parser_accepts_minutes_and_unicode_dash(self):
        self.assertEqual(parse_jornada("08:00–14:00"), (time(8, 0), time(14, 0)))
        # The profile has a recurring Friday 10:00–12:30 block, so the
        # weekday-agnostic score is 80 rather than assuming full availability.
        self.assertEqual(score_compat("08-14"), 80)

    def test_calendar_conflict_uses_minute_precision(self):
        score = rank({
            "title": "IT Intern", "description": "IT support", "location": "CABA",
            "schedule": "17:30–18:50", "posting_status": "open", "closed": False,
            "publication_date_verified": True, "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        self.assertIn("horario explícitamente superpuesto con la cursada UADE", score["mandatory_gaps"])

    def test_verified_requirement_status_alone_does_not_verify_original_publication_date(self):
        score = rank({
            "title": "IT Intern", "description": "Python", "location": "CABA", "schedule": "20 hours",
            "posting_status": "open", "published_date": "2026-10-14",
            "verified_requirements": {"publication date": {"status": "verified", "evidence": "date visible"}},
        }, today=date(2026, 10, 14))
        self.assertEqual(score["freshness"], "unverified")

    def test_preferred_years_are_pending_not_a_hard_veto(self):
        score = rank({
            "title": "Data Analyst", "description": "3 years of experience preferred; Python and SQL.",
            "location": "CABA", "schedule": "20 hours", "posting_status": "open",
            "publication_date_verified": True, "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        self.assertNotEqual(score["eligibility"], "ineligible")
        self.assertTrue(any("3 años" in item for item in score["confirm"]))

    def test_ambiguous_years_are_pending_not_a_hard_veto(self):
        score = rank({
            "title": "Data Analyst", "description": "3 years of experience in reporting.",
            "location": "CABA", "schedule": "20 hours", "posting_status": "open",
            "publication_date_verified": True, "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        self.assertNotEqual(score["eligibility"], "ineligible")

    def test_word_boundaries_avoid_it_substrings_in_nontechnical_roles(self):
        score = rank({
            "title": "Employee Benefits Specialist", "description": "Benefits administration and financial wellness.",
            "profile_text": "Estudiante de Gestión de TI.", "location": "CABA", "schedule": "20 hours",
            "posting_status": "open", "closed": False, "publication_date_verified": True,
            "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        self.assertEqual(score["dimensions"]["carrera"]["score"], 1.0)

    def test_weighted_fit_uses_rubric_and_is_one_to_five(self):
        score = rank({"title": "Python Intern", "description": "Python, SQL; student; part-time 20 hours", "location": "Buenos Aires", "schedule": "20 hours", "posting_status": "open", "publication_date_verified": True, "published_date": "2026-10-14"}, today=date(2026, 10, 14))
        self.assertGreaterEqual(score["fit_score"], 1)
        self.assertLessEqual(score["fit_score"], 5)
        self.assertEqual(score["dimensions"]["evidencia_cv"]["weight"], 0.40)
        self.assertEqual(score["dimensions"]["jornada"]["weight"], 0.25)
        self.assertEqual(score["dimensions"]["compatibilidad_calendar"]["weight"], 0.15)

    def test_candidate_skills_come_from_profile_not_the_job_description(self):
        job = {
            "title": "Back Office",
            "description": "Procesar datos y Excel; part-time 20 horas.",
            "location": "CABA",
            "schedule": "20 hours",
            "posting_status": "open",
            "closed": False,
            "publication_date_verified": True,
            "published_date": "2026-10-14",
        }
        no_evidence = rank({**job, "profile_text": "Estudiante de Gestión de TI."}, today=date(2026, 10, 14))
        excel_evidence = rank({**job, "profile_text": "Experiencia demostrable usando Excel."}, today=date(2026, 10, 14))
        self.assertEqual(no_evidence["dimensions"]["evidencia_cv"]["score"], 1.0)
        self.assertEqual(excel_evidence["dimensions"]["evidencia_cv"]["score"], 3.0)
        self.assertIn("ninguna", no_evidence["dimensions"]["evidencia_cv"]["reason"])
        self.assertIn("excel", excel_evidence["dimensions"]["evidencia_cv"]["reason"].lower())

    def test_it_support_listing_is_classified_as_a_technology_role(self):
        score = rank({
            "title": "Pasante de Microinformática",
            "description": "Brindar soporte IT de primer nivel a usuarios.",
            "profile_text": "Estudiante de Gestión de TI.",
            "location": "Parque Patricios, Buenos Aires",
            "posting_status": "open",
            "closed": False,
            "publication_date_verified": True,
            "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        self.assertTrue(score["verification"]["inferred"][0]["value"])
        self.assertEqual(score["dimensions"]["carrera"]["score"], 5.0)

    def test_support_training_does_not_claim_windows_or_m365_experience(self):
        score = rank({
            "title": "Pasante de Microinformática",
            "description": "Soporte IT; configurar Windows y Microsoft 365.",
            "profile_text": "Red Hat RH124; Cisco CCNA: Introduction to Networks.",
            "location": "Parque Patricios, Buenos Aires",
            "posting_status": "open",
            "closed": False,
            "publication_date_verified": True,
            "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        evidence = score["dimensions"]["evidencia_cv"]
        self.assertEqual(evidence["score"], 3.0)
        aligned = evidence["reason"].split(";", 1)[0]
        detected = evidence["reason"].split(";", 1)[1]
        self.assertIn("support", aligned)
        self.assertNotIn("windows_m365", aligned)
        self.assertIn("windows_m365", detected)

    def test_unrelated_word_containing_ai_does_not_raise_career_fit(self):
        score = rank({
            "title": "Programa de Pasantías 2026",
            "description": "Pasantías en energía, comercio y recursos humanos.",
            "profile_text": "Estudiante de Gestión de TI.",
            "location": "Vicente López, Buenos Aires",
            "schedule": "20 horas semanales",
            "posting_status": "open",
            "closed": False,
            "publication_date_verified": True,
            "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        self.assertEqual(score["dimensions"]["carrera"]["score"], 1.0)

    def test_verified_requirements_resolve_unknowns_but_mandatory_gaps_veto(self):
        base = {"title": "IT Intern", "description": "Python intern", "location": "Buenos Aires", "schedule": "20 hours", "closed": False, "publication_date_verified": True, "published_date": "2026-10-14"}
        unchecked = rank(base, today=date(2026, 10, 14))
        checked = rank({**base, "posting_status": "open", "verified_requirements": {
            "academic requirement": {"status": "met", "evidence": "Official posting"},
            "schedule": {"status": "met"},
            "location": {"status": "met"},
            "experience": {"status": "met"},
            "publication date": {"status": "verified"},
        }}, today=date(2026, 10, 14))
        self.assertEqual(unchecked["eligibility"], "uncertain")
        self.assertNotEqual(checked["eligibility"], "uncertain")
        vetoed = rank({**base, "mandatory_gaps": ["Requires 3 years experience"]}, today=date(2026, 10, 14))
        self.assertEqual(vetoed["eligibility"], "ineligible")
        self.assertEqual(vetoed["fit_score"], 0)
        self.assertEqual(vetoed["priority"], 0)

    def test_closed_and_unverified_dates_cannot_rank_as_current(self):
        closed = rank({"title": "Data Intern", "description": "Python", "location": "CABA", "schedule": "20 hours", "closed": True, "publication_date_verified": True, "published_date": "2026-10-14"}, today=date(2026, 10, 14))
        date_signal_only = rank({"title": "Data Intern", "description": "Python", "location": "CABA", "schedule": "20 hours", "closed": False, "published_date": "2026-10-14"}, today=date(2026, 10, 14))
        self.assertEqual(closed["eligibility"], "ineligible")
        self.assertEqual(date_signal_only["freshness"], "unverified")

    def test_experience_ranges_and_intervening_words_are_detected(self):
        base = {"title": "Principal Salesforce Consultant", "location": "Argentina remote", "schedule": "Full Time", "posting_status": "open", "publication_date_verified": True, "published_date": "2026-10-14"}
        principal = rank({**base, "description": "Requires 10–15 years of Salesforce consulting experience."}, today=date(2026, 10, 14))
        senior = rank({**base, "title": "Senior Security Engineer", "description": "6+ years of professional software engineering experience."}, today=date(2026, 10, 14))
        self.assertEqual(principal["eligibility"], "ineligible")
        self.assertIn("exige 15 años de experiencia profesional", principal["mandatory_gaps"])
        self.assertEqual(senior["eligibility"], "ineligible")
        self.assertIn("exige 6 años de experiencia profesional", senior["mandatory_gaps"])

    def test_required_near_native_english_is_a_b1_mismatch(self):
        score = rank({
            "title": "Technical Support Engineer",
            "description": "Required Experience and Technical Skills: Native or near-native English, comfortable leading calls with US customers.",
            "location": "Argentina remote", "schedule": "full-time", "posting_status": "open",
            "publication_date_verified": True, "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        self.assertEqual(score["eligibility"], "ineligible")
        self.assertTrue(any("inglés avanzado" in gap for gap in score["mandatory_gaps"]))

    def test_related_experience_months_are_left_pending_without_candidate_evidence(self):
        score = rank({
            "title": "Back Office",
            "description": "Experiencia mínima de 6 meses en procesamiento de información y/o datos.",
            "location": "CABA", "schedule": "Part-time 08:00-14:00", "posting_status": "open",
            "publication_date_verified": True, "published_date": "2026-10-14",
        }, today=date(2026, 10, 14))
        self.assertEqual(score["eligibility"], "uncertain")
        self.assertTrue(any("6 meses" in item for item in score["confirm"]))


class PublicationEvidenceTests(unittest.TestCase):
    def test_four_day_primary_window_keeps_five_day_listing_secondary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.tsv"
            fields = ["portal", "job_id", "empresa", "titulo", "ubicacion", "url", "fecha", "descripcion", "jornada", "modalidad"]
            rows = [
                {"portal": "greenhouse", "job_id": "gh-4", "empresa": "Acme", "titulo": "IT Intern", "ubicacion": "CABA", "url": "https://jobs.example/4", "fecha": "2026-10-13", "descripcion": "Python internship", "jornada": "20 hours", "modalidad": "hybrid"},
                {"portal": "greenhouse", "job_id": "gh-5", "empresa": "Acme", "titulo": "IT Intern", "ubicacion": "CABA", "url": "https://jobs.example/5", "fecha": "2026-10-12", "descripcion": "Python internship", "jornada": "20 hours", "modalidad": "hybrid"},
            ]
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, delimiter="|")
                writer.writeheader()
                writer.writerows(rows)
            result, state = build_pipeline([path], today=date(2026, 10, 17), ledger_path=Path(tmp) / "ledger.json")
            freshness = {item["job_id"]: item["freshness_window"] for item in result}
            self.assertEqual(freshness, {"gh-4": "primary", "gh-5": "secondary"})
            self.assertEqual(state["metrics"]["within_4_days_verified"], 1)

    def test_original_sources_beat_republication_date_and_keep_provenance(self):
        evidence = [
            {"source": "linkedin", "publication_date": "2026-10-14", "url": "https://linkedin.example/1"},
            {"source": "greenhouse", "publication_date": "2026-09-29", "url": "https://jobs.example/1"},
        ]
        posted, source, conflict = verified_publication_evidence(evidence, today=date(2026, 10, 14))
        self.assertEqual(posted, date(2026, 9, 29))
        self.assertEqual(source["source"], "greenhouse")
        self.assertFalse(conflict)

    def test_different_verified_dates_are_flagged_as_conflict(self):
        posted, _, conflict = verified_publication_evidence([
            {"source": "greenhouse", "publication_date": "2026-10-10"},
            {"source": "lever", "publication_date": "2026-10-12"},
        ], today=date(2026, 10, 14))
        self.assertEqual(posted, date(2026, 10, 10))
        self.assertTrue(conflict)

    def test_pipeline_uses_source_of_date_not_first_seen_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.tsv"
            fields = ["portal", "job_id", "empresa", "titulo", "ubicacion", "url", "fecha", "descripcion", "jornada", "modalidad"]
            rows = [
                {"portal": "linkedin", "job_id": "li-1", "empresa": "Acme", "titulo": "IT Intern", "ubicacion": "CABA", "url": "https://jobs.example/role", "fecha": "2026-10-14", "descripcion": "Python internship", "jornada": "20 hours", "modalidad": "hybrid"},
                {"portal": "greenhouse", "job_id": "gh-1", "empresa": "Acme", "titulo": "IT Intern", "ubicacion": "CABA", "url": "https://jobs.example/role", "fecha": "2026-09-29", "descripcion": "Python internship", "jornada": "20 hours", "modalidad": "hybrid"},
            ]
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, delimiter="|")
                writer.writeheader()
                writer.writerows(rows)
            result, _ = build_pipeline([path], today=date(2026, 10, 14), ledger_path=Path(tmp) / "ledger.json")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["published_date"], "2026-09-29")
            self.assertEqual(result[0]["publication_date_evidence"]["source"], "greenhouse")
            self.assertEqual(result[0]["freshness_window"], "expired_window")

    def test_pipeline_merges_exact_cross_source_url_but_keeps_richest_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "jobs.tsv"
            fields = ["portal", "job_id", "empresa", "titulo", "ubicacion", "url", "fecha", "descripcion", "jornada", "modalidad"]
            rows = [
                {"portal": "uade", "job_id": "123", "empresa": "Acme", "titulo": "IT Intern", "ubicacion": "CABA", "url": "https://jobs.example/role", "fecha": "2026-10-14", "descripcion": "IT support.", "jornada": "20 hours", "modalidad": "onsite"},
                {"portal": "company", "job_id": "123", "empresa": "Acme", "titulo": "IT Intern", "ubicacion": "CABA", "url": "https://jobs.example/role?utm_source=x", "fecha": "2026-10-14", "descripcion": "IT support, Windows, Microsoft 365, account management and tickets.", "jornada": "20 hours", "modalidad": "onsite"},
            ]
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, delimiter="|")
                writer.writeheader()
                writer.writerows(rows)
            result, _ = build_pipeline([path], today=date(2026, 10, 14), ledger_path=root / "ledger.json")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["descripcion"], rows[1]["descripcion"])
            self.assertEqual(len(result[0]["source_records"]), 2)

    def test_pipeline_carries_old_manual_state_to_new_key_without_dropping_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, ledger_path = root / "jobs.tsv", root / "ledger.json"
            path.write_text(
                "portal|job_id|empresa|titulo|ubicacion|url|fecha|descripcion|jornada|modalidad\n"
                "uade|2249|Acme|IT Intern|CABA|https://empleos.uade.edu.ar/Postulaciones|2026-10-14|Python internship|20 horas|presencial\n",
                encoding="utf-8",
            )
            ledger_path.write_text(
                '{"uade:2249":{"state":"Applied","review_notes":"manual note","first_seen":"2026-10-01"}}',
                encoding="utf-8",
            )
            result, state = build_pipeline([path], today=date(2026, 10, 14), ledger_path=ledger_path)
            self.assertEqual(result[0]["state"], "Applied")
            self.assertEqual(result[0]["review_notes"], "manual note")
            old = state["ledger"]["uade:2249"]
            self.assertTrue(old["migrated_to"].startswith("source-id:uade:2249"))


if __name__ == "__main__":
    unittest.main()
