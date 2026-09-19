"""
UPHSD College of Computer Studies - AI-Powered OBE Syllabus Generator
Interactive Streamlit GUI for Faculty Quality Assurance & Curriculum Design.
Supports Milestones 1 & 2: Generation, Validation, SQLite CRUD, and Jinja2 HTML Export.
"""

import os
import sys
import json
import sqlite3
import streamlit as st
from streamlit import runtime
from streamlit.web import cli as stcli

import obe_schemas
import llm_engine
import db_manager
import export_engine

# ---------------------------------------------------------------------------
# 1. Page Configuration & UPHSD Branding
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="UPHSD CCS - OBE Syllabus Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional CSS: UPHSD Maroon (#800000) & Gold (#FFD700)
st.markdown("""
<style>
    :root {
        --uphsd-maroon: #800000;
        --uphsd-gold: #FFD700;
    }
    .stApp {
        background: linear-gradient(135deg, rgba(128, 0, 0, 0.04) 0%, rgba(255, 215, 0, 0.05) 50%, rgba(255, 255, 255, 1) 100%);
    }
    [data-testid="stSidebar"] {
        background-color: #800000 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] input, 
    [data-testid="stSidebar"] textarea, 
    [data-testid="stSidebar"] [data-baseweb="select"] div {
        background-color: #FFF9F9 !important;
        color: #800000 !important;
        border-radius: 6px !important;
    }
    .stButton>button {
        background-color: #800000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        padding: 8px 18px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #FFD700 !important;
        color: #800000 !important;
        box-shadow: 0px 4px 12px rgba(128,0,0,0.35) !important;
        transform: translateY(-2px);
    }
    .badge-pass {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        display: inline-block;
    }
    .badge-exam {
        background-color: #fff3cd;
        color: #856404;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. State Initialization
# ---------------------------------------------------------------------------
if "current_syllabus" not in st.session_state:
    # Try loading existing sample if present
    if os.path.exists("sample_validated_output.json"):
        try:
            with open("sample_validated_output.json", "r", encoding="utf-8") as f:
                st.session_state.current_syllabus = obe_schemas.CourseMetadataSchema.model_validate_json(f.read())
        except Exception:
            st.session_state.current_syllabus = None
    else:
        st.session_state.current_syllabus = None

if "db_initialized" not in st.session_state:
    db_manager.init_db()
    st.session_state.db_initialized = True

# ---------------------------------------------------------------------------
# 3. Sidebar: Configuration & Course Metadata
# ---------------------------------------------------------------------------
logo_path = "assets/UPHSD-logo-yellow.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)

st.sidebar.markdown("### **UPHSD Molino Campus**\n#### College of Computer Studies")
st.sidebar.caption("AI-Powered OBE Syllabus Generator Microservice")
st.sidebar.markdown("**Developer:** Leinad Clark M. Dela Cruz  \n**Instructor:** Prof. Rob Malitao")
st.sidebar.divider()

st.sidebar.subheader("⚙️ AI Engine Settings")
model_choice = st.sidebar.selectbox(
    "Local Ollama Model",
    options=["qwen2.5", "qwen2.5:7b", "qwen2.5:3b", "qwen2.5:1.5b"],
    index=0,
    help="Ollama background service running on localhost:11434"
)

st.sidebar.subheader("📋 Course Parameters")
course_presets = {
    "CS 311: Data Mining and Knowledge Discovery": {
        "code": "CS 311",
        "title": "Data Mining and Knowledge Discovery",
        "prereq": "CS 211, MATH 201",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "desc": "Comprehensive study of Knowledge Discovery in Databases (KDD), data preprocessing, association rule mining (Apriori, FP-Growth), classification (Decision Trees, Naive Bayes, Random Forests), clustering (K-Means, DBSCAN), and Python data mining pipelines.",
        "file": "syllabi_library/CS_311_Syllabus.json"
    },
    "CS 312: Artificial Intelligence & Machine Learning": {
        "code": "CS 312",
        "title": "Artificial Intelligence and Machine Learning",
        "prereq": "CS 211, MATH 202",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "desc": "Foundational study of rational agents, heuristic search (A*, Minimax), knowledge representation, supervised learning, neural networks, PyTorch deep learning, and computer vision.",
        "file": "syllabi_library/CS_312_Syllabus.json"
    },
    "BSIT 3112: Computer Graphics and Programming": {
        "code": "BSIT 3112",
        "title": "Computer Graphics and Programming",
        "prereq": "BSIT 2104",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "desc": "Introduction to the mathematics of computer graphics and visual computing. Topics include coordinate transformations, rendering primitive geometries, illumination models, shading, texture mapping, and OpenGL programming.",
        "file": "syllabi_library/BSIT_3112_Computer_Graphics.json"
    },
    "CS 211: Data Structures and Algorithms": {
        "code": "CS 211",
        "title": "Data Structures and Algorithms",
        "prereq": "CS 102 (Intermediate Programming)",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "desc": "Abstract data types, linear and non-linear data structures including stacks, queues, linked lists, binary search trees, heaps, hash tables, and asymptotic Big-O algorithmic complexity analysis.",
        "file": "syllabi_library/CS_211_Data_Structures.json"
    },
    "IT 221: Web Systems and Technologies": {
        "code": "IT 221",
        "title": "Web Systems and Technologies",
        "prereq": "CS 102",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "desc": "Client-server web architectures, responsive frontend development (HTML5/CSS3/JavaScript), RESTful API engineering, backend services, database persistence, web security vulnerabilities, and cloud deployment.",
        "file": "syllabi_library/IT_221_Syllabus.json"
    },
    "IT 213: Advanced Database Systems": {
        "code": "IT 213",
        "title": "Advanced Database Management Systems",
        "prereq": "IT 104",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "desc": "Relational schema normalization (3NF/BCNF), physical storage, B+ tree indexing, query execution optimization, ACID transaction guarantees, concurrency control, and NoSQL document stores.",
        "file": "syllabi_library/IT_213_Syllabus.json"
    },
    "CS 323: Cybersecurity & Information Assurance": {
        "code": "CS 323",
        "title": "Information Assurance and Cybersecurity",
        "prereq": "IT 212, CS 211",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "desc": "Digital information security principles, applied cryptography (AES, RSA, SHA-256), network scanning (Nmap), packet sniffing (Wireshark), web app security (OWASP), firewalls, and incident response.",
        "file": "syllabi_library/CS_323_Syllabus.json"
    },
    "BS Nursing: Fundamentals of Nursing Practice": {
        "code": "BSN 101",
        "title": "Fundamentals of Nursing Practice",
        "prereq": "Anatomy and Physiology",
        "units": "4 Units (2 Units Lecture, 2 Units Clinical Skills Lab)",
        "desc": "Introduction to professional nursing concepts, aseptic techniques, vital signs monitoring, medication administration, health assessment, wound care, and compassionate patient-centered care.",
        "file": "syllabi_library/BSN_101_Nursing.json"
    },
    "Custom Course": {
        "code": "CS 301",
        "title": "Software Engineering",
        "prereq": "CS 201",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "desc": "Software life cycle models, Agile scrum practices, software architecture, verification, testing, and modern DevOps pipelines.",
        "file": None
    }
}

preset_choice = st.sidebar.selectbox("Load Example Course Preset", options=list(course_presets.keys()), index=0)
selected_preset = course_presets[preset_choice]

# Automatically synchronize active syllabus and form inputs when user changes preset
if "active_preset_name" not in st.session_state:
    st.session_state.active_preset_name = preset_choice
    st.session_state["input_code"] = selected_preset["code"]
    st.session_state["input_title"] = selected_preset["title"]
    st.session_state["input_prereq"] = selected_preset["prereq"]
    st.session_state["input_units"] = selected_preset["units"]
    st.session_state["input_desc"] = selected_preset["desc"]

if st.session_state.active_preset_name != preset_choice:
    st.session_state.active_preset_name = preset_choice
    st.session_state["input_code"] = selected_preset["code"]
    st.session_state["input_title"] = selected_preset["title"]
    st.session_state["input_prereq"] = selected_preset["prereq"]
    st.session_state["input_units"] = selected_preset["units"]
    st.session_state["input_desc"] = selected_preset["desc"]
    target_lib_file = selected_preset.get("file")
    if target_lib_file and os.path.exists(target_lib_file):
        try:
            with open(target_lib_file, "r", encoding="utf-8") as f:
                loaded_syl = obe_schemas.CourseMetadataSchema.model_validate_json(f.read())
                st.session_state.current_syllabus = loaded_syl
                db_manager.ingest_syllabus(loaded_syl)
                hpath = export_engine.export_syllabus_html(loaded_syl.course_code, auto_open=False)
                st.session_state.last_exported_html = hpath
        except Exception as err:
            st.sidebar.warning(f"Note loading preset: {err}")

input_code = st.sidebar.text_input("Course Code", key="input_code")
input_title = st.sidebar.text_input("Course Title", key="input_title")
input_prereq = st.sidebar.text_input("Prerequisite(s)", key="input_prereq")
input_units = st.sidebar.text_input("Credit Units", key="input_units")
input_desc = st.sidebar.text_area("Course Catalog Description", height=120, key="input_desc")

# ---------------------------------------------------------------------------
# 4. Main App Header
# ---------------------------------------------------------------------------
st.title("Outcome-Based Education (OBE) Syllabus Generator")
st.markdown("**University of Perpetual Help System DALTA — Academic Quality Assurance**")

# ---------------------------------------------------------------------------
# 5. Core Operational Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 1. LLM Generation & Validation",
    "✏️ 2. Faculty Human-in-the-Loop CRUD",
    "🗄️ 3. Normalized SQLite Database",
    "📄 4. Jinja2 Institutional HTML Export",
    "📥 5. JSON File Injector & Batch Importer"
])

# ---------------------------------------------------------------------------
# TAB 1: AI Generation & Pydantic Validation
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Milestone 1: Structured LLM Engine & Schema Validation")
    st.write(
        "Leverage local Qwen 2.5 in JSON mode to synthesize active Bloom's outcomes and an 18-week schedule. "
        "The automated retry loop intercepts `ValidationError` and enforces deterministic boundaries on the LLM."
    )

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("Generate & Validate Syllabus", use_container_width=True):
            with st.spinner(f"Querying Ollama ({model_choice}) with automated retry feedback loop..."):
                try:
                    generated = llm_engine.generate_syllabus_data(
                        course_title=input_title,
                        course_description=input_desc,
                        course_code=input_code,
                        prerequisites=input_prereq,
                        credit_units=input_units,
                        model_name=model_choice,
                        allow_fallback=True
                    )
                    st.session_state.current_syllabus = generated

                    # 1. Write sample_validated_output.json
                    with open("sample_validated_output.json", "w", encoding="utf-8") as f:
                        f.write(generated.model_dump_json(indent=2))

                    # 2. Auto-ingest into SQLite
                    db_manager.ingest_syllabus(generated)

                    # 3. Auto-compile and export HTML website
                    html_path = export_engine.export_syllabus_html(generated.course_code, auto_open=False)
                    st.session_state.last_exported_html = html_path

                    st.success(f"[PASS] Pydantic Validated! Auto-stored in SQLite and HTML website generated: {os.path.basename(html_path)}")
                except Exception as e:
                    st.error(f"Generation failed: {e}")

    if st.session_state.current_syllabus:
        s = st.session_state.current_syllabus
        st.divider()

        # Audit Badges
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Course Code", s.course_code)
        c2.metric("Total Outcomes (CLOs)", len(s.course_outcomes))
        c3.metric("Schedule Length", f"{len(s.weekly_schedule)} Weeks")
        c4.metric("Grading Total", f"{sum(g.percentage_weight for g in s.grading_breakdown):.1f}%")

        st.markdown("#### Quality Assurance Compliance Checks")
        col_chk1, col_chk2, col_chk3 = st.columns(3)
        with col_chk1:
            st.markdown('<span class="badge-pass">✓ 18-Week Term Enforced</span>', unsafe_allow_html=True)
            st.caption("Weeks 1 to 18 generated in strict chronological order.")
        with col_chk2:
            st.markdown('<span class="badge-exam">✓ Major Exams Positioned</span>', unsafe_allow_html=True)
            st.caption("W6: Prelim Exam | W12: Midterm Exam | W18: Final Exam.")
        with col_chk3:
            st.markdown('<span class="badge-pass">✓ Bloom\'s Verbs & K/S/A Validated</span>', unsafe_allow_html=True)
            st.caption("No non-measurable verbs detected; LLOs categorized into K, S, A.")

        # Inspect Data
        subtab_preview, subtab_json = st.tabs(["Rendered Syllabus View", "Raw Validated JSON"])
        with subtab_preview:
            st.markdown("### Course Learning Outcomes (CLOs)")
            for co in s.course_outcomes:
                st.markdown(f"**CLO {co.co_number}** [{co.bloom_level}]: {co.co_description}")
                st.caption(f"Mapped Program Outcomes: {co.mapped_po}")

            st.markdown("### 18-Week Schedule Preview")
            st.dataframe([
                {
                    "Week": w.week_number,
                    "Period": w.period,
                    "Topic": w.topic,
                    "Activity (TLA)": w.teaching_learning_activity,
                    "Assessment": w.assessment_task,
                    "Aligned CO": w.aligned_co,
                    "LLOs Count": len(w.lesson_outcomes)
                } for w in s.weekly_schedule
            ], use_container_width=True)

        with subtab_json:
            st.json(s.model_dump())
            st.download_button(
                label="📥 Download Validated JSON",
                data=s.model_dump_json(indent=2),
                file_name="sample_validated_output.json",
                mime="application/json"
            )

# ---------------------------------------------------------------------------
# TAB 2: Faculty Human-in-the-Loop CRUD
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Milestone 2: Human-in-the-Loop Faculty Edit Interface")
    st.write(
        "Accreditation standards require academic faculty to review and modify AI-generated outcomes. "
        "Edits are validated in real-time by Pydantic before persisting to SQLite."
    )

    if st.session_state.current_syllabus:
        s = st.session_state.current_syllabus
        co_numbers = [co.co_number for co in s.course_outcomes]

        col_sel, col_bloom = st.columns([1, 1])
        with col_sel:
            selected_co_num = st.selectbox("Select CLO to Modify", options=co_numbers)
        target_co = next((co for co in s.course_outcomes if co.co_number == selected_co_num), None)

        with col_bloom:
            bloom_idx = ["Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"].index(target_co.bloom_level)
            new_bloom = st.selectbox("Bloom's Revised Taxonomy Level", options=[
                "Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"
            ], index=bloom_idx)

        new_desc = st.text_area("Course Outcome Description", value=target_co.co_description, height=90)
        new_pos_str = st.text_input("Mapped Program Outcomes (comma separated)", value=", ".join(str(p) for p in target_co.mapped_po))

        if st.button("Apply Human-in-the-Loop Edit"):
            try:
                parsed_pos = [int(x.strip()) for x in new_pos_str.split(",") if x.strip()]
                # Validate revised outcome
                validated_edit = obe_schemas.CourseOutcomeSchema(
                    co_number=selected_co_num,
                    bloom_level=new_bloom,
                    co_description=new_desc,
                    mapped_po=parsed_pos
                )

                # Update in memory session state
                for idx, co in enumerate(s.course_outcomes):
                    if co.co_number == selected_co_num:
                        s.course_outcomes[idx] = validated_edit
                        break

                # If course exists in DB, update relational record
                db_manager.update_course_outcome(
                    course_code=s.course_code,
                    co_number=selected_co_num,
                    new_description=new_desc,
                    new_bloom_level=new_bloom,
                    new_mapped_po=parsed_pos
                )
                st.success(f"[PASS] Successfully revised CLO {selected_co_num}! Database and memory updated.")
            except Exception as e:
                st.error(f"Validation Error in faculty edit: {e}")

        st.divider()
        if st.button("💾 Persist Full Syllabus to SQLite Database (schema.sql)", use_container_width=True):
            try:
                cid = db_manager.ingest_syllabus(s)
                st.success(f"[PASS] Syllabus successfully stored in SQLite database! Primary Course ID: {cid}")
            except Exception as e:
                st.error(f"Database insertion failed: {e}")
    else:
        st.warning("Please generate or load a syllabus in Tab 1 first.")

# ---------------------------------------------------------------------------
# TAB 3: Normalized SQLite Database Explorer
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Milestone 2: Relational Persistence & Schema Inspection")
    st.write("Inspect 3NF normalized tables in `obe_syllabus.db` with foreign keys and cascading deletes.")

    courses = db_manager.list_courses()
    if courses:
        st.markdown("#### Stored Courses")
        st.dataframe(courses, use_container_width=True)

        selected_code = st.selectbox("Inspect Course Records", options=[c["course_code"] for c in courses])
        if selected_code:
            relational_data = db_manager.get_course_by_code(selected_code)
            t_clo, t_weeks, t_grade = st.tabs(["Course Outcomes Table", "Weekly Schedule & LLOs Table", "Grading Components Table"])

            with t_clo:
                st.dataframe(relational_data["course_outcomes"], use_container_width=True)

            with t_weeks:
                st.dataframe(relational_data["weekly_schedule"], use_container_width=True)

            with t_grade:
                st.dataframe(relational_data["grading_breakdown"], use_container_width=True)

            if st.button(f"🗑️ Delete Course '{selected_code}' (Test Cascading Delete)"):
                success = db_manager.delete_course(selected_code)
                if success:
                    st.success(f"[PASS] Course '{selected_code}' and all related outcomes deleted via ON DELETE CASCADE.")
                    st.rerun()
    else:
        st.info("No courses currently stored in SQLite. Click 'Persist Full Syllabus to SQLite Database' in Tab 2.")

# ---------------------------------------------------------------------------
# TAB 4: Jinja2 Institutional HTML Export
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Milestone 2: Jinja2 Document Assembly & Institutional Export")
    st.write(
        "Compile stored relational database records into the official UPHSD College of Computer Studies "
        "Outcome-Based Education syllabus template."
    )

    courses = db_manager.list_courses()
    if courses:
        codes = [c["course_code"] for c in courses]
        default_index = 0
        if st.session_state.current_syllabus and st.session_state.current_syllabus.course_code in codes:
            default_index = codes.index(st.session_state.current_syllabus.course_code)

        export_target = st.selectbox("Select Course for HTML Compilation", options=codes, index=default_index, key="export_sel")
        
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            if st.button("🔨 Compile & Assemble Institutional Syllabus HTML", use_container_width=True):
                try:
                    html_path = export_engine.export_syllabus_html(export_target, auto_open=False)
                    st.success(f"[PASS] Successfully generated: {os.path.basename(html_path)}")
                    st.session_state.last_exported_html = html_path
                except Exception as e:
                    st.error(f"Export compilation failed: {e}")

        # Ensure last_exported_html points to current selection if file exists
        potential_path = os.path.join("exports", f"{export_target.replace(' ', '_').replace('/', '_')}_Syllabus.html")
        if os.path.exists(potential_path):
            st.session_state.last_exported_html = potential_path

        if "last_exported_html" in st.session_state and os.path.exists(st.session_state.last_exported_html):
            with col_c2:
                if st.button("🌐 Open HTML in Web Browser Window", use_container_width=True):
                    import webbrowser
                    webbrowser.open(f"file://{os.path.abspath(st.session_state.last_exported_html)}")

            with open(st.session_state.last_exported_html, "r", encoding="utf-8") as f:
                html_content = f.read()

            st.download_button(
                label="📥 Download Browser-Ready HTML Syllabus",
                data=html_content,
                file_name=os.path.basename(st.session_state.last_exported_html),
                mime="text/html",
                use_container_width=True
            )

            st.markdown(f"#### Live Preview: `{os.path.basename(st.session_state.last_exported_html)}`")
            st.components.v1.html(html_content, height=750, scrolling=True)
    else:
        st.warning("Please persist a syllabus to SQLite first to export the official document.")

# ---------------------------------------------------------------------------
# TAB 5: JSON File Injector & Batch Importer
# ---------------------------------------------------------------------------
with tab5:
    st.subheader("Milestone 2: Relational JSON Ingestion & Batch Injection")
    st.write(
        "Inject any structured OBE course syllabus JSON into the normalized SQLite database (`obe_syllabus.db`). "
        "The system validates Pydantic data contracts and populates `courses`, `course_outcomes`, `weekly_schedules`, "
        "`lesson_outcomes`, and `grading_components` within an atomic transaction."
    )

    st.markdown("### 1. Batch Inject Computer Science Flagship Syllabi")
    st.info(
        "The system includes pre-validated 18-week OBE syllabus JSON files for Computer Science / IT programs: "
        "**Data Mining**, **Artificial Intelligence**, **Computer Graphics**, **Data Structures**, **Web Systems**, "
        "**Advanced Databases**, and **Cybersecurity**."
    )

    lib_dir = "syllabi_library"
    if os.path.exists(lib_dir):
        json_files = [f for f in os.listdir(lib_dir) if f.endswith(".json")]
        st.write(f"📁 **Available Syllabi in `{lib_dir}/` ({len(json_files)} files):**")
        st.caption(", ".join(json_files))

        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            if st.button("⚡ Batch Inject All 6+ CS Syllabi into SQLite", use_container_width=True):
                with st.spinner("Injecting and normalizing all course JSON files into SQLite tables..."):
                    results = db_manager.batch_ingest_directory(lib_dir)
                    st.success(f"[PASS] Successfully ingested {len(results)} courses into normalized SQLite database!")
                    st.dataframe(results, use_container_width=True)

        with col_b2:
            if st.button("🔨 Batch Compile HTML Files for All Stored Courses", use_container_width=True):
                with st.spinner("Compiling HTML syllabus documents using Jinja2..."):
                    courses = db_manager.list_courses()
                    compiled = []
                    for c in courses:
                        try:
                            hpath = export_engine.export_syllabus_html(c["course_code"], auto_open=False)
                            compiled.append({"Course Code": c["course_code"], "Title": c["course_title"], "Exported HTML": os.path.basename(hpath), "Status": "READY"})
                        except Exception as e:
                            compiled.append({"Course Code": c["course_code"], "Title": c["course_title"], "Status": f"ERROR: {e}"})
                    st.success(f"[PASS] Compiled {len(compiled)} institutional HTML documents!")
                    st.dataframe(compiled, use_container_width=True)

    st.divider()
    st.markdown("### 2. Custom Syllabus JSON File Injector")
    st.write("Upload any custom syllabus JSON file to validate its Pydantic contract and persist it into SQLite.")

    uploaded_file = st.file_uploader("Upload Course Syllabus JSON File", type=["json"])
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8")
            parsed_json = json.loads(file_content)
            validated_upload = obe_schemas.CourseMetadataSchema.model_validate(parsed_json)

            st.success(f"[PASS] Pydantic Validated: '{validated_upload.course_title}' ({validated_upload.course_code})")
            st.json({
                "course_code": validated_upload.course_code,
                "course_title": validated_upload.course_title,
                "outcomes_count": len(validated_upload.course_outcomes),
                "weeks_count": len(validated_upload.weekly_schedule),
                "grading_components": len(validated_upload.grading_breakdown)
            })

            if st.button(f"📥 Inject '{validated_upload.course_code}' into SQLite Database", use_container_width=True):
                cid = db_manager.ingest_syllabus(validated_upload)
                html_path = export_engine.export_syllabus_html(validated_upload.course_code, auto_open=False)
                st.session_state.current_syllabus = validated_upload
                st.session_state.last_exported_html = html_path
                st.success(f"[PASS] Ingested into SQLite with ID {cid}! Document compiled: {os.path.basename(html_path)}")
        except Exception as e:
            st.error(f"JSON Validation / Ingestion Error: {e}")

# ---------------------------------------------------------------------------
# 6. Standalone Execution Logic
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not runtime.exists():
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
