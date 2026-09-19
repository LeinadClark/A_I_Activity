"""
Database Manager Module: SQLite Persistence, Structured JSON Ingestion, & CRUD Operations.
Enforces foreign key relationships and cascading deletes for multi-tiered syllabus entities.
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional, Union

from obe_schemas import CourseMetadataSchema, CourseOutcomeSchema


DEFAULT_DB_PATH = "obe_syllabus.db"
DEFAULT_SCHEMA_PATH = "schema.sql"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Creates and returns a SQLite connection with foreign keys enabled.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH, schema_path: str = DEFAULT_SCHEMA_PATH) -> None:
    """
    Initializes the normalized SQLite database using the DDL script.
    """
    if not os.path.exists(schema_path):
        # Check current directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        alt_path = os.path.join(base_dir, schema_path)
        if os.path.exists(alt_path):
            schema_path = alt_path
        else:
            raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        ddl_script = f.read()

    with get_connection(db_path) as conn:
        conn.executescript(ddl_script)
        conn.commit()
    print(f"[DB Manager] Initialized database at '{db_path}' using '{schema_path}'.")


def ingest_syllabus(
    syllabus: Union[CourseMetadataSchema, Dict[str, Any], str],
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """
    Ingests validated syllabus data into normalized relational tables inside an atomic transaction.
    """
    # 1. Validate data contract
    if isinstance(syllabus, str):
        validated = CourseMetadataSchema.model_validate_json(syllabus)
    elif isinstance(syllabus, dict):
        validated = CourseMetadataSchema.model_validate(syllabus)
    elif isinstance(syllabus, CourseMetadataSchema):
        validated = syllabus
    else:
        raise ValueError("Invalid syllabus format. Expected CourseMetadataSchema, dict, or JSON string.")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Delete existing course if it exists (triggers cascading delete on children)
        cursor.execute("DELETE FROM courses WHERE course_code = ?", (validated.course_code,))

        # 2. Insert Root Course
        cursor.execute("""
            INSERT INTO courses (course_code, course_title, course_description, credit_units, prerequisites)
            VALUES (?, ?, ?, ?, ?)
        """, (
            validated.course_code,
            validated.course_title,
            validated.course_description,
            validated.credit_units,
            validated.prerequisites
        ))
        course_id = cursor.lastrowid

        # 3. Insert Course Outcomes (CLOs)
        for co in validated.course_outcomes:
            cursor.execute("""
                INSERT INTO course_outcomes (course_id, co_number, bloom_level, co_description, mapped_po)
                VALUES (?, ?, ?, ?, ?)
            """, (
                course_id,
                co.co_number,
                co.bloom_level,
                co.co_description,
                json.dumps(co.mapped_po)
            ))

        # 4. Insert Weekly Schedules & Child Lesson Outcomes (LLOs)
        for week in validated.weekly_schedule:
            cursor.execute("""
                INSERT INTO weekly_schedules (
                    course_id, week_number, period, topic,
                    teaching_learning_activity, assessment_task, result_evidence, aligned_co
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                course_id,
                week.week_number,
                week.period,
                week.topic,
                week.teaching_learning_activity,
                week.assessment_task,
                week.result_evidence,
                json.dumps(week.aligned_co)
            ))
            schedule_week_id = cursor.lastrowid

            # Insert LLOs categorized into K, S, A
            for llo in week.lesson_outcomes:
                cursor.execute("""
                    INSERT INTO lesson_outcomes (schedule_week_id, category, description)
                    VALUES (?, ?, ?)
                """, (
                    schedule_week_id,
                    llo.category,
                    llo.description
                ))

        # 5. Insert Grading Components
        for comp in validated.grading_breakdown:
            cursor.execute("""
                INSERT INTO grading_components (course_id, assessment_task, percentage_weight)
                VALUES (?, ?, ?)
            """, (
                course_id,
                comp.assessment_task,
                comp.percentage_weight
            ))

        conn.commit()
    print(f"[DB Manager] Ingested course '{validated.course_code}' (ID: {course_id}) with all relational children.")
    return course_id


def ingest_json_file(file_path: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Reads a syllabus JSON file from disk, validates with Pydantic, and injects into SQLite.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = f.read()
    return ingest_syllabus(data, db_path=db_path)


def batch_ingest_directory(dir_path: str = "syllabi_library", db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Scans a directory of JSON syllabus files and injects each into SQLite database.
    """
    if not os.path.exists(dir_path):
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    results = []
    for fname in sorted(os.listdir(dir_path)):
        if fname.endswith(".json"):
            fpath = os.path.join(dir_path, fname)
            try:
                cid = ingest_json_file(fpath, db_path=db_path)
                with open(fpath, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                results.append({
                    "file": fname,
                    "course_code": cdata.get("course_code"),
                    "course_title": cdata.get("course_title"),
                    "status": "SUCCESS",
                    "course_id": cid
                })
            except Exception as e:
                results.append({
                    "file": fname,
                    "status": f"FAILED: {e}"
                })
    return results


def get_course_by_code(course_code: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """
    Retrieves full relational data for a course by course_code and reconstructs a structured dict.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Fetch course
        cursor.execute("SELECT * FROM courses WHERE course_code = ?", (course_code,))
        course_row = cursor.fetchone()
        if not course_row:
            return None

        course_id = course_row["id"]
        course_dict = dict(course_row)

        # Fetch Course Outcomes
        cursor.execute("""
            SELECT co_number, bloom_level, co_description, mapped_po
            FROM course_outcomes
            WHERE course_id = ?
            ORDER BY co_number ASC
        """, (course_id,))
        cos = []
        for r in cursor.fetchall():
            cos.append({
                "co_number": r["co_number"],
                "bloom_level": r["bloom_level"],
                "co_description": r["co_description"],
                "mapped_po": json.loads(r["mapped_po"])
            })
        course_dict["course_outcomes"] = cos

        # Fetch Weekly Schedules & LLOs
        cursor.execute("""
            SELECT id, week_number, period, topic, teaching_learning_activity,
                   assessment_task, result_evidence, aligned_co
            FROM weekly_schedules
            WHERE course_id = ?
            ORDER BY week_number ASC
        """, (course_id,))
        weeks = []
        for w_row in cursor.fetchall():
            w_id = w_row["id"]
            cursor.execute("""
                SELECT category, description
                FROM lesson_outcomes
                WHERE schedule_week_id = ?
                ORDER BY id ASC
            """, (w_id,))
            llos = [{"category": l["category"], "description": l["description"]} for l in cursor.fetchall()]

            weeks.append({
                "week_number": w_row["week_number"],
                "period": w_row["period"],
                "topic": w_row["topic"],
                "teaching_learning_activity": w_row["teaching_learning_activity"],
                "assessment_task": w_row["assessment_task"],
                "result_evidence": w_row["result_evidence"],
                "aligned_co": json.loads(w_row["aligned_co"]),
                "lesson_outcomes": llos
            })
        course_dict["weekly_schedule"] = weeks

        # Fetch Grading Components
        cursor.execute("""
            SELECT assessment_task, percentage_weight
            FROM grading_components
            WHERE course_id = ?
            ORDER BY id ASC
        """, (course_id,))
        course_dict["grading_breakdown"] = [
            {"assessment_task": g["assessment_task"], "percentage_weight": g["percentage_weight"]}
            for g in cursor.fetchall()
        ]

        return course_dict


def list_courses(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Returns a summary list of all stored courses.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.course_code, c.course_title, c.credit_units, c.created_at,
                   COUNT(DISTINCT co.id) AS outcome_count,
                   COUNT(DISTINCT ws.id) AS week_count
            FROM courses c
            LEFT JOIN course_outcomes co ON c.id = co.course_id
            LEFT JOIN weekly_schedules ws ON c.id = ws.course_id
            GROUP BY c.id
            ORDER BY c.course_code ASC
        """)
        return [dict(r) for r in cursor.fetchall()]


def update_course_outcome(
    course_code: str,
    co_number: int,
    new_description: Optional[str] = None,
    new_bloom_level: Optional[str] = None,
    new_mapped_po: Optional[List[int]] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """
    Human-in-the-Loop Faculty Edit: Modifies a generated Course Learning Outcome.
    Validates with CourseOutcomeSchema before writing to database.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM courses WHERE course_code = ?", (course_code,))
        c_row = cursor.fetchone()
        if not c_row:
            print(f"[DB Manager] Course '{course_code}' not found.")
            return False
        course_id = c_row["id"]

        cursor.execute("""
            SELECT bloom_level, co_description, mapped_po
            FROM course_outcomes
            WHERE course_id = ? AND co_number = ?
        """, (course_id, co_number))
        co_row = cursor.fetchone()
        if not co_row:
            print(f"[DB Manager] CO {co_number} not found for course '{course_code}'.")
            return False

        updated_bloom = new_bloom_level or co_row["bloom_level"]
        updated_desc = new_description or co_row["co_description"]
        updated_pos = new_mapped_po if new_mapped_po is not None else json.loads(co_row["mapped_po"])

        # Pydantic validation before persisting edit
        validated_co = CourseOutcomeSchema(
            co_number=co_number,
            bloom_level=updated_bloom,
            co_description=updated_desc,
            mapped_po=updated_pos
        )

        cursor.execute("""
            UPDATE course_outcomes
            SET bloom_level = ?, co_description = ?, mapped_po = ?
            WHERE course_id = ? AND co_number = ?
        """, (
            validated_co.bloom_level,
            validated_co.co_description,
            json.dumps(validated_co.mapped_po),
            course_id,
            co_number
        ))
        conn.commit()

    print(f"[DB Manager] Successfully updated CLO {co_number} for course '{course_code}'.")
    return True


def delete_course(course_code: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Deletes course by code. Verifies cascading delete on all child tables.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM courses WHERE course_code = ?", (course_code,))
        row = cursor.fetchone()
        if not row:
            return False
        course_id = row["id"]

        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()

        # Verify cascading deletes
        cursor.execute("SELECT COUNT(*) FROM course_outcomes WHERE course_id = ?", (course_id,))
        co_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM weekly_schedules WHERE course_id = ?", (course_id,))
        ws_count = cursor.fetchone()[0]

        if co_count == 0 and ws_count == 0:
            print(f"[DB Manager] [OK] Cascading delete verified: Course '{course_code}' and all related records deleted.")
            return True
        else:
            print(f"[DB Manager] [WARN] Cascading delete left {co_count} COs and {ws_count} schedules.")
            return False


if __name__ == "__main__":
    init_db()
    if os.path.exists("sample_validated_output.json"):
        with open("sample_validated_output.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        cid = ingest_syllabus(data)
        courses = list_courses()
        print("Stored Courses:", courses)
        # Test human-in-the-loop update
        update_course_outcome(
            course_code="CS 211",
            co_number=2,
            new_description="Critically evaluate algorithm asymptotic complexities and optimize runtime structures."
        )
        fetched = get_course_by_code("CS 211")
        print(f"Retrieved {fetched['course_title']} with {len(fetched['weekly_schedule'])} weeks.")
