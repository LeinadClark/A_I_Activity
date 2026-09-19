-- ============================================================================
-- Outcome-Based Education (OBE) Course Syllabus Relational Database Schema
-- Architecture: 3NF Normalized Relational Schema with Cascading Deletes
-- ============================================================================

PRAGMA foreign_keys = ON;

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS lesson_outcomes;
DROP TABLE IF EXISTS grading_components;
DROP TABLE IF EXISTS weekly_schedules;
DROP TABLE IF EXISTS course_outcomes;
DROP TABLE IF EXISTS courses;

-- ----------------------------------------------------------------------------
-- 1. Courses Table (Root Entity)
-- ----------------------------------------------------------------------------
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL,
    course_title TEXT NOT NULL,
    course_description TEXT NOT NULL,
    credit_units TEXT NOT NULL DEFAULT '3 Units (2 Units Lecture, 1 Unit Laboratory)',
    prerequisites TEXT NOT NULL DEFAULT 'None',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Course Outcomes Table (CLOs / COs)
-- ----------------------------------------------------------------------------
CREATE TABLE course_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    co_number INTEGER NOT NULL,
    bloom_level TEXT NOT NULL,
    co_description TEXT NOT NULL,
    mapped_po TEXT NOT NULL DEFAULT '[]', -- Stored as JSON string, e.g. '[1, 2]'
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE (course_id, co_number)
);

-- ----------------------------------------------------------------------------
-- 3. Weekly Schedules Table (18-Week Semester Term)
-- ----------------------------------------------------------------------------
CREATE TABLE weekly_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    week_number INTEGER NOT NULL CHECK(week_number BETWEEN 1 AND 18),
    period TEXT NOT NULL CHECK(period IN ('Prelim', 'Midterm', 'Final')),
    topic TEXT NOT NULL,
    teaching_learning_activity TEXT NOT NULL,
    assessment_task TEXT NOT NULL,
    result_evidence TEXT DEFAULT 'Lab Output / Portfolio',
    aligned_co TEXT NOT NULL DEFAULT '[]', -- Stored as JSON string, e.g. '[1, 2]'
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE (course_id, week_number)
);

-- ----------------------------------------------------------------------------
-- 4. Lesson Outcomes Table (Weekly LLOs: Knowledge, Skills, Attitude)
-- ----------------------------------------------------------------------------
CREATE TABLE lesson_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_week_id INTEGER NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('K', 'S', 'A', 'Knowledge', 'Skills', 'Attitude')),
    description TEXT NOT NULL,
    FOREIGN KEY (schedule_week_id) REFERENCES weekly_schedules(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 5. Grading Components Table (Assessment Matrix Summing to 100%)
-- ----------------------------------------------------------------------------
CREATE TABLE grading_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    assessment_task TEXT NOT NULL,
    percentage_weight REAL NOT NULL CHECK(percentage_weight > 0),
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- Performance Indexes for Relational Queries & Foreign Key Integrity
-- ----------------------------------------------------------------------------
CREATE INDEX idx_course_outcomes_course_id ON course_outcomes(course_id);
CREATE INDEX idx_weekly_schedules_course_id ON weekly_schedules(course_id);
CREATE INDEX idx_lesson_outcomes_schedule_week_id ON lesson_outcomes(schedule_week_id);
CREATE INDEX idx_grading_components_course_id ON grading_components(course_id);
