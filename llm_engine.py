"""
LLM Engine: Ollama / Qwen 2.5 API Wrapper with Automated Retry Loop & Pydantic Validation.
Automates generation of Bloom-aligned CLOs and an 18-week OBE syllabus matrix.
"""

import os
import sys
import json
import time
import subprocess
import requests
from typing import Dict, Any, Optional, List, Callable
from pydantic import ValidationError

from obe_schemas import (
    CourseMetadataSchema,
    CourseOutcomeSchema,
    WeeklyScheduleSchema,
    LessonOutcomeSchema,
    GradingComponentSchema
)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"
DEFAULT_MODEL = "qwen2.5:1.5b"


def is_ollama_running() -> bool:
    """Checks if local Ollama daemon is reachable on port 11434."""
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def ensure_ollama_running(timeout_seconds: int = 8) -> bool:
    """
    Verifies if Ollama is running; if not, automatically launches the local Ollama daemon.
    Returns True if service is alive.
    """
    if is_ollama_running():
        return True

    # Candidate paths for ollama executable on Windows
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
        r"C:\Users\Leinad\AppData\Local\Programs\Ollama\ollama.exe",
        "ollama.exe",
        "ollama"
    ]
    for exe in candidates:
        if os.path.exists(exe) or exe in ["ollama.exe", "ollama"]:
            try:
                # Launch detached background daemon
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                subprocess.Popen(
                    [exe, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                )
                break
            except Exception:
                continue

    # Poll until ready or timeout
    start_t = time.time()
    while time.time() - start_t < timeout_seconds:
        if is_ollama_running():
            return True
        time.sleep(0.5)

    return is_ollama_running()


def get_available_ollama_models() -> List[str]:
    """Retrieves list of installed Ollama models, starting daemon if needed."""
    if not is_ollama_running():
        ensure_ollama_running(timeout_seconds=4)
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=3)
        if r.status_code == 200:
            data = r.json()
            names = [m["name"] for m in data.get("models", [])]
            if names:
                return names
    except Exception:
        pass
    return ["qwen2.5:1.5b", "qwen2.5:7b", "qwen2.5:latest"]

OBE_SYSTEM_PROMPT = """You are an expert Outcome-Based Education (OBE) Curriculum Designer for the College of Computer Studies (CCS).
Your task is to generate a comprehensive, strictly validated 18-week course syllabus conforming to institutional CHED and CCS standards.

MANDATORY OBE BUSINESS RULES:
1. Bloom's Taxonomy: Every Course Outcome (CLO) description MUST begin with an active, measurable Bloom's taxonomy verb (e.g., Implement, Analyze, Design, Evaluate, Formulate).
   NEVER use non-measurable verbs such as "understand", "learn", "know", "study", or "appreciate".
2. 18-Week Academic Term: You must generate all 18 weeks sequentially (1 to 18):
   - Week 6 MUST be "Preliminary Examination" (Period: "Prelim").
   - Week 12 MUST be "Midterm Examination" (Period: "Midterm").
   - Week 18 MUST be "Final Examination & Capstone Defense" (Period: "Final").
3. K/S/A Categorization: For every regular instructional week, the `lesson_outcomes` array MUST contain outcomes covering:
   - "K" (Knowledge - cognitive concepts)
   - "S" (Skills - psychomotor/coding/practical execution)
   - "A" (Attitude - affective values, precision, ethics, teamwork)
4. Comprehensive Alignment: Every generated Course Outcome number (e.g. 1, 2, 3, 4, 5) MUST appear in the `aligned_co` field of at least one week in the 18-week schedule.
5. Grading Matrix: Assessment components must reflect CS/IT standard grading (Hands-on labs, quizzes, exams) and their percentage_weight values must sum to exactly 100.0.

You must respond ONLY with a single valid JSON object adhering to this exact schema structure:
{
  "course_code": "<Provided Course Code>",
  "course_title": "<Provided Course Title>",
  "course_description": "<Provided Course Catalog Description>",
  "credit_units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
  "prerequisites": "<Provided Prerequisites or None>",
  "course_outcomes": [
    {
      "co_number": 1,
      "bloom_level": "Applying",
      "co_description": "Apply fundamental theories and methodologies of the subject to practical scenarios.",
      "mapped_po": [1, 2]
    }
  ],
  "weekly_schedule": [
    {
      "week_number": 1,
      "period": "Prelim",
      "topic": "Course Orientation & Subject Domain Foundations",
      "teaching_learning_activity": "Interactive Lecture and Laboratory Toolchain Setup",
      "assessment_task": "Baseline Knowledge Assessment and Setup Verification",
      "result_evidence": "Configured Environment / Portfolio",
      "aligned_co": [1],
      "lesson_outcomes": [
        {"category": "K", "description": "Identify the foundational principles and scope of the subject."},
        {"category": "S", "description": "Configure domain software, toolchains, or clinical instruments."},
        {"category": "A", "description": "Value professional discipline and adherence to domain standards."}
      ]
    }
  ],
  "grading_breakdown": [
    {"assessment_task": "Hands-on Laboratory Exercises", "percentage_weight": 40.0},
    {"assessment_task": "Quizzes and Seatworks", "percentage_weight": 20.0},
    {"assessment_task": "Preliminary Examination", "percentage_weight": 10.0},
    {"assessment_task": "Midterm Examination", "percentage_weight": 15.0},
    {"assessment_task": "Final Examination / Capstone", "percentage_weight": 15.0}
  ]
}
"""


def _generate_deterministic_fallback(
    course_code: str,
    course_title: str,
    course_description: str,
    prerequisites: str = "None",
    credit_units: str = "3 Units (2 Units Lecture, 1 Unit Laboratory)"
) -> CourseMetadataSchema:
    """
    High-fidelity, domain-aware generator used when local Ollama daemon is offline or interrupted.
    Dynamically tailors outcomes and the 18-week schedule to Nursing, Computing, or General fields.
    """
    tl = course_title.lower()
    dl = course_description.lower()
    is_nursing = any(k in tl or k in dl for k in ["nurs", "medic", "health", "clinical", "hospital", "patient", "anatomy"])

    if is_nursing:
        cos = [
            CourseOutcomeSchema(
                co_number=1,
                bloom_level="Applying",
                co_description="Apply nursing process and aseptic clinical techniques in patient assessment and health promotion.",
                mapped_po=[1, 2]
            ),
            CourseOutcomeSchema(
                co_number=2,
                bloom_level="Analyzing",
                co_description="Analyze human vital signs, physiological data, and diagnostic lab values to formulate nursing care plans.",
                mapped_po=[2, 3]
            ),
            CourseOutcomeSchema(
                co_number=3,
                bloom_level="Applying",
                co_description="Administer pharmacological treatments and demonstrate safe medication dosages under hospital protocols.",
                mapped_po=[3, 4]
            ),
            CourseOutcomeSchema(
                co_number=4,
                bloom_level="Evaluating",
                co_description="Evaluate patient outcomes, ethical dilemmas, and infection control compliance in clinical ward settings.",
                mapped_po=[1, 4, 5]
            ),
            CourseOutcomeSchema(
                co_number=5,
                bloom_level="Creating",
                co_description="Formulate holistic, patient-centered nursing care plans integrating Perpetualite compassion and healthcare ethics.",
                mapped_po=[5, 6]
            )
        ]

        weekly_topics = [
            # Prelim Period (Weeks 1 - 6)
            (1, "Prelim", "Orientation to Professional Nursing, Bioethics, and Health Care Systems", "Clinical Orientation & Interactive Lecture", "Core Competencies Assessment", [1],
             "Explain the scope of professional nursing practice and bioethics", "Demonstrate clinical handwashing and basic aseptic technique", "Embody the Perpetualite core value of compassionate service"),
            (2, "Prelim", "Vital Signs Assessment: Body Temperature, Pulse, and Respiration", "Vital Signs Demonstration and Return Demonstration", "Vital Signs Clinical Rubric", [1, 2],
             "State normal physiological parameters across age cohorts", "Measure and record pulse rates and respiratory patterns accurately", "Value patient comfort and dignity during physical assessment"),
            (3, "Prelim", "Blood Pressure Measurement and Hemodynamic Monitoring", "Sphygmomanometer Practical Lab Session", "Blood Pressure Return Demo", [1, 2],
             "Explain Korotkoff sounds and factors influencing vascular pressure", "Execute accurate blood pressure measurement techniques", "Demonstrate meticulous accuracy in recording clinical data"),
            (4, "Prelim", "Health Assessment: Head-to-Toe Physical Examination Techniques", "Simulation Ward Inspection & Palpation Lab", "Physical Assessment Checklist", [1, 2],
             "Describe inspection, palpation, percussion, and auscultation procedures", "Perform systematic physical assessment across body systems", "Respect patient privacy and cultural sensitivities"),
            (5, "Prelim", "Infection Control, Universal Precautions, and PPE Protocols", "Sterile Field Setup & PPE Donning/Doffing Lab", "Infection Control Checklist", [1, 4],
             "Explain chains of infection transmission and sterile barrier principles", "Don and doff sterile gloves, masks, and protective gowns", "Display diligence in preventing nosocomial pathogen transmission"),
            (6, "Prelim", "Preliminary Examination: Fundamental Nursing Theories & Clinical Skills Return Demo", "Formal Examination & Clinical Simulation", "Prelim Written Exam & Clinical OSCE", [1, 2],
             "Recall anatomical landmarks and basic nursing intervention principles", "Execute timed basic clinical skill return demonstrations", "Exhibit professional composure and ethical demeanor under evaluation"),

            # Midterm Period (Weeks 7 - 12)
            (7, "Midterm", "Nursing Process: Assessment, Nursing Diagnosis, and Care Planning", "Case Study Analysis Workshop", "Care Plan Draft Evaluation", [2, 5],
             "Identify NANDA nursing diagnosis taxonomies and etiology statements", "Formulate measurable short-term and long-term patient goals", "Commit to individualized, compassionate patient care"),
            (8, "Midterm", "Medication Administration Foundations: The 10 Rights and Dosage Calculations", "Pharmacological Calculation Workshop", "Drug Calculation Problem Set", [3],
             "Explain pharmacokinetics, drug classifications, and safety checks", "Calculate metric dosages and intravenous drip rates without error", "Uphold zero-tolerance for pharmacological administration errors"),
            (9, "Midterm", "Enteral and Topical Medication Delivery: Oral, Sublingual, and Transdermal", "Skills Lab Medication Pass Simulation", "Medication Pass Performance Task", [3],
             "Describe administration routes and absorption barriers", "Administer oral medications following 10-rights safety protocols", "Demonstrate empathy when addressing patient medication anxieties"),
            (10, "Midterm", "Parenteral Medication Delivery: Intramuscular, Subcutaneous, and Intradermal", "Injection Simulation Lab", "Injection Technique Rubric", [3, 4],
             "Identify correct injection sites, needle gauges, and penetration angles", "Perform sterile intramuscular and subcutaneous injections", "Provide reassuring patient communication during needle procedures"),
            (11, "Midterm", "Wound Care, Surgical Asepsis, and Sterile Dressing Changes", "Wound Debridement & Dressing Change Lab", "Sterile Dressing Change Rubric", [1, 4],
             "Differentiate wound healing phases and exudate classifications", "Execute sterile dressing change and wound cleansing procedures", "Show meticulous patience in preserving sterile fields"),
            (12, "Midterm", "Midterm Examination: Clinical OSCE on Medication Administration and Wound Management", "Formal Clinical OSCE Exam Session", "Midterm Clinical OSCE Rubric", [2, 3, 4],
             "Synthesize pharmacological safety rules and wound healing dynamics", "Demonstrate flawless parenteral administration under inspection", "Display professional accountability and nurse-patient rapport"),

            # Final Period (Weeks 13 - 18)
            (13, "Final", "Intravenous (IV) Therapy: Cannulation, Fluid Maintenance, and Infiltration Monitoring", "IV Cannulation Simulation Workshop", "IV Insertion Skill Checklist", [3, 4],
             "Explain fluid and electrolyte balances and IV solution categories", "Insert and secure intravenous cannulas under sterile conditions", "Maintain constant vigilance for phlebitis and infiltration signs"),
            (14, "Final", "Oxygenation, Airway Management, and Tracheostomy Care", "Airway Suctioning and Nebulization Practical Lab", "Airway Management Assessment", [2, 4],
             "Describe pulse oximetry, respiratory mechanics, and hypoxia signs", "Perform tracheostomy care and sterile endotracheal suctioning", "Respond with calm urgency to acute respiratory distress indicators"),
            (15, "Final", "Pain Management, Patient Comfort Measures, and Palliative Nursing", "Pain Assessment Scale and Comfort Measure Workshop", "Pain Management Case Study", [1, 5],
             "Assess acute versus chronic pain using standardized clinical scales", "Implement non-pharmacological comfort and repositioning interventions", "Demonstrate deep empathy for patients enduring severe discomfort"),
            (16, "Final", "Perioperative Nursing: Pre-operative Preparation and Post-Anesthesia Recovery", "Operating Room Protocols & Recovery Room Lab", "Perioperative Checklist Task", [1, 4],
             "Outline surgical consent verification and recovery complications", "Monitor post-operative vital signs and surgical wound drains", "Prioritize patient safety during post-anesthetic transitions"),
            (17, "Final", "Comprehensive Clinical Nursing Integration and Interdisciplinary Ward Rounds", "Hospital Ward Simulation & Case Defense", "Integrative Nursing Portfolio", [1, 2, 3, 4, 5],
             "Synthesize multi-system health alterations into prioritized actions", "Collaborate with medical teams in simulated ward handovers (SBAR)", "Demonstrate leadership and collaborative teamwork in nursing care"),
            (18, "Final", "Final Examination & Capstone Clinical Defense: Comprehensive Patient Care Evaluation", "Formal Capstone Defense & Exit Clinical Exam", "Final Comprehensive Evaluation", [1, 2, 3, 4, 5],
             "Synthesize all theoretical nursing sciences and clinical proficiencies", "Defend comprehensive evidence-based nursing care management plan", "Exemplify Perpetualite 'Helpers of God' professional virtue")
        ]

        grading = [
            GradingComponentSchema(assessment_task="Clinical Skills Laboratory & Return Demonstrations", percentage_weight=40.0),
            GradingComponentSchema(assessment_task="Quizzes & Pharmacological Calculations", percentage_weight=20.0),
            GradingComponentSchema(assessment_task="Preliminary Examination (Theory & OSCE)", percentage_weight=10.0),
            GradingComponentSchema(assessment_task="Midterm Examination (Theory & OSCE)", percentage_weight=15.0),
            GradingComponentSchema(assessment_task="Final Examination & Clinical Capstone Defense", percentage_weight=15.0)
        ]

        return CourseMetadataSchema(
            course_code=course_code,
            course_title=course_title,
            course_description=course_description,
            credit_units=credit_units,
            prerequisites=prerequisites,
            course_outcomes=cos,
            weekly_schedule=[
                WeeklyScheduleSchema(
                    week_number=wn, period=per, topic=top, teaching_learning_activity=tla,
                    assessment_task=at, result_evidence="Clinical Portfolio / Return Demo Rubric",
                    aligned_co=ali,
                    lesson_outcomes=[
                        LessonOutcomeSchema(category="K", description=kd),
                        LessonOutcomeSchema(category="S", description=sd),
                        LessonOutcomeSchema(category="A", description=ad)
                    ]
                ) for (wn, per, top, tla, at, ali, kd, sd, ad) in weekly_topics
            ],
            grading_breakdown=grading
        )

    # Dynamic Course Topic Generator for ANY general academic subject (Computing, Engineering, Sciences, etc.)

    # 2. Dynamic Course Topic Generator for ANY general academic subject
    cos = [
        CourseOutcomeSchema(
            co_number=1,
            bloom_level="Applying",
            co_description=f"Apply fundamental theories, core concepts, and methodologies of {course_title} to solve real-world problems.",
            mapped_po=[1, 2]
        ),
        CourseOutcomeSchema(
            co_number=2,
            bloom_level="Analyzing",
            co_description=f"Analyze specialized data structures, system models, and workflows within {course_title}.",
            mapped_po=[2, 3]
        ),
        CourseOutcomeSchema(
            co_number=3,
            bloom_level="Applying",
            co_description=f"Execute modern domain-specific tools, practical frameworks, and standards relevant to {course_title}.",
            mapped_po=[3, 4]
        ),
        CourseOutcomeSchema(
            co_number=4,
            bloom_level="Evaluating",
            co_description=f"Evaluate competing techniques, architectural trade-offs, and quality standards in {course_title}.",
            mapped_po=[2, 4, 5]
        ),
        CourseOutcomeSchema(
            co_number=5,
            bloom_level="Creating",
            co_description=f"Synthesize comprehensive projects in {course_title} embodying professional ethics and industry best practices.",
            mapped_po=[4, 5, 6]
        )
    ]

    weekly_topics = [
        # Prelim Period (Weeks 1 - 6)
        (1, "Prelim", f"Course Orientation, Syllabus Review, and Scope of {course_title}", "Interactive Lecture & Environment Setup", "Toolchain Setup Verification", [1],
         f"Explain the primary learning objectives and career relevance of {course_title}", "Configure development environments, software tools, or clinical protocols", "Acknowledge academic integrity standards and software engineering rigor"),
        (2, "Prelim", f"Core Theoretical Principles and Historical Evolution of {course_title}", "Foundations Workshop & Case Study", "Conceptual Reflection Paper", [1],
         f"State foundational theorems and core terminologies of {course_title}", "Perform baseline domain analysis and functional problem decomposition", "Appreciate the evolution and societal impact of this discipline"),
        (3, "Prelim", f"Fundamental Problem Solving and Analytical Modeling in {course_title}", "Hands-on Analytical Modeling Lab", "Diagnostic Modeling Exercise", [1, 2],
         "Describe the key variables, constraints, and operational frameworks", "Construct initial problem-solving workflows using standard procedures", "Value methodical precision when structuring domain solutions"),
        (4, "Prelim", f"Standard Workflows, Syntax, and Implementation Practices in {course_title}", "Implementation Hands-on Lab Session", "Practical Exercise Submission", [1],
         "Formulate standard procedural steps and programmatic logic", "Execute core procedures and write verified algorithmic modules", "Demonstrate diligence in testing edge cases and boundary parameters"),
        (5, "Prelim", f"Intermediate Techniques, Debugging, and Validation in {course_title}", "Hands-on Debugging & Optimization Workshop", "Validated Pipeline Output", [1, 2],
         "Identify standard validation protocols and common structural bugs", "Apply diagnostic procedures to troubleshoot anomalies and defects", "Display perseverance when debugging complex multi-component issues"),
        (6, "Prelim", "Preliminary Examination: Theoretical and Hands-on Practical Examination", "Formal Examination Session", "Prelim Written & Practical Exam", [1, 2],
         "Recall fundamental definitions, principles, and analytical models", "Execute timed practical implementations under formal exam conditions", "Exhibit honesty, composure, and professionalism during assessment"),

        # Midterm Period (Weeks 7 - 12)
        (7, "Midterm", f"Intermediate Architecture and Component Design in {course_title}", "Architectural Design Workshop", "Structural Design Blueprint", [2],
         f"Explain intermediate system hierarchies and data flows in {course_title}", "Draft modular architectures adhering to separation-of-concerns principles", "Value modularity and reusability in system construction"),
        (8, "Midterm", f"Quantitative and Qualitative Performance Metrics in {course_title}", "Performance Profiling Lab Session", "Benchmarking Diagnostic Sheet", [2],
         "Formulate evaluation metrics, throughput measures, and benchmark standards", "Profile system performance and calculate empirical operational metrics", "Commit to quantitative rigor when comparing performance trade-offs"),
        (9, "Midterm", f"Advanced Algorithmic Methods and Applied Workflows in {course_title}", "Advanced Methods Workshop", "Algorithmic Implementation Task", [2, 3],
         "Analyze specialized algorithmic paradigms and high-level mechanisms", "Program advanced procedures utilizing domain libraries and APIs", "Strive for algorithmic efficiency and clean software structure"),
        (10, "Midterm", f"Integration of Industry Toolchains, Frameworks, and Libraries", "Industry Framework Lab Session", "Integrated Framework Module", [3],
         "Identify modern industry frameworks and ecosystem standard tooling", "Integrate third-party libraries and handle inter-module data exchanges", "Display curiosity in exploring cutting-edge developer tooling"),
        (11, "Midterm", f"Optimization, Resource Management, and Quality Auditing in {course_title}", "Code Tuning & Optimization Lab", "Optimization Report", [2, 3],
         "Explain bottleneck identification, caching, and resource minimization", "Refactor suboptimal modules to enhance execution speed and reliability", "Demonstrate prudence when balancing complexity against efficiency"),
        (12, "Midterm", "Midterm Examination: Practical Midterm Project Defense and Exam", "Formal Midterm Exam Session", "Midterm Project Submission & Rubric", [2, 3],
         "Synthesize intermediate theory and practical architectural frameworks", "Defend a working prototype under live inspection and questioning", "Demonstrate technical mastery under formal assessment"),

        # Final Period (Weeks 13 - 18)
        (13, "Final", f"Advanced Specialized Concepts and Modern Paradigms in {course_title}", "Specialized Topics Seminar & Lab", "Advanced Concept Assignment", [4],
         "Explain high-level advanced paradigms and contemporary research frontiers", "Implement experimental features utilizing modern design patterns", "Value innovation and forward-thinking problem solving"),
        (14, "Final", f"Security, Safety, Ethics, and Governance Considerations in {course_title}", "Ethical & Security Audit Workshop", "Risk Assessment Matrix", [4],
         "Outline ethical standards, legal responsibilities, and security threats", "Perform security audits and apply defensive hardening techniques", "Uphold professional ethics, user privacy, and data protection"),
        (15, "Final", f"Enterprise Systems Integration and Scalability for {course_title}", "Scalability Lab Workshop", "Distributed Module Deployment", [4, 5],
         "Describe enterprise scalability constraints, concurrency, and distribution", "Configure distributed components and handle concurrent data operations", "Foster holistic architectural thinking in enterprise design"),
        (16, "Final", f"Comprehensive Quality Assurance, Verification, and Stress Testing", "Automated QA and Stress Testing Lab", "Test Suite & Coverage Report", [2, 4],
         "Explain unit testing, integration testing, and regression verification", "Construct automated test suites achieving comprehensive branch coverage", "Maintain zero tolerance for unverified production code"),
        (17, "Final", f"Capstone Project Consolidation, Peer Review, and Pre-Defense in {course_title}", "Collaborative Integration Workshop", "Pre-Defense Functional Prototype", [1, 2, 3, 4, 5],
         "Consolidate all project submodules into a cohesive enterprise solution", "Execute peer code reviews and incorporate constructive feedback", "Practice collaborative teamwork and shared accountability"),
        (18, "Final", "Final Examination & Capstone Defense: Comprehensive Project Presentation", "Formal Capstone Project Defense", "Final Evaluation & Defense Rubric", [1, 2, 3, 4, 5],
         f"Synthesize all theoretical sciences and practical skills in {course_title}", "Present and defend an enterprise-grade solution before a faculty panel", "Exemplify Perpetualite leadership, virtue, and professional ethics")
    ]

    schedule = []
    for (w_num, period, topic, tla, at, aligned, k_desc, s_desc, a_desc) in weekly_topics:
        llos = [
            LessonOutcomeSchema(category="K", description=k_desc),
            LessonOutcomeSchema(category="S", description=s_desc),
            LessonOutcomeSchema(category="A", description=a_desc)
        ]
        schedule.append(WeeklyScheduleSchema(
            week_number=w_num,
            period=period,
            topic=topic,
            teaching_learning_activity=tla,
            assessment_task=at,
            result_evidence="Lab Portfolio / Project Output",
            aligned_co=aligned,
            lesson_outcomes=llos
        ))

    grading = [
        GradingComponentSchema(assessment_task="Hands-on Laboratory Exercises & Coding Tasks", percentage_weight=40.0),
        GradingComponentSchema(assessment_task="Quizzes & Technical Seatworks", percentage_weight=20.0),
        GradingComponentSchema(assessment_task="Preliminary Examination", percentage_weight=10.0),
        GradingComponentSchema(assessment_task="Midterm Examination", percentage_weight=15.0),
        GradingComponentSchema(assessment_task="Final Examination & Capstone Defense", percentage_weight=15.0)
    ]

    return CourseMetadataSchema(
        course_code=course_code,
        course_title=course_title,
        course_description=course_description,
        credit_units=credit_units,
        prerequisites=prerequisites,
        course_outcomes=cos,
        weekly_schedule=schedule,
        grading_breakdown=grading
    )


def _sanitize_llm_json_payload(
    data: Dict[str, Any],
    course_code: str,
    course_title: str,
    course_description: str,
    prerequisites: str,
    credit_units: str
) -> Dict[str, Any]:
    """
    Sanitizes and repairs LLM generated JSON data to guarantee Pydantic schema compliance
    while strictly preserving all domain-specific creative content produced by Ollama.
    """
    if not isinstance(data, dict):
        data = {}

    data["course_code"] = str(data.get("course_code") or course_code).strip()
    data["course_title"] = str(data.get("course_title") or course_title).strip()
    data["course_description"] = str(data.get("course_description") or course_description).strip()
    data["prerequisites"] = str(data.get("prerequisites") or prerequisites).strip()
    data["credit_units"] = str(data.get("credit_units") or credit_units).strip()

    valid_bloom = {"Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"}
    banned_replacements = {"understand": "Comprehend", "know": "Identify", "learn": "Acquire"}

    # 1. Course Outcomes
    raw_cos = data.get("course_outcomes")
    if not isinstance(raw_cos, list) or len(raw_cos) == 0:
        raw_cos = [
            {"co_number": 1, "bloom_level": "Applying", "co_description": f"Apply fundamental methodologies and core theories of {data['course_title']}.", "mapped_po": [1, 2]},
            {"co_number": 2, "bloom_level": "Analyzing", "co_description": f"Analyze specialized domain algorithms and architectures within {data['course_title']}.", "mapped_po": [2, 3]},
            {"co_number": 3, "bloom_level": "Evaluating", "co_description": f"Evaluate technical design choices and trade-offs in {data['course_title']}.", "mapped_po": [3, 4]},
            {"co_number": 4, "bloom_level": "Creating", "co_description": f"Formulate innovative software or system implementations in {data['course_title']}.", "mapped_po": [1, 5]}
        ]

    sanitized_cos = []
    for idx, co in enumerate(raw_cos, start=1):
        if not isinstance(co, dict):
            co = {}
        bl = str(co.get("bloom_level", "Applying")).capitalize()
        if bl not in valid_bloom:
            bl = "Applying"
        desc = str(co.get("co_description") or f"Implement core techniques relevant to {data['course_title']}.").strip()
        first_word = desc.split()[0].lower().rstrip("s,.:;") if desc.split() else ""
        if first_word in banned_replacements:
            desc = banned_replacements[first_word] + desc[len(first_word):]
        pos = co.get("mapped_po")
        if not isinstance(pos, list) or not pos:
            pos = [idx % 5 + 1]
        else:
            pos = [int(p) for p in pos if str(p).isdigit()]
            if not pos:
                pos = [1]
        sanitized_cos.append({
            "co_number": idx,
            "bloom_level": bl,
            "co_description": desc,
            "mapped_po": pos
        })

    # Enforce at least 3 Course Learning Outcomes
    while len(sanitized_cos) < 4:
        next_idx = len(sanitized_cos) + 1
        bloom_cycle = ["Applying", "Analyzing", "Evaluating", "Creating"]
        b_lvl = bloom_cycle[(next_idx - 1) % len(bloom_cycle)]
        sanitized_cos.append({
            "co_number": next_idx,
            "bloom_level": b_lvl,
            "co_description": f"{b_lvl} advanced paradigms, computational models, and design standards in {data['course_title']}.",
            "mapped_po": [next_idx % 5 + 1]
        })

    data["course_outcomes"] = sanitized_cos

    # 2. Weekly Schedule (Ensure all 18 weeks)
    raw_weeks = data.get("weekly_schedule")
    if not isinstance(raw_weeks, list):
        raw_weeks = []

    weeks_by_num = {}
    for w in raw_weeks:
        if isinstance(w, dict) and "week_number" in w:
            try:
                wn = int(w["week_number"])
                if 1 <= wn <= 18:
                    weeks_by_num[wn] = w
            except Exception:
                pass

    sanitized_weeks = []
    for wn in range(1, 19):
        w = weeks_by_num.get(wn, {})
        if wn <= 6:
            period = "Prelim"
        elif wn <= 12:
            period = "Midterm"
        else:
            period = "Final"

        # Major Examination Locks
        if wn == 6:
            topic = str(w.get("topic") or "Preliminary Examination: Theoretical & Practical Competencies")
            if "prelim" not in topic.lower():
                topic = "Preliminary Examination: " + topic
            tla = str(w.get("teaching_learning_activity") or "Formal Examination & Skill Return Demo")
            at = str(w.get("assessment_task") or "Preliminary Examination Paper & Evaluation")
        elif wn == 12:
            topic = str(w.get("topic") or "Midterm Examination: Comprehensive Assessment")
            if "midterm" not in topic.lower():
                topic = "Midterm Examination: " + topic
            tla = str(w.get("teaching_learning_activity") or "Formal Examination & Hands-on Practical Defense")
            at = str(w.get("assessment_task") or "Midterm Examination Paper & Evaluation")
        elif wn == 18:
            topic = str(w.get("topic") or "Final Examination & Capstone Defense")
            if "final" not in topic.lower():
                topic = "Final Examination: " + topic
            tla = str(w.get("teaching_learning_activity") or "Formal Capstone Defense & Project Presentation")
            at = str(w.get("assessment_task") or "Final Comprehensive Examination & Project Portfolio")
        else:
            topic = str(w.get("topic") or f"Module {wn}: Advanced Principles of {data['course_title']}")
            tla = str(w.get("teaching_learning_activity") or "Interactive Lecture and Hands-on Laboratory Workshop")
            at = str(w.get("assessment_task") or "Practical Seatwork / Formative Assessment")

        rev = str(w.get("result_evidence") or "Laboratory Exercise Output / Portfolio")

        # Aligned CO
        aligned = w.get("aligned_co")
        if not isinstance(aligned, list) or not aligned:
            aligned = [(wn % len(sanitized_cos)) + 1]
        else:
            aligned = [int(x) for x in aligned if str(x).isdigit()]
            if not aligned:
                aligned = [(wn % len(sanitized_cos)) + 1]

        # Lesson Outcomes (K, S, A)
        raw_los = w.get("lesson_outcomes", [])
        if not isinstance(raw_los, list):
            raw_los = []

        sanitized_los = []
        found_cats = set()
        for lo in raw_los:
            if isinstance(lo, dict):
                cat = str(lo.get("category", "")).strip().upper()
                if cat in ("K", "KNOWLEDGE"):
                    cat = "K"
                elif cat in ("S", "SKILLS", "SKILL"):
                    cat = "S"
                elif cat in ("A", "ATTITUDE", "ATTITUDES"):
                    cat = "A"
                else:
                    continue
                desc = str(lo.get("description", "")).strip()
                first_w = desc.split()[0].lower().rstrip("s,.:;") if desc.split() else ""
                if first_w in banned_replacements:
                    desc = banned_replacements[first_w] + desc[len(first_w):]
                if len(desc) < 5:
                    desc = f"Demonstrate mastery of {cat} domain competencies for Week {wn}."
                sanitized_los.append({"category": cat, "description": desc})
                found_cats.add(cat)

        if wn not in (6, 12, 18):
            if "K" not in found_cats:
                sanitized_los.append({"category": "K", "description": f"Explain theoretical foundations and core principles for Week {wn}."})
            if "S" not in found_cats:
                sanitized_los.append({"category": "S", "description": f"Apply practical domain tools, coding standards, and workflows for Week {wn}."})
            if "A" not in found_cats:
                sanitized_los.append({"category": "A", "description": f"Value professional accuracy, ethical discipline, and teamwork during Week {wn}."})

        sanitized_weeks.append({
            "week_number": wn,
            "period": period,
            "topic": topic,
            "teaching_learning_activity": tla,
            "assessment_task": at,
            "result_evidence": rev,
            "aligned_co": aligned,
            "lesson_outcomes": sanitized_los
        })

    # Ensure EVERY Course Outcome is aligned in at least one week across the 18 weeks
    all_cos = {c["co_number"] for c in sanitized_cos}
    aligned_cos = set()
    for w in sanitized_weeks:
        for a in w.get("aligned_co", []):
            aligned_cos.add(a)
    missing_cos = sorted(list(all_cos - aligned_cos))
    if missing_cos:
        # Distribute missing COs into instructional weeks
        for idx, m_co in enumerate(missing_cos):
            target_week_idx = (idx * 3 + 1) % len(sanitized_weeks)
            if m_co not in sanitized_weeks[target_week_idx]["aligned_co"]:
                sanitized_weeks[target_week_idx]["aligned_co"].append(m_co)

    data["weekly_schedule"] = sanitized_weeks

    # 3. Grading Breakdown (sum must equal 100.0)
    gb = data.get("grading_breakdown")
    if not isinstance(gb, list) or len(gb) < 3:
        data["grading_breakdown"] = [
            {"assessment_task": "Hands-on Laboratory Exercises", "percentage_weight": 40.0},
            {"assessment_task": "Quizzes and Seatworks", "percentage_weight": 20.0},
            {"assessment_task": "Preliminary Examination", "percentage_weight": 10.0},
            {"assessment_task": "Midterm Examination", "percentage_weight": 15.0},
            {"assessment_task": "Final Examination & Capstone Defense", "percentage_weight": 15.0}
        ]
    else:
        total_w = sum(float(g.get("percentage_weight", 0)) for g in gb)
        if abs(total_w - 100.0) > 0.01:
            data["grading_breakdown"] = [
                {"assessment_task": "Hands-on Laboratory Exercises", "percentage_weight": 40.0},
                {"assessment_task": "Quizzes and Seatworks", "percentage_weight": 20.0},
                {"assessment_task": "Preliminary Examination", "percentage_weight": 10.0},
                {"assessment_task": "Midterm Examination", "percentage_weight": 15.0},
                {"assessment_task": "Final Examination & Capstone Defense", "percentage_weight": 15.0}
            ]

    return data


def _try_parse_json(text: str) -> Dict[str, Any]:
    """
    Robust JSON parser with automatic bracket and delimiter repair for LLM token streams.
    """
    text = text.strip()
    # 1. Standard parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Try slicing from first '{' to last '}'
    first_b = text.find("{")
    last_b = text.rfind("}")
    if first_b != -1 and last_b != -1 and last_b > first_b:
        sub = text[first_b:last_b + 1]
        try:
            return json.loads(sub)
        except Exception:
            pass

    # 3. Auto-close truncated objects/arrays
    for suffix in ["}", "]}", "]}}", "\"\n}\n]}", "\"\n}\n]}}", "0.0}\n]\n}"]:
        try:
            return json.loads(text + suffix)
        except Exception:
            pass

    # 4. Final attempt standard loads to raise the descriptive JSONDecodeError
    return json.loads(text)


def generate_syllabus_data(
    course_title: str,
    course_description: str,
    course_code: str = "CS 311",
    target_pos: Optional[list] = None,
    prerequisites: str = "None",
    credit_units: str = "3 Units (2 Units Lecture, 1 Unit Laboratory)",
    max_retries: int = 3,
    model_name: str = DEFAULT_MODEL,
    allow_fallback: bool = True,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    stream: bool = False
) -> CourseMetadataSchema:
    """
    Queries local Ollama (Qwen 2.5) with strict JSON formatting and automated retry loop.
    Supports real-time token streaming and progress callbacks for CLI and GUI.
    """
    # Ensure Ollama daemon is active before querying
    if not is_ollama_running():
        print("[LLM Engine] Ollama daemon not running. Attempting auto-start on localhost:11434...")
        ensure_ollama_running(timeout_seconds=6)

    if target_pos is None:
        target_pos = [1, 2, 3, 4, 5, 6]

    user_prompt = (
        f"Generate a complete 18-week Outcome-Based Education (OBE) course syllabus for:\n"
        f"Course Code: {course_code}\n"
        f"Course Title: {course_title}\n"
        f"Description: {course_description}\n"
        f"Target Program Outcomes (POs): {target_pos}\n"
        f"Prerequisites: {prerequisites}\n"
        f"Credit Units: {credit_units}\n\n"
        f"Remember: Output strictly in JSON. Ensure 18 weeks, Week 6 is Prelim Exam, "
        f"Week 12 is Midterm Exam, Week 18 is Final Exam, every non-exam week has K, S, and A outcomes, "
        f"and all Course Outcomes are mapped."
    )

    current_prompt = f"{OBE_SYSTEM_PROMPT}\n\nUSER REQUEST:\n{user_prompt}"

    use_stream = stream or (progress_callback is not None)

    for attempt in range(1, max_retries + 1):
        print(f"\n[LLM Engine] Querying Ollama '{model_name}' (Attempt {attempt}/{max_retries})...")
        payload = {
            "model": model_name,
            "prompt": current_prompt,
            "format": "json",
            "stream": use_stream,
            "options": {
                "temperature": 0.2,
                "num_ctx": 4096,
                "num_predict": 4096
            }
        }

        try:
            start_t = time.time()
            if use_stream:
                response = requests.post(OLLAMA_GENERATE_URL, json=payload, stream=True, timeout=300)
                response.raise_for_status()
                chunks = []
                token_count = 0
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line.decode("utf-8"))
                            token = chunk_data.get("response", "")
                            chunks.append(token)
                            token_count += 1
                            if progress_callback and token_count % 15 == 0:
                                progress_callback(token_count, token)
                        except Exception:
                            pass
                raw_text = "".join(chunks).strip()
                if progress_callback:
                    progress_callback(token_count, "")
            else:
                response = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=240)
                response.raise_for_status()
                res_json = response.json()
                raw_text = res_json.get("response", "").strip()

            elapsed = time.time() - start_t
            print(f"[LLM Engine] Live generation complete ({elapsed:.2f}s). Validating against Pydantic schema...")

            # 1. Parse JSON syntax with auto-repair
            raw_data = _try_parse_json(raw_text)

            # 2. Sanitize and repair minor syntax omissions while preserving LLM generated content
            data = _sanitize_llm_json_payload(
                data=raw_data,
                course_code=course_code,
                course_title=course_title,
                course_description=course_description,
                prerequisites=prerequisites,
                credit_units=credit_units
            )

            # 3. Strict Pydantic Data Contract Validation
            validated_syllabus = CourseMetadataSchema.model_validate(data)
            print("[LLM Engine] [OK] Pydantic Validation Successful! All OBE constraints satisfied.")
            return validated_syllabus

        except requests.exceptions.RequestException as req_err:
            print(f"[LLM Engine] Connection to Ollama failed at {OLLAMA_GENERATE_URL}: {req_err}")
            if allow_fallback:
                print("[LLM Engine] Activating domain-aware dynamic fallback generator...")
                return _generate_deterministic_fallback(
                    course_code=course_code,
                    course_title=course_title,
                    course_description=course_description,
                    prerequisites=prerequisites,
                    credit_units=credit_units
                )
            raise RuntimeError(
                f"Ollama connection error ({req_err}). Please verify Ollama is running at http://localhost:11434."
            ) from req_err

        except (json.JSONDecodeError, ValidationError, ValueError) as val_err:
            print(f"[LLM Engine] [FAIL] Validation error on attempt {attempt}: {val_err}")
            if attempt == max_retries:
                if allow_fallback:
                    print("[LLM Engine] Maximum LLM retries exceeded. Falling back to calibrated reference schema.")
                    return _generate_deterministic_fallback(
                        course_code=course_code,
                        course_title=course_title,
                        course_description=course_description,
                        prerequisites=prerequisites,
                        credit_units=credit_units
                    )
                raise RuntimeError(
                    f"Failed to generate valid OBE syllabus with Ollama after {max_retries} attempts: {val_err}"
                ) from val_err

            # Self-correcting feedback loop: re-prompt model with bounded error message
            short_err = str(val_err)[:350]
            current_prompt = (
                f"{OBE_SYSTEM_PROMPT}\n\nUSER REQUEST:\n{user_prompt}\n\n"
                f"CORRECTION DIRECTIVE FOR ATTEMPT {attempt + 1}:\n"
                f"Previous output had error: {short_err}\n"
                f"Re-generate the full valid JSON resolving this error strictly. Ensure 18 weeks and K/S/A outcomes."
            )
            time.sleep(1)


if __name__ == "__main__":
    print("Testing LLM Engine...")
    syllabus = generate_syllabus_data(
        course_title="Computer Graphics and Programming",
        course_description="Introduction to 3D computer graphics, matrix mathematics, rendering pipelines, shaders, and OpenGL.",
        course_code="BSIT 3112"
    )
    print(f"Generated Syllabus for: {syllabus.course_title} ({syllabus.course_code})")
    print(f"Total Outcomes: {len(syllabus.course_outcomes)}")
    print(f"Total Weeks: {len(syllabus.weekly_schedule)}")
