"""
OBE Data Schemas and Validation Contracts
Enforces Bloom's Taxonomy, K/S/A categorization, and 18-week schedule integrity.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Banned Non-Measurable Verbs in OBE / Bloom's Taxonomy
# ---------------------------------------------------------------------------
NON_MEASURABLE_VERBS = [
    "understand", "know", "learn", "study", "familiarize", "comprehend",
    "appreciate", "gain knowledge", "become aware", "grasp", "be exposed to"
]

BLOOM_LEVELS = Literal[
    "Remembering",
    "Understanding",
    "Applying",
    "Analyzing",
    "Evaluating",
    "Creating"
]

KSA_CATEGORIES = Literal["K", "S", "A", "Knowledge", "Skills", "Attitude"]


# ---------------------------------------------------------------------------
# 1. Lesson Learning Outcome (LLO) Schema
# ---------------------------------------------------------------------------
class LessonOutcomeSchema(BaseModel):
    """
    Represents a specific Lesson Learning Outcome categorized into K, S, or A.
    """
    category: KSA_CATEGORIES = Field(
        ...,
        description="OBE Domain Category: 'K' (Knowledge), 'S' (Skills), or 'A' (Attitude)"
    )
    description: str = Field(
        ...,
        description="Measurable outcome statement starting with an active verb"
    )

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        clean = str(v).strip().upper()
        if clean in ("K", "KNOWLEDGE"):
            return "K"
        elif clean in ("S", "SKILLS", "SKILL"):
            return "S"
        elif clean in ("A", "ATTITUDE", "ATTITUDES"):
            return "A"
        raise ValueError(f"Invalid LLO category '{v}'. Must be 'K' (Knowledge), 'S' (Skills), or 'A' (Attitude).")

    @field_validator("description")
    @classmethod
    def validate_action_description(cls, v: str) -> str:
        text = v.strip()
        if len(text) < 5:
            raise ValueError("Lesson outcome description must be at least 5 characters.")
        
        lower = text.lower()
        first_word = lower.split()[0].rstrip("s,.:;") if lower.split() else ""
        if first_word in ["understand", "know", "learn"]:
            raise ValueError(
                f"Non-measurable verb '{first_word}' used in LLO: '{text}'. "
                "Use measurable action verbs (e.g., Identify, Demonstrate, Value)."
            )
        return text


# ---------------------------------------------------------------------------
# 2. Course Learning Outcome (CLO) Schema
# ---------------------------------------------------------------------------
class CourseOutcomeSchema(BaseModel):
    """
    Represents a Course Learning Outcome (CLO / CO) aligned with Bloom's Taxonomy.
    """
    co_number: int = Field(..., ge=1, description="Course outcome identifier (1, 2, 3, ...)")
    bloom_level: BLOOM_LEVELS = Field(
        ...,
        description="Bloom's Revised Cognitive Domain Level"
    )
    co_description: str = Field(
        ...,
        description="Measurable outcome starting with an active Bloom's verb"
    )
    mapped_po: List[int] = Field(
        ...,
        min_length=1,
        description="Program Outcomes aligned with this Course Outcome, e.g. [1, 2, 5]"
    )

    @field_validator("co_description")
    @classmethod
    def validate_bloom_verb(cls, v: str) -> str:
        text = v.strip()
        if len(text) < 10:
            raise ValueError("Course outcome description must be at least 10 characters.")

        first_words = " ".join(text.lower().split()[:2])
        for banned in NON_MEASURABLE_VERBS:
            if text.lower().startswith(banned) or f" {banned} " in f" {first_words} ":
                raise ValueError(
                    f"OBE Violation: Vague verb '{banned}' detected in Course Outcome description: '{text}'. "
                    "Course Outcomes must use active, measurable verbs such as 'Apply', 'Design', 'Analyze', 'Evaluate'."
                )
        return text


# ---------------------------------------------------------------------------
# 3. Weekly Schedule Schema (18-Week Semester Term)
# ---------------------------------------------------------------------------
class WeeklyScheduleSchema(BaseModel):
    """
    Represents a single academic week in the 18-week semester.
    """
    week_number: int = Field(..., ge=1, le=18, description="Academic week index (1-18)")
    period: Literal["Prelim", "Midterm", "Final"] = Field(
        ...,
        description="Academic term period: Weeks 1-6 (Prelim), 7-12 (Midterm), 13-18 (Final)"
    )
    topic: str = Field(..., min_length=3, description="Subject matter / topic for the week")
    teaching_learning_activity: str = Field(
        ...,
        min_length=3,
        description="Teaching and learning activity or lab performance task"
    )
    assessment_task: str = Field(
        ...,
        min_length=3,
        description="Assessment strategy or evaluation tool (e.g., Hands-on Lab Exam, Quiz)"
    )
    result_evidence: str = Field(
        default="Lab Output / Portfolio",
        description="Evidence or artifact produced by students"
    )
    aligned_co: List[int] = Field(
        ...,
        min_length=1,
        description="List of Course Outcome numbers addressed this week, e.g. [1, 2]"
    )
    lesson_outcomes: List[LessonOutcomeSchema] = Field(
        default_factory=list,
        description="Weekly Lesson Learning Outcomes (LLOs) categorized into K, S, and A"
    )

    @field_validator("period", mode="before")
    @classmethod
    def auto_assign_period(cls, v: Optional[str], info) -> str:
        # Auto-compute or validate period based on week_number if provided
        week = info.data.get("week_number") if info.data else None
        if week:
            if 1 <= week <= 6:
                return "Prelim"
            elif 7 <= week <= 12:
                return "Midterm"
            elif 13 <= week <= 18:
                return "Final"
        return v or "Prelim"

    @model_validator(mode="after")
    def validate_exam_weeks_and_ksa(self) -> "WeeklyScheduleSchema":
        wn = self.week_number
        topic_lower = self.topic.lower()

        # Institutional Examination Weeks Check
        if wn == 6:
            if "prelim" not in topic_lower:
                raise ValueError("Week 6 must be designated for the Preliminary Examination.")
        elif wn == 12:
            if "midterm" not in topic_lower:
                raise ValueError("Week 12 must be designated for the Midterm Examination.")
        elif wn == 18:
            if "final" not in topic_lower:
                raise ValueError("Week 18 must be designated for the Final Examination.")
        else:
            # For regular instructional weeks, enforce K/S/A coverage if LLOs are provided
            if self.lesson_outcomes:
                categories = {llo.category for llo in self.lesson_outcomes}
                missing = {"K", "S", "A"} - categories
                if missing:
                    raise ValueError(
                        f"Week {wn} LLOs must cover Knowledge (K), Skills (S), and Attitude (A). "
                        f"Missing categories: {missing}"
                    )
        return self


# ---------------------------------------------------------------------------
# 4. Grading Breakdown Component Schema
# ---------------------------------------------------------------------------
class GradingComponentSchema(BaseModel):
    """
    Represents an assessment grading component with its percentage weight.
    """
    assessment_task: str = Field(..., description="Assessment task name (e.g., Quizzes, Lab Exercises)")
    percentage_weight: float = Field(..., ge=1.0, le=100.0, description="Percentage weight (e.g., 30.0)")


# ---------------------------------------------------------------------------
# 5. Full Course Metadata & Syllabus Schema (Root Contract)
# ---------------------------------------------------------------------------
class CourseMetadataSchema(BaseModel):
    """
    Root contract for the complete AI-generated OBE Syllabus.
    """
    course_code: str = Field(..., min_length=2, description="Institutional course code, e.g., 'BSIT 3112'")
    course_title: str = Field(..., min_length=3, description="Official course title")
    course_description: str = Field(..., min_length=20, description="Comprehensive catalog description")
    credit_units: str = Field(default="3 Units (2 Units Lecture, 1 Unit Laboratory)", description="Credit unit breakdown")
    prerequisites: str = Field(default="None", description="Prerequisite course code(s)")
    course_outcomes: List[CourseOutcomeSchema] = Field(
        ...,
        min_length=3,
        max_length=8,
        description="List of 3 to 8 Course Learning Outcomes"
    )
    weekly_schedule: List[WeeklyScheduleSchema] = Field(
        ...,
        min_length=18,
        max_length=18,
        description="Comprehensive 18-week instructional matrix"
    )
    grading_breakdown: List[GradingComponentSchema] = Field(
        default_factory=lambda: [
            GradingComponentSchema(assessment_task="Hands-on Laboratory Exercises & Projects", percentage_weight=40.0),
            GradingComponentSchema(assessment_task="Quizzes & Seatworks", percentage_weight=20.0),
            GradingComponentSchema(assessment_task="Preliminary Examination", percentage_weight=10.0),
            GradingComponentSchema(assessment_task="Midterm Examination", percentage_weight=15.0),
            GradingComponentSchema(assessment_task="Final Examination & Capstone Defense", percentage_weight=15.0),
        ],
        description="Assessment grading components summing to exactly 100%"
    )

    @model_validator(mode="after")
    def validate_full_syllabus(self) -> "CourseMetadataSchema":
        # 1. Enforce exactly 18 weeks numbered 1 through 18
        week_numbers = [w.week_number for w in self.weekly_schedule]
        if sorted(week_numbers) != list(range(1, 19)):
            raise ValueError(f"Weekly schedule must contain exactly weeks 1 through 18 in sequence. Got: {week_numbers}")

        # 2. Enforce all Course Outcomes are mapped in the schedule
        defined_co_numbers = {co.co_number for co in self.course_outcomes}
        mapped_co_numbers = set()
        for week in self.weekly_schedule:
            mapped_co_numbers.update(week.aligned_co)

        unmapped = defined_co_numbers - mapped_co_numbers
        if unmapped:
            raise ValueError(
                f"OBE Compliance Failure: Course Outcomes {unmapped} are never aligned in any week's schedule. "
                "Every Course Outcome must be addressed at least once across the 18-week term."
            )

        # 3. Enforce Grading Breakdown weights sum to 100%
        total_weight = sum(item.percentage_weight for item in self.grading_breakdown)
        if abs(total_weight - 100.0) > 0.5:
            raise ValueError(f"Grading breakdown weights must sum to 100%. Current total: {total_weight}%")

        return self
