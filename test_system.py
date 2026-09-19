"""
Automated Verification & Test Suite for OBE Syllabus Generator.
Tests:
1. Pydantic Schema Contracts & Taboo Verb Rejection
2. K/S/A Categorization & 18-Week Schedule Constraints
3. SQLite Normalization & Cascading Deletes (ON DELETE CASCADE)
4. Human-in-the-Loop Faculty Edit (CRUD)
5. Jinja2 Institutional Template Compilation
"""

import os
import json
import sqlite3
from pydantic import ValidationError

import obe_schemas
import db_manager
import export_engine


def test_schema_valid_payload():
    """Test that a well-formed 18-week syllabus passes Pydantic validation."""
    with open("sample_validated_output.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    syllabus = obe_schemas.CourseMetadataSchema.model_validate(data)
    assert syllabus.course_code == data["course_code"]
    assert len(syllabus.weekly_schedule) == 18
    assert len(syllabus.course_outcomes) >= 3
    print("[TEST 1 PASSED] Valid payload strictly validated.")


def test_banned_verbs_rejection():
    """Test that non-measurable verbs like 'understand' are strictly rejected."""
    try:
        obe_schemas.CourseOutcomeSchema(
            co_number=1,
            bloom_level="Applying",
            co_description="Understand basic computer programming concepts.",
            mapped_po=[1]
        )
        assert False, "Should have raised ValidationError for non-measurable verb 'understand'."
    except ValidationError as e:
        assert "Vague verb 'understand' detected" in str(e)
        print("[TEST 2 PASSED] Taboo verb 'understand' successfully intercepted and rejected.")


def test_missing_ksa_rejection():
    """Test that regular instructional weeks missing K, S, or A are rejected."""
    try:
        obe_schemas.WeeklyScheduleSchema(
            week_number=1,
            period="Prelim",
            topic="Introduction to Computing",
            teaching_learning_activity="Lecture",
            assessment_task="Quiz",
            result_evidence="Quiz Sheet",
            aligned_co=[1],
            lesson_outcomes=[
                obe_schemas.LessonOutcomeSchema(category="K", description="Define core computer concepts.")
                # Missing 'S' and 'A'
            ]
        )
        assert False, "Should have raised ValidationError for missing S and A categories."
    except ValidationError as e:
        assert "Missing categories" in str(e)
        print("[TEST 3 PASSED] Missing K/S/A categories in LLOs strictly intercepted.")


def test_exam_weeks_enforcement():
    """Test that weeks 6, 12, and 18 are strictly reserved for Major Examinations."""
    try:
        obe_schemas.WeeklyScheduleSchema(
            week_number=6,
            period="Prelim",
            topic="Regular Lecture on Arrays",  # Not Prelim Exam
            teaching_learning_activity="Lecture",
            assessment_task="Quiz",
            result_evidence="Quiz Sheet",
            aligned_co=[1]
        )
        assert False, "Should have raised ValidationError for non-exam Week 6."
    except ValidationError as e:
        assert "Week 6 must be designated for the Preliminary Examination" in str(e)
        print("[TEST 4 PASSED] Week 6 Preliminary Examination strictly enforced.")


def test_database_persistence_and_cascading_delete():
    """Test normalized database ingestion, foreign keys, and cascading delete."""
    test_db = "test_obe_temp.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    db_manager.init_db(db_path=test_db)

    with open("sample_validated_output.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    course_id = db_manager.ingest_syllabus(data, db_path=test_db)
    assert course_id > 0

    # Verify rows in child tables
    with db_manager.get_connection(test_db) as conn:
        co_count = conn.execute("SELECT COUNT(*) FROM course_outcomes WHERE course_id = ?", (course_id,)).fetchone()[0]
        ws_count = conn.execute("SELECT COUNT(*) FROM weekly_schedules WHERE course_id = ?", (course_id,)).fetchone()[0]
        lo_count = conn.execute("SELECT COUNT(*) FROM lesson_outcomes").fetchone()[0]
        assert co_count >= 3
        assert ws_count == 18
        assert lo_count > 0

    # Test faculty edit (CRUD)
    db_manager.update_course_outcome(
        course_code=data["course_code"],
        co_number=1,
        new_description="Apply advanced data structures to solve complex algorithmic problems.",
        db_path=test_db
    )
    fetched = db_manager.get_course_by_code(data["course_code"], db_path=test_db)
    assert fetched["course_outcomes"][0]["co_description"] == "Apply advanced data structures to solve complex algorithmic problems."

    # Test Cascading Delete
    success = db_manager.delete_course(data["course_code"], db_path=test_db)
    assert success is True

    # Verify zero child records remain
    conn = db_manager.get_connection(test_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM course_outcomes").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM weekly_schedules").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM lesson_outcomes").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM grading_components").fetchone()[0] == 0
    finally:
        conn.close()

    try:
        os.remove(test_db)
    except Exception:
        pass
    print("[TEST 5 PASSED] SQLite normalization, CRUD updates, and ON DELETE CASCADE verified.")


def test_jinja2_export_compilation():
    """Test Jinja2 compilation into browser-ready HTML matching institutional CCS layout."""
    with open("sample_validated_output.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    db_manager.init_db()
    db_manager.ingest_syllabus(data)

    out_file = export_engine.export_syllabus_html(data["course_code"], auto_open=False)
    assert os.path.exists(out_file)

    with open(out_file, "r", encoding="utf-8") as f:
        html = f.read()

    # Verify essential institutional components
    assert "University of Perpetual Help System DALTA" in html
    assert "College of Computer Studies" in html
    assert "Institutional Philosophy, Vision, and Mission" in html
    assert "Eight Perpetualite Core Values" in html
    assert "Course Learning Outcomes" in html
    assert "18-Week Detailed Learning Plan" in html
    assert "Course Evaluation & Grading System" in html
    assert "MS. JOY DEE BACSA" in html
    print("[TEST 6 PASSED] Jinja2 HTML export accurately contains all official CCS sections.")


if __name__ == "__main__":
    print("Running Automated Verification Suite...\n")
    test_schema_valid_payload()
    test_banned_verbs_rejection()
    test_missing_ksa_rejection()
    test_exam_weeks_enforcement()
    test_database_persistence_and_cascading_delete()
    test_jinja2_export_compilation()
    print("\nALL 6 VERIFICATION TESTS PASSED SUCCESSFULLY!")
