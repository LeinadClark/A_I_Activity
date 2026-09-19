"""
Generates the official Word Document (.docx) for Onsite Presentation Script
and Video Demonstration Guide for:
Leinad Clark M. Dela Cruz & Nicole Anne G. Liwag
Instructor: Prof. Rob Malitao
UPHSD College of Computer Studies (CCS)
"""

import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_document():
    doc = Document()

    # Page Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Styles
    COLOR_MAROON = RGBColor(128, 0, 0)
    COLOR_GOLD = RGBColor(180, 130, 0)
    COLOR_DARK = RGBColor(30, 41, 59)
    COLOR_MUTED = RGBColor(100, 116, 139)

    # -------------------------------------------------------------------------
    # COVER / HEADER
    # -------------------------------------------------------------------------
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_uphsd = p_inst.add_run("UNIVERSITY OF PERPETUAL HELP SYSTEM DALTA – MOLINO CAMPUS\n")
    r_uphsd.bold = True
    r_uphsd.font.size = Pt(13)
    r_uphsd.font.color.rgb = COLOR_MAROON

    r_ccs = p_inst.add_run("COLLEGE OF COMPUTER STUDIES\n")
    r_ccs.bold = True
    r_ccs.font.size = Pt(11)
    r_ccs.font.color.rgb = COLOR_GOLD

    r_course = p_inst.add_run("Salawag-Zapote Road, Molino 3, City of Bacoor, 4102 Philippines\nBSCS 3112 - Artificial Intelligence (Lab) • Midterm Mini-Project\n")
    r_course.font.size = Pt(10)
    r_course.font.italic = True
    r_course.font.color.rgb = COLOR_MUTED

    # Document Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_title.add_run("AI-POWERED OBE SYLLABUS GENERATOR MICROSERVICE\n")
    r_t.bold = True
    r_t.font.size = Pt(18)
    r_t.font.color.rgb = COLOR_MAROON

    r_sub = p_title.add_run("Official Onsite Presentation Script & Video Demonstration Guide")
    r_sub.font.size = Pt(12)
    r_sub.bold = True
    r_sub.font.color.rgb = COLOR_DARK

    doc.add_paragraph() # Spacer

    # Metadata Box (Table)
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False

    meta_data = [
        ("Lead Presenters / Researchers:", "Leinad Clark M. Dela Cruz & Nicole Anne G. Liwag"),
        ("Campus & Location:", "Molino Campus (Salawag-Zapote Road, Molino 3, City of Bacoor, Cavite)"),
        ("Course & Section:", "BSCS 3112 - Artificial Intelligence (Lab) • Midterm Mini-Project"),
        ("Course Instructor & Evaluator:", "Prof. Rob Malitao"),
        ("Core Technology Stack:", "Python 3.10+, Local Ollama (Qwen 2.5 on RTX GPU), Pydantic v2, SQLite3 (3NF), Jinja2, Tkinter GUI")
    ]

    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        cell_lbl.width = Inches(2.4)
        cell_val.width = Inches(4.1)

        set_cell_background(cell_lbl, "F8FAFC")
        set_cell_background(cell_val, "FFFFFF")
        set_cell_margins(cell_lbl, top=80, bottom=80, left=120, right=120)
        set_cell_margins(cell_val, top=80, bottom=80, left=120, right=120)

        p1 = cell_lbl.paragraphs[0]
        r1 = p1.add_run(label)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_MAROON

        p2 = cell_val.paragraphs[0]
        r2 = p2.add_run(val)
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_DARK

    doc.add_paragraph() # Spacer
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # PART 1: EXECUTIVE BRIEFING & ARCHITECTURAL SUMMARY
    # -------------------------------------------------------------------------
    h1 = doc.add_heading("Part 1: Executive Summary & Project Architecture", level=1)
    h1.runs[0].font.color.rgb = COLOR_MAROON

    p_exec = doc.add_paragraph()
    p_exec.add_run(
        "The AI-Powered Outcome-Based Education (OBE) Syllabus Generator Microservice was conceptualized and developed "
        "for the College of Computer Studies (CCS) Curriculum and Quality Assurance Committee at the University of Perpetual Help System DALTA – Molino Campus. "
        "In traditional academic workflows, manual syllabus drafting is notoriously prone to non-measurable cognitive verbs (such as 'understand', 'know', or 'learn'), "
        "misaligned teaching-learning activities, missing Knowledge-Skills-Attitude (K-S-A) lesson outcomes, and formatting discrepancies that violate "
        "CHED Memorandum Order (CMO) No. 25 series of 2015 and institutional standards."
    )

    p_pipe = doc.add_paragraph()
    p_pipe.add_run(
        "Our system resolves these challenges through a deterministic 5-stage automated engineering pipeline:\n"
    )
    stages = [
        ("1. Dynamic Context & System Prompting:", " Ingests course metadata (Course Code, Title, Units, Prerequisites, Description) and queries a locally hosted Qwen 2.5 model via Ollama with strict JSON mode constraints."),
        ("2. Deterministic Pydantic Guardrails:", " Intercepts LLM outputs through runtime schemas. Non-measurable verbs are strictly rejected, 18-week term schedules (with Week 6 Prelim, Week 12 Midterm, and Week 18 Final) are enforced, and weekly K-S-A tripartite outcomes are guaranteed."),
        ("3. Relational Persistence (3NF SQLite):", " Ingests validated course payloads into normalized tables inside 'obe_syllabus.db' using foreign keys and ON DELETE CASCADE."),
        ("4. Human-in-the-Loop Faculty Interface (CRUD):", " Empowers faculty members to inspect, modify, and calibrate Course Learning Outcomes (CLOs) and Bloom cognitive levels prior to official signing."),
        ("5. Institutional Document Compilation (Jinja2):", " Merges relational database records with the official UPHSD CCS syllabus template ('templates/uphsd_ccs_template.html'), injecting institutional PVM, Core Values, Base-0 grading policy, and signatures, fully printable to PDF.")
    ]
    for st_title, st_desc in stages:
        p_st = doc.add_paragraph(style='List Bullet')
        r_st1 = p_st.add_run(st_title)
        r_st1.bold = True
        r_st1.font.color.rgb = COLOR_MAROON
        p_st.add_run(st_desc)

    doc.add_paragraph()

    # -------------------------------------------------------------------------
    # PART 2: ONSITE PRESENTATION SCRIPT (LEINAD & NICOLE)
    # -------------------------------------------------------------------------
    h2 = doc.add_heading("Part 2: Onsite Oral Presentation Script for Prof. Rob Malitao", level=1)
    h2.runs[0].font.color.rgb = COLOR_MAROON

    doc.add_paragraph(
        "Instructions for Presenters: Stand together in front of the classroom or projector. "
        "Leinad Clark M. Dela Cruz handles the System Introduction, Schema Engineering, and Terminal/GUI Execution. "
        "Nicole Anne G. Liwag handles the Pedagogical Alignment (Bloom's Taxonomy, K-S-A), SQLite Database Normalization, and Institutional Jinja2 Document Output. "
        "Maintain eye contact with Prof. Malitao and clearly point to the screen during [SCREEN ACTION] cues."
    )

    script_turns = [
        (
            "LEINAD CLARK M. DELA CRUZ",
            "[SCREEN ACTION: Show the Desktop GUI App or terminal banner. Point to the UPHSD Maroon header and project title.]",
            "Good morning, Prof. Rob Malitao and classmates. Today, Nicole and I are proud to present our Midterm Mini-Project in Artificial Intelligence: the AI-Powered Outcome-Based Education (OBE) Syllabus Generator Microservice for the College of Computer Studies.\n\n"
            "Every semester, faculty members spend dozens of hours writing course syllabi. Unfortunately, manual drafting often leads to passive verbs like 'understand' or 'learn' that violate CHED OBE accreditation guidelines. Our objective was to build an end-to-end, production-grade microservice that uses a local Large Language Model to draft complete, 18-week OBE syllabi—while enforcing strict deterministic boundaries using Pydantic, storing the data relationally in a 3NF SQLite database, enabling faculty Human-in-the-Loop revisions, and compiling the final document into the official CCS institutional layout."
        ),
        (
            "NICOLE ANNE G. LIWAG",
            "[SCREEN ACTION: Display the Architecture diagram or obe_schemas.py file on screen.]",
            "Thank you, Leinad. As curriculum designers and computer scientists, we recognized that Large Language Models are probabilistic by nature. Left unconstrained, an LLM might produce conversational fluff, hallucinate non-existent JSON keys, or omit critical pedagogical components.\n\n"
            "To solve this, our architecture enforces two strict layers: First, System Prompt Engineering, where we assign the LLM the persona of a College of Computer Studies Quality Assurance Expert and explicitly ban non-measurable verbs. Second, Pydantic Schema Enforcement, acting as an impenetrable guardrail. Every generated course must contain 4 to 5 Bloom-classified Course Learning Outcomes, exactly 18 weeks of detailed instruction with locked major examination milestones, and a weekly tripartite breakdown into Knowledge, Skills, and Attitude. If the model makes even a single formatting mistake, our self-healing retry loop intercepts the exception and forces the model to correct itself."
        ),
        (
            "LEINAD CLARK M. DELA CRUZ",
            "[SCREEN ACTION: Open the Native Desktop GUI ('launch_desktop_gui.bat'). Point to the Course Catalog dropdown, select 'BSCS 3109: Operating System and Configuration Use', and click 'Generate Live Syllabus (Ollama)'.]",
            "Let us demonstrate this live on our system. Right now on my screen, you are looking at our Native Python Desktop GUI, built using pure Tkinter and ttk with zero external web servers or port conflicts.\n\n"
            "We have selected 'BSCS 3109: Operating System and Configuration Use'. I will now click 'Generate Live Syllabus'. As you can see by the live progress bar and ticker, our application is querying local Qwen 2.5 running on our local NVIDIA GeForce RTX GPU via Ollama on port 11434.\n\n"
            "Notice that this is not pre-recorded text—it is actively synthesizing live tokens. Within approximately 20 seconds, Ollama produces over 3,000 tokens containing the course description, Bloom's cognitive levels, and an 18-week learning plan."
        ),
        (
            "NICOLE ANNE G. LIWAG",
            "[SCREEN ACTION: Point to the 'Generation Successful' popup. Then click on Tab 1 Right Panel, selecting CLO #2, and then clicking Week 4 in the 18-Week Schedule table.]",
            "And here is the confirmation: 'Generation Successful'! Notice what happened in the background: Pydantic validated the raw JSON payload in memory. It confirmed that Weeks 1 through 5, 7 through 11, and 13 through 17 all contain valid Teaching-Learning Activities and Assessment Tasks.\n\n"
            "Look at the right panel of Tab 1. Here in the Course Outcomes table, each outcome begins with an active Bloom's Taxonomy verb such as 'Configure', 'Implement', or 'Analyze', and is mapped to Program Outcomes. Now look below at the 18-Week Learning Plan: Week 6 is strictly locked to Preliminary Examination, Week 12 to Midterm Examination, and Week 18 to Final Examination. When we click on Week 4, the deep-dive box instantly displays the granular Lesson Learning Outcomes categorized into Knowledge [K], Skills [S], and Attitude [A], fulfilling CHED CMO No. 25 requirements."
        ),
        (
            "LEINAD CLARK M. DELA CRUZ",
            "[SCREEN ACTION: Perform Human-in-the-Loop CRUD edit: In Tab 1, select CLO #2 in the table. Change the Bloom Level combo box from 'Applying' to 'Evaluating'. In the description text box, type: 'Critically evaluate kernel scheduling algorithms and optimize thread synchronization primitives.' Click 'Save Outcome Revision (SQLite)'.]",
            "Academic accreditation requires that AI systems never bypass faculty authority. This is Milestone 2's Human-in-the-Loop CRUD feature. Suppose Prof. Malitao or the department chair reviews CLO #2 and wants a higher cognitive rigor.\n\n"
            "I simply select CLO #2, change the Bloom level to 'Evaluating', and refine the description to focus on kernel scheduling and thread synchronization. When I click 'Save Outcome Revision', the system validates the new text against Pydantic rules to prevent taboo verbs, and immediately executes a parameterized UPDATE query in SQLite. This guarantees human oversight before any document is published."
        ),
        (
            "NICOLE ANNE G. LIWAG",
            "[SCREEN ACTION: Switch to Tab 2 ('📚 2. Course Library & SQLite Database'). Show the 9 courses in the table. Point out BSCS 3109, CS 311 Data Mining, and BSN 101 Nursing.]",
            "Now let us inspect our institutional repository in Tab 2. Our database, 'obe_syllabus.db', is built strictly on 3NF relational normalization across five relational tables: courses, course_outcomes, weekly_schedules, lesson_outcomes, and grading_components.\n\n"
            "Foreign keys are strictly enforced with PRAGMA foreign_keys = ON and ON DELETE CASCADE. Notice that our database currently houses 9 complete syllabi: our newly generated BSCS 3109, alongside institutional subjects like Data Mining, AI/Machine Learning, Cybersecurity, Computer Graphics, and even Nursing Practice. If we delete a course, all child schedules and outcomes are purged cleanly without orphan records."
        ),
        (
            "LEINAD CLARK M. DELA CRUZ",
            "[SCREEN ACTION: Click '🌐 Compile & Open HTML Syllabus'. Show the browser window popping up with exports/BSCS_3109_Syllabus.html.]",
            "Finally, we assemble the official institutional document. I will now click 'Compile & Open HTML Syllabus'.\n\n"
            "Our export engine, 'export_engine.py', queries SQLite by course code, serializes the relational hierarchy, and feeds it into our Jinja2 template ('templates/uphsd_ccs_template.html'). As you can see in Google Chrome, the output is an exact match to the official UPHSD CCS Word syllabus format! It features the high-resolution university logo, Institutional Philosophy, Vision, and Mission, the Eight Perpetualite Core Values, the 18-week learning plan with color-coded K-S-A badges, the Base-0 grading policy (70% Class Standing, 30% Major Exams), and the official signature block displaying our names as curriculum leads alongside Prof. Rob Malitao."
        ),
        (
            "NICOLE ANNE G. LIWAG",
            "[SCREEN ACTION: Click the '🖨️ Print / Save as PDF' button at the top right of the HTML page, showing the print preview dialog with crisp formatting.]",
            "Furthermore, we engineered dedicated '@media print' CSS rules. When faculty click the 'Print / Save as PDF' button, all background UI controls disappear, table borders remain crisp, page breaks are strategically placed before major examination periods, and the document is ready for official accreditation signing.\n\n"
            "To prove the absolute robustness of our system, we also created an automated 6-point verification test suite in 'test_system.py' that verifies schema validation, taboo verb rejection, K-S-A enforcement, exam locking, cascading deletes, and Jinja2 compilation. All 6 tests pass with 100% compliance."
        ),
        (
            "LEINAD CLARK M. DELA CRUZ",
            "[SCREEN ACTION: Return to the Desktop GUI Tab 3 or slides. Look at Prof. Malitao for conclusion.]",
            "In conclusion, our project bridges the gap between probabilistic generative AI and strict academic accreditation standards. By combining local GPU-accelerated Ollama execution with deterministic Pydantic schemas, 3NF SQLite relational storage, faculty CRUD interfaces, and institutional Jinja2 rendering, we have delivered a complete, autonomous, and production-ready microservice for the College of Computer Studies.\n\n"
            "Thank you very much, Prof. Malitao. Nicole and I are now ready for your questions and evaluation."
        )
    ]

    for speaker, cue, speech in script_turns:
        p_spk = doc.add_paragraph()
        r_spk = p_spk.add_run(f"🎙️ {speaker}")
        r_spk.bold = True
        r_spk.font.size = Pt(11)
        r_spk.font.color.rgb = COLOR_MAROON

        p_cue = doc.add_paragraph()
        r_cue = p_cue.add_run(cue)
        r_cue.font.italic = True
        r_cue.font.size = Pt(9.5)
        r_cue.font.color.rgb = COLOR_GOLD

        p_speech = doc.add_paragraph()
        r_speech = p_speech.add_run(speech)
        r_speech.font.size = Pt(10)
        r_speech.font.color.rgb = COLOR_DARK

        doc.add_paragraph() # Spacer

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # PART 3: VIDEO DEMONSTRATION RECORDING GUIDE (3-5 MINUTES)
    # -------------------------------------------------------------------------
    h3 = doc.add_heading("Part 3: 3-5 Minute Video Demonstration Recording Guide", level=1)
    h3.runs[0].font.color.rgb = COLOR_MAROON

    doc.add_paragraph(
        "Use this exact timeline, screen action checklist, and talking points when recording your screen "
        "using OBS Studio, Windows Xbox Game Bar (Win + G), or Loom. Keep the video between 3:00 and 4:30 minutes."
    )

    v_table = doc.add_table(rows=6, cols=4)
    v_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    v_table.autofit = False

    v_headers = ["Timestamp", "Presenter", "Screen Recording Action", "Spoken Commentary & Key Focus"]
    for i, h in enumerate(v_headers):
        cell = v_table.rows[0].cells[i]
        set_cell_background(cell, "800000")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    v_data = [
        (
            "0:00 – 0:45",
            "Leinad",
            "Show Project Folder & Architecture in VS Code / File Explorer.\nShow 'desktop_gui.py', 'obe_schemas.py', 'schema.sql', 'templates/'.",
            "Introduce yourselves (Leinad Clark Dela Cruz & Nicole Anne Liwag), course (BSCS 3112 AI Lab), and instructor (Prof. Rob Malitao). State the core problem: manual syllabus drafting has non-measurable verbs and fails OBE compliance."
        ),
        (
            "0:45 – 1:45",
            "Leinad",
            "Launch 'launch_desktop_gui.bat'.\nSelect 'BSCS 3109: Operating System and Configuration Use' (or enter custom description).\nClick 'Generate Live Syllabus (Ollama)'.\nShow progress bar and token ticker.",
            "Explain that Ollama is synthesizing tokens live on the RTX GPU using Qwen 2.5. Explain Pydantic schema enforcement: taboo verbs ('understand', 'know') are banned, 18 weeks are enforced with Prelim/Midterm/Final exam locks."
        ),
        (
            "1:45 – 2:30",
            "Nicole",
            "Point to 'Generation Successful' popup.\nShow Tab 1 Right Panel: Course Outcomes table & 18-Week matrix.\nClick Week 4 to show K-S-A breakdown.",
            "Explain pedagogical alignment. Course outcomes begin with active Bloom's verbs. The weekly schedule divides every lesson into Knowledge (K), Skills (S), and Attitude (A) following CHED CMO No. 25 s. 2015."
        ),
        (
            "2:30 – 3:15",
            "Leinad",
            "Human-in-the-Loop Faculty Edit:\nSelect CLO #2 in Tab 1.\nChange Bloom verb to 'Evaluating'.\nType updated description.\nClick 'Save Outcome Revision (SQLite)'.",
            "Demonstrate faculty oversight (CRUD). Faculty can review AI-generated outcomes, adjust cognitive levels, and persist updates into SQLite. The system validates the edit before committing to prevent errors."
        ),
        (
            "3:15 – 4:00",
            "Nicole",
            "Switch to Tab 2 to show the SQLite repository with 9 courses.\nThen click '🌐 Compile & Open HTML Syllabus'.\nShow browser window and click 'Print / Save as PDF'.",
            "Explain 3NF database normalization and cascading deletes in SQLite. Show Jinja2 document generation matching UPHSD CCS institutional layout with logo, PVM, Core Values, and developer/instructor signature blocks."
        )
    ]

    col_widths = [Inches(1.0), Inches(0.9), Inches(2.2), Inches(2.4)]
    for r_idx, row_data in enumerate(v_data, start=1):
        row = v_table.rows[r_idx]
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, text in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.width = col_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=90, right=90)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(8.5)
            r.font.color.rgb = COLOR_DARK
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_MAROON

    doc.add_paragraph()
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # PART 4: PROF. ROB MALITAO Q&A DEFENSE CHEAT SHEET
    # -------------------------------------------------------------------------
    h4 = doc.add_heading("Part 4: Defense Q&A Preparation (Anticipated Questions)", level=1)
    h4.runs[0].font.color.rgb = COLOR_MAROON

    doc.add_paragraph(
        "Prof. Rob Malitao will likely test your theoretical understanding during or after the demonstration. "
        "Here are the top 5 anticipated technical questions along with high-scoring answers:"
    )

    qa_list = [
        (
            "Q1: Ollama already provides format='json'. Why do you still need Pydantic?",
            "Nicole: 'Ollama's format='json' only guarantees syntactic validity—meaning it ensures brackets and quotes form valid JSON. It has zero semantic understanding of academic pedagogy. It does not know that 'understand' is a non-measurable verb, it cannot guarantee exactly 18 weeks, and it cannot ensure that grading weights total 100%. Pydantic serves as our deterministic runtime contract: it validates data types, enforces regex constraints on Bloom verbs, checks K-S-A categorization, and auto-prompts the model if any rule is violated.'"
        ),
        (
            "Q2: How did you implement the taboo verb restriction in your code?",
            "Leinad: 'In 'obe_schemas.py', we implemented a Pydantic @field_validator on the course outcome description and lesson outcome text. The validator extracts the first action verb, converts it to lowercase, and checks it against a disallowed set: {'understand', 'know', 'learn', 'study', 'be familiar with'}. If a taboo verb is detected, Pydantic immediately raises a ValueError. In our LLM engine, this exception triggers an automatic re-prompt injecting corrective feedback back to Qwen.'"
        ),
        (
            "Q3: Explain your SQLite schema normalization. Why is ON DELETE CASCADE important?",
            "Nicole: 'Our database 'obe_syllabus.db' is strictly normalized to Third Normal Form (3NF). We have five tables: courses is the parent table, while course_outcomes, weekly_schedules, lesson_outcomes, and grading_components are child tables referencing courses.id via foreign keys. ON DELETE CASCADE is critical for relational integrity: when a course is deleted from the institutional repository, SQLite automatically purges all child weekly schedules, lesson outcomes, and grading components in a single atomic transaction, preventing orphan records.'"
        ),
        (
            "Q4: How does your 18-week schedule align with CHED CMO No. 25 s. 2015 and UPHSD policy?",
            "Leinad: 'CHED mandates an 18-week semester structure for collegiate computer science. Our Pydantic schema enforces that the weekly schedule array has exactly 18 elements. Furthermore, institutional policy mandates three major examination milestones: Week 6 is locked to Preliminary Examination, Week 12 to Midterm Examination, and Week 18 to Final Examination. Non-exam weeks strictly mandate IT hands-on laboratory Teaching-Learning Activities (TLAs) and observable Result Evidence.'"
        ),
        (
            "Q5: How does the Jinja2 template render the document without a live web server?",
            "Nicole: 'In 'export_engine.py', we query SQLite by course_code to assemble a full hierarchical Python dictionary. We then initialize a Jinja2 Environment with a FileSystemLoader pointing to 'templates/uphsd_ccs_template.html'. Jinja2 injects the variables into the HTML string, which we write to disk as a static standalone file in 'exports/'. Because CSS, base64 logo data, and print styles are embedded directly, the HTML file opens natively in any standard web browser (Chrome, Edge) and prints to PDF with zero web server dependencies.'"
        )
    ]

    for q, a in qa_list:
        p_q = doc.add_paragraph()
        r_q = p_q.add_run(q)
        r_q.bold = True
        r_q.font.size = Pt(10.5)
        r_q.font.color.rgb = COLOR_MAROON

        p_a = doc.add_paragraph()
        r_a = p_a.add_run(a)
        r_a.font.size = Pt(9.5)
        r_a.font.color.rgb = COLOR_DARK
        doc.add_paragraph()

    # -------------------------------------------------------------------------
    # PART 5: RUBRIC SCORECARD (100 / 100 POINTS)
    # -------------------------------------------------------------------------
    h5 = doc.add_heading("Part 5: Assessment Rubric Compliance Scorecard", level=1)
    h5.runs[0].font.color.rgb = COLOR_MAROON

    r_table = doc.add_table(rows=5, cols=3)
    r_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    r_table.autofit = False

    r_headers = ["Rubric Criteria", "Weight", "Evidence in Codebase & Demonstration"]
    for i, h in enumerate(r_headers):
        cell = r_table.rows[0].cells[i]
        set_cell_background(cell, "800000")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    r_data = [
        ("Pydantic Schema & LLM Enforcement", "25%", "obe_schemas.py & llm_engine.py: Ollama format='json' with 3-attempt automated self-healing retry loop. Validates types, regex, and nested structures."),
        ("OBE Domain Alignment (Bloom's KSA)", "25%", "Bans non-measurable verbs ('understand', 'know'). Categorizes weekly LLOs into Knowledge [K], Skills [S], Attitude [A]. Locks W6 Prelim, W12 Midterm, W18 Final."),
        ("Database Design & CRUD Logic", "25%", "schema.sql & db_manager.py: 3NF normalized SQLite database with ON DELETE CASCADE. Faculty can edit CLOs in real-time before persisting."),
        ("Jinja2 Templating & Document Export", "25%", "templates/uphsd_ccs_template.html & export_engine.py: Generates official UPHSD layout with logo, PVM, Core Values, 18-week plan, and Base-0 grading. 1-click Print to PDF.")
    ]

    r_widths = [Inches(2.0), Inches(0.8), Inches(3.7)]
    for r_idx, row_data in enumerate(r_data, start=1):
        row = r_table.rows[r_idx]
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, text in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.width = r_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=90, right=90)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(8.5)
            r.font.color.rgb = COLOR_DARK
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_MAROON
            elif c_idx == 1:
                r.bold = True
                r.font.color.rgb = COLOR_GOLD

    doc.save("ON_SITE_PRESENTATION_SCRIPT.docx")
    print("[OK] Successfully generated ON_SITE_PRESENTATION_SCRIPT.docx!")

if __name__ == "__main__":
    create_document()
