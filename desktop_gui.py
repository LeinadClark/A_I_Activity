"""
UPHSD College of Computer Studies - AI-Powered OBE Syllabus Generator
Native Desktop Python GUI Application (Tkinter / TTK)
Compatible with Python 3.10+ on Windows / Linux / macOS.
"""

import os
import sys
import json
import time
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# Ensure working directory is always the script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import obe_schemas
import llm_engine
import db_manager
import export_engine


# Institutional Color Palette (UPHSD Maroon & Gold Theme)
COLOR_MAROON = "#7B1113"
COLOR_MAROON_DARK = "#5A0B0D"
COLOR_GOLD = "#DAA520"
COLOR_BG = "#F1F5F9"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT_MAIN = "#0F172A"
COLOR_TEXT_MUTED = "#64748B"
COLOR_BORDER = "#CBD5E1"
COLOR_SUCCESS = "#16A34A"
COLOR_PRIMARY_BLUE = "#2563EB"
COLOR_HIGHLIGHT = "#FEF3C7"


PRESETS = [
    {
        "code": "CS 311",
        "title": "Data Mining and Knowledge Discovery",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "prereq": "CS 211 (Data Structures), MATH 201 (Statistics)",
        "desc": (
            "Comprehensive study of Knowledge Discovery in Databases (KDD), data preprocessing, "
            "association rule mining (Apriori, FP-Growth), classification algorithms (Decision Trees, Naive Bayes, "
            "Random Forests), clustering (K-Means, DBSCAN), and Python data mining pipelines with scikit-learn."
        )
    },
    {
        "code": "CS 312",
        "title": "Artificial Intelligence and Machine Learning",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "prereq": "CS 211 (Data Structures), MATH 202 (Linear Algebra)",
        "desc": (
            "Foundations of rational agents, uninformed and informed heuristic search (A*, Minimax), "
            "knowledge representation, supervised/unsupervised machine learning, neural networks, "
            "PyTorch deep learning architectures, and modern computer vision/NLP applications."
        )
    },
    {
        "code": "CS 323",
        "title": "Information Assurance and Cybersecurity",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "prereq": "IT 212 (Computer Networks), CS 211 (Data Structures)",
        "desc": (
            "Digital information security principles, applied cryptography (AES, RSA, SHA-256), "
            "network reconnaissance with Nmap, packet analysis with Wireshark, OWASP Top 10 vulnerabilities, "
            "firewall architectures, security policies, and incident response procedures."
        )
    },
    {
        "code": "IT 221",
        "title": "Web Systems and Technologies",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "prereq": "CS 102 (Intermediate Programming)",
        "desc": (
            "Client-server web architectures, modern responsive frontend development (HTML5/CSS3/JavaScript), "
            "RESTful API design and consumption, backend server frameworks, relational database persistence, "
            "authentication/authorization protocols, and containerized cloud deployment."
        )
    },
    {
        "code": "BSIT 3112",
        "title": "Computer Graphics and Programming",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "prereq": "BSIT 2104 (Object-Oriented Programming)",
        "desc": (
            "Introduction to the mathematics of computer graphics and 3D visual computing. "
            "Topics include coordinate frames, vector mathematics, primitive rasterization, "
            "2D/3D affine transformations, projection frustums, lighting models (Phong), "
            "shading techniques, texture mapping, and OpenGL programming with GPU pipeline optimization."
        )
    },
    {
        "code": "BSN 101",
        "title": "Fundamentals of Nursing Practice",
        "units": "4 Units (2 Units Lecture, 2 Units Clinical Laboratory)",
        "prereq": "Anatomy and Physiology with Pathophysiology",
        "desc": (
            "Foundational principles of professional nursing practice, patient-centered care, "
            "vital signs monitoring and physiological assessment, aseptic technique and infection control, "
            "pharmacological dosage calculations, parenteral medication administration, and bioethical standards."
        )
    },
    {
        "code": "CS 401",
        "title": "Cloud Computing and Distributed Systems",
        "units": "3 Units (2 Units Lecture, 1 Unit Laboratory)",
        "prereq": "IT 212 (Computer Networks), IT 221 (Web Systems)",
        "desc": (
            "Principles of distributed systems, cloud computing service models (IaaS, PaaS, Serverless), "
            "virtualization, microservices architecture, Docker containers, Kubernetes orchestration, "
            "and cloud-native database replication."
        )
    }
]


class OBESyllabusDesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UPHSD College of Computer Studies — AI OBE Syllabus Generator")
        self.geometry("1220x840")
        self.minsize(1050, 720)
        self.configure(bg=COLOR_BG)

        # Active Data State
        self.current_syllabus = None
        self.last_exported_html = None
        self.db_path = "obe_syllabus.db"

        # Initialize SQLite database
        try:
            db_manager.init_db(self.db_path)
            if os.path.exists("syllabi_library"):
                existing = db_manager.list_courses(self.db_path)
                if len(existing) == 0:
                    db_manager.batch_ingest_directory("syllabi_library", db_path=self.db_path)
        except Exception as e:
            print(f"Database init warning: {e}")

        self._setup_styles()
        self._build_header()
        self._build_main_notebook()
        self._check_ollama_daemon()

        # Load first preset into inputs by default
        self._load_preset_to_inputs(0)

    def _setup_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(".", font=("Segoe UI", 10), background=COLOR_BG)
        self.style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI Semibold", 10),
            padding=[16, 8],
            background="#E2E8F0",
            foreground="#334155"
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", COLOR_MAROON)],
            foreground=[("selected", "#FFFFFF")]
        )

        self.style.configure(
            "Primary.TButton",
            font=("Segoe UI Semibold", 10),
            background=COLOR_MAROON,
            foreground="#FFFFFF",
            padding=[12, 6],
            borderwidth=0
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", COLOR_MAROON_DARK), ("disabled", "#94A3B8")]
        )

        self.style.configure(
            "Success.TButton",
            font=("Segoe UI Semibold", 10),
            background=COLOR_SUCCESS,
            foreground="#FFFFFF",
            padding=[12, 6],
            borderwidth=0
        )
        self.style.map(
            "Success.TButton",
            background=[("active", "#15803D"), ("disabled", "#94A3B8")]
        )

        self.style.configure(
            "Blue.TButton",
            font=("Segoe UI Semibold", 10),
            background=COLOR_PRIMARY_BLUE,
            foreground="#FFFFFF",
            padding=[12, 6],
            borderwidth=0
        )
        self.style.map(
            "Blue.TButton",
            background=[("active", "#1D4ED8"), ("disabled", "#94A3B8")]
        )

        self.style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), background="#E2E8F0")
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=26)

    def _build_header(self):
        header_frame = tk.Frame(self, bg=COLOR_MAROON, height=72)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_container = tk.Frame(header_frame, bg=COLOR_MAROON)
        title_container.pack(side=tk.LEFT, padx=20, pady=10)

        lbl_univ = tk.Label(
            title_container,
            text="UNIVERSITY OF PERPETUAL HELP SYSTEM DALTA – MOLINO CAMPUS",
            font=("Segoe UI Bold", 13),
            bg=COLOR_MAROON,
            fg=COLOR_GOLD
        )
        lbl_univ.pack(anchor="w")

        lbl_dept = tk.Label(
            title_container,
            text="COLLEGE OF COMPUTER STUDIES • AI-POWERED OBE SYLLABUS GENERATOR MICROSERVICE",
            font=("Segoe UI Semibold", 9),
            bg=COLOR_MAROON,
            fg="#FFFFFF"
        )
        lbl_dept.pack(anchor="w")

        lbl_devs = tk.Label(
            title_container,
            text="Developers: Leinad Clark M. Dela Cruz & Nicole Anne G. Liwag | Instructor: Prof. Rob Malitao",
            font=("Segoe UI", 8),
            bg=COLOR_MAROON,
            fg="#FEF08A"
        )
        lbl_devs.pack(anchor="w")

        # Right status badge frame
        status_frame = tk.Frame(header_frame, bg=COLOR_MAROON)
        status_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        self.lbl_ollama_status = tk.Label(
            status_frame,
            text="Checking Ollama Service...",
            font=("Segoe UI Semibold", 9),
            bg=COLOR_MAROON,
            fg="#F8FAFC"
        )
        self.lbl_ollama_status.pack(side=tk.TOP, anchor="e")

        btn_refresh_ollama = tk.Button(
            status_frame,
            text="🔄 Recheck Ollama",
            font=("Segoe UI", 8),
            bg="#991B1E",
            fg="#FFFFFF",
            relief=tk.FLAT,
            command=self._check_ollama_daemon
        )
        btn_refresh_ollama.pack(side=tk.BOTTOM, anchor="e", pady=(3, 0))

        # Accent Gold Line
        accent_strip = tk.Frame(self, bg=COLOR_GOLD, height=4)
        accent_strip.pack(fill=tk.X, side=tk.TOP)

    def _build_main_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        self.tab_generator = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_database = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_qa = tk.Frame(self.notebook, bg=COLOR_BG)

        self.notebook.add(self.tab_generator, text="🎓 1. AI Syllabus Generator (Live Ollama)")
        self.notebook.add(self.tab_database, text="📚 2. Course Library & SQLite Database")
        self.notebook.add(self.tab_qa, text="🛠️ 3. System Health & QA Verification Suite")

        self._build_generator_tab()
        self._build_database_tab()
        self._build_qa_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event=None):
        try:
            sel_idx = self.notebook.index(self.notebook.select())
            if sel_idx == 1:
                self._load_database_courses()
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # TAB 1: AI SYLLABUS GENERATOR & EDITOR
    # -------------------------------------------------------------------------
    def _build_generator_tab(self):
        paned = tk.PanedWindow(self.tab_generator, orient=tk.HORIZONTAL, bg=COLOR_BG, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # LEFT PANE: Form Inputs & Generator Controls
        left_card = tk.Frame(paned, bg=COLOR_CARD, bd=1, relief=tk.SOLID, highlightbackground=COLOR_BORDER)
        paned.add(left_card, minsize=420, width=460)

        lbl_section = tk.Label(
            left_card,
            text="Course Parameters & Model Configuration",
            font=("Segoe UI Bold", 11),
            bg=COLOR_CARD,
            fg=COLOR_MAROON
        )
        lbl_section.pack(anchor="w", padx=16, pady=(14, 6))

        # Preset Selector
        tk.Label(left_card, text="Quick Course Presets:", font=("Segoe UI Semibold", 9), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(4, 2))
        preset_names = [f"{p['code']}: {p['title']}" for p in PRESETS] + ["Custom Academic Subject..."]
        self.cmb_presets = ttk.Combobox(left_card, values=preset_names, state="readonly", font=("Segoe UI", 9))
        self.cmb_presets.current(0)
        self.cmb_presets.pack(fill=tk.X, padx=16, pady=(0, 10))
        self.cmb_presets.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Form Fields
        field_frame = tk.Frame(left_card, bg=COLOR_CARD)
        field_frame.pack(fill=tk.X, padx=16)

        tk.Label(field_frame, text="Course Code:", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).grid(row=0, column=0, sticky="w", pady=3)
        self.ent_code = ttk.Entry(field_frame, font=("Segoe UI", 9))
        self.ent_code.grid(row=0, column=1, sticky="ew", pady=3, padx=(6, 0))

        tk.Label(field_frame, text="Course Title:", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).grid(row=1, column=0, sticky="w", pady=3)
        self.ent_title = ttk.Entry(field_frame, font=("Segoe UI", 9))
        self.ent_title.grid(row=1, column=1, sticky="ew", pady=3, padx=(6, 0))

        tk.Label(field_frame, text="Credit Units:", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).grid(row=2, column=0, sticky="w", pady=3)
        self.ent_units = ttk.Entry(field_frame, font=("Segoe UI", 9))
        self.ent_units.grid(row=2, column=1, sticky="ew", pady=3, padx=(6, 0))

        tk.Label(field_frame, text="Prerequisite(s):", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).grid(row=3, column=0, sticky="w", pady=3)
        self.ent_prereq = ttk.Entry(field_frame, font=("Segoe UI", 9))
        self.ent_prereq.grid(row=3, column=1, sticky="ew", pady=3, padx=(6, 0))

        field_frame.columnconfigure(1, weight=1)

        tk.Label(left_card, text="Course Catalog Description:", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(8, 2))
        self.txt_desc = scrolledtext.ScrolledText(left_card, height=4, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        self.txt_desc.pack(fill=tk.X, padx=16, pady=(0, 10))

        # Model Selector
        tk.Label(left_card, text="Local Ollama Model (localhost:11434):", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(4, 2))
        self.cmb_models = ttk.Combobox(left_card, values=["qwen2.5:1.5b", "qwen2.5:7b", "qwen2.5:latest"], state="readonly", font=("Segoe UI", 9))
        self.cmb_models.set("qwen2.5:1.5b")
        self.cmb_models.pack(fill=tk.X, padx=16, pady=(0, 10))

        # Generator Action Buttons
        self.btn_generate = ttk.Button(
            left_card,
            text="🚀 GENERATE SYLLABUS LIVE WITH OLLAMA",
            style="Primary.TButton",
            command=self._start_live_generation
        )
        self.btn_generate.pack(fill=tk.X, padx=16, pady=(8, 6))

        # Progress Bar & Ticker
        self.prog_bar = ttk.Progressbar(left_card, mode="indeterminate")
        self.prog_bar.pack(fill=tk.X, padx=16, pady=(4, 4))

        self.lbl_ticker = tk.Label(
            left_card,
            text="Ready to generate. Select course and click button above.",
            font=("Segoe UI", 8),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED,
            wraplength=420
        )
        self.lbl_ticker.pack(fill=tk.X, padx=16, pady=(0, 6))

        # Live Console Output Box
        tk.Label(left_card, text="Ollama Engine Log:", font=("Segoe UI Semibold", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 2))
        self.txt_log = scrolledtext.ScrolledText(left_card, height=8, font=("Consolas", 8), bg="#1E293B", fg="#F8FAFC")
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        # RIGHT PANE: Results Preview & Human-in-the-Loop CRUD
        right_card = tk.Frame(paned, bg=COLOR_CARD, bd=1, relief=tk.SOLID, highlightbackground=COLOR_BORDER)
        paned.add(right_card, minsize=540)

        # Overview Metrics Ribbon
        self.frame_metrics = tk.Frame(right_card, bg=COLOR_HIGHLIGHT, bd=1, relief=tk.SOLID)
        self.frame_metrics.pack(fill=tk.X, padx=14, pady=10)

        self.lbl_active_course = tk.Label(
            self.frame_metrics,
            text="Active Syllabus: No Course Loaded",
            font=("Segoe UI Bold", 10),
            bg=COLOR_HIGHLIGHT,
            fg=COLOR_MAROON
        )
        self.lbl_active_course.pack(side=tk.LEFT, padx=12, pady=8)

        self.lbl_stats = tk.Label(
            self.frame_metrics,
            text="CLOs: 0 | Weeks: 0 | Grading: 0%",
            font=("Segoe UI Semibold", 9),
            bg=COLOR_HIGHLIGHT,
            fg="#92400E"
        )
        self.lbl_stats.pack(side=tk.RIGHT, padx=12, pady=8)

        # Sub-Notebook for CLO Editor & 18-Week Schedule
        sub_nb = ttk.Notebook(right_card)
        sub_nb.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

        # SUB-TAB 1: Course Learning Outcomes (CLOs) Editor
        tab_clo = tk.Frame(sub_nb, bg=COLOR_CARD)
        sub_nb.add(tab_clo, text="📋 Course Learning Outcomes (CLOs) & CRUD Editor")

        tree_frame = tk.Frame(tab_clo, bg=COLOR_CARD)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        cols = ("co_number", "bloom_level", "mapped_po", "co_description")
        self.tree_clo = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse", height=6)
        self.tree_clo.heading("co_number", text="#")
        self.tree_clo.heading("bloom_level", text="Bloom's Level")
        self.tree_clo.heading("mapped_po", text="Mapped POs")
        self.tree_clo.heading("co_description", text="Outcome Description (Active Verb)")

        self.tree_clo.column("co_number", width=40, anchor="center")
        self.tree_clo.column("bloom_level", width=110, anchor="center")
        self.tree_clo.column("mapped_po", width=90, anchor="center")
        self.tree_clo.column("co_description", width=400, anchor="w")

        sb_clo = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_clo.yview)
        self.tree_clo.configure(yscrollcommand=sb_clo.set)
        self.tree_clo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_clo.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_clo.bind("<<TreeviewSelect>>", self._on_clo_select)

        # Faculty Edit Frame (Human-in-the-Loop CRUD)
        edit_box = tk.LabelFrame(
            tab_clo,
            text=" ✏️ Faculty Human-in-the-Loop Outcome Editor (CRUD) ",
            font=("Segoe UI Semibold", 9),
            bg=COLOR_CARD,
            fg=COLOR_MAROON,
            bd=1,
            relief=tk.SOLID
        )
        edit_box.pack(fill=tk.X, padx=8, pady=(4, 8))

        e_row1 = tk.Frame(edit_box, bg=COLOR_CARD)
        e_row1.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(e_row1, text="Selected CLO:", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).pack(side=tk.LEFT)
        self.lbl_selected_clo_num = tk.Label(e_row1, text="None", font=("Segoe UI Bold", 9), bg=COLOR_CARD, fg=COLOR_MAROON)
        self.lbl_selected_clo_num.pack(side=tk.LEFT, padx=(4, 16))

        tk.Label(e_row1, text="Bloom's Taxonomy Level:", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).pack(side=tk.LEFT)
        self.cmb_bloom = ttk.Combobox(
            e_row1,
            values=["Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"],
            state="readonly",
            width=14
        )
        self.cmb_bloom.set("Applying")
        self.cmb_bloom.pack(side=tk.LEFT, padx=6)

        e_row2 = tk.Frame(edit_box, bg=COLOR_CARD)
        e_row2.pack(fill=tk.X, padx=10, pady=(2, 6))

        tk.Label(e_row2, text="Description:", font=("Segoe UI Semibold", 9), bg=COLOR_CARD).pack(side=tk.LEFT, anchor="n")
        self.ent_clo_desc = ttk.Entry(e_row2, font=("Segoe UI", 9))
        self.ent_clo_desc.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        btn_apply_clo = ttk.Button(e_row2, text="Update CLO (CRUD)", style="Success.TButton", command=self._apply_clo_edit)
        btn_apply_clo.pack(side=tk.RIGHT)

        # SUB-TAB 2: 18-Week Learning Plan
        tab_sched = tk.Frame(sub_nb, bg=COLOR_CARD)
        sub_nb.add(tab_sched, text="📅 18-Week Learning Plan Matrix")

        sched_frame = tk.Frame(tab_sched, bg=COLOR_CARD)
        sched_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        w_cols = ("week", "period", "topic", "tla", "assessment", "aligned_co")
        self.tree_weeks = ttk.Treeview(sched_frame, columns=w_cols, show="headings", selectmode="browse")
        self.tree_weeks.heading("week", text="Wk")
        self.tree_weeks.heading("period", text="Period")
        self.tree_weeks.heading("topic", text="Curricular Topic")
        self.tree_weeks.heading("tla", text="Teaching/Learning Activity")
        self.tree_weeks.heading("assessment", text="Assessment Task")
        self.tree_weeks.heading("aligned_co", text="CLO")

        self.tree_weeks.column("week", width=40, anchor="center")
        self.tree_weeks.column("period", width=70, anchor="center")
        self.tree_weeks.column("topic", width=220, anchor="w")
        self.tree_weeks.column("tla", width=150, anchor="w")
        self.tree_weeks.column("assessment", width=140, anchor="w")
        self.tree_weeks.column("aligned_co", width=50, anchor="center")

        sb_weeks = ttk.Scrollbar(sched_frame, orient="vertical", command=self.tree_weeks.yview)
        self.tree_weeks.configure(yscrollcommand=sb_weeks.set)
        self.tree_weeks.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_weeks.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_weeks.bind("<<TreeviewSelect>>", self._on_week_select)

        # Week K/S/A Details Card
        self.lbl_week_ksa = tk.Label(
            tab_sched,
            text="Select a week above to view Knowledge (K), Skills (S), and Attitude (A) lesson outcomes.",
            font=("Segoe UI", 9),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED,
            justify=tk.LEFT,
            wraplength=620
        )
        self.lbl_week_ksa.pack(fill=tk.X, padx=12, pady=6)

        # ACTION TOOLBAR
        toolbar = tk.Frame(right_card, bg=COLOR_CARD)
        toolbar.pack(fill=tk.X, padx=14, pady=(6, 12))

        btn_save_db = ttk.Button(toolbar, text="💾 Save to SQLite", style="Primary.TButton", command=self._save_to_database)
        btn_save_db.pack(side=tk.LEFT, padx=(0, 6))

        btn_export_html = ttk.Button(toolbar, text="🌐 Compile & Open HTML Syllabus", style="Blue.TButton", command=self._export_and_open_html)
        btn_export_html.pack(side=tk.LEFT, padx=6)

        btn_export_json = ttk.Button(toolbar, text="📁 Export JSON", command=self._export_json_file)
        btn_export_json.pack(side=tk.LEFT, padx=6)

    # -------------------------------------------------------------------------
    # TAB 2: DATABASE & COURSE LIBRARY
    # -------------------------------------------------------------------------
    def _build_database_tab(self):
        frame_top = tk.Frame(self.tab_database, bg=COLOR_BG)
        frame_top.pack(fill=tk.X, padx=16, pady=12)

        lbl_container = tk.Frame(frame_top, bg=COLOR_BG)
        lbl_container.pack(side=tk.LEFT)

        lbl_lib = tk.Label(
            lbl_container,
            text="Institutional Syllabus Repository (obe_syllabus.db)",
            font=("Segoe UI Bold", 12),
            bg=COLOR_BG,
            fg=COLOR_MAROON
        )
        lbl_lib.pack(anchor="w")

        self.lbl_db_count = tk.Label(
            lbl_container,
            text="Querying database...",
            font=("Segoe UI", 9),
            bg=COLOR_BG,
            fg="#475569"
        )
        self.lbl_db_count.pack(anchor="w")

        btn_refresh_db = ttk.Button(frame_top, text="🔄 Refresh Library", command=self._load_database_courses)
        btn_refresh_db.pack(side=tk.RIGHT, padx=4)

        btn_seed_lib = ttk.Button(frame_top, text="📚 Ingest All Library Syllabi", command=self._seed_library_to_db)
        btn_seed_lib.pack(side=tk.RIGHT, padx=4)

        btn_import_json = ttk.Button(frame_top, text="📥 Ingest External JSON", command=self._import_json_to_db)
        btn_import_json.pack(side=tk.RIGHT, padx=4)

        # Table of Courses
        frame_tbl = tk.Frame(self.tab_database, bg=COLOR_CARD, bd=1, relief=tk.SOLID)
        frame_tbl.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))

        db_cols = ("code", "title", "units", "clos", "weeks", "updated")
        self.tree_db = ttk.Treeview(frame_tbl, columns=db_cols, show="headings", selectmode="browse")
        self.tree_db.heading("code", text="Course Code")
        self.tree_db.heading("title", text="Course Title")
        self.tree_db.heading("units", text="Credit Units")
        self.tree_db.heading("clos", text="Total CLOs")
        self.tree_db.heading("weeks", text="Total Weeks")
        self.tree_db.heading("updated", text="Last Updated")

        self.tree_db.column("code", width=110, anchor="center")
        self.tree_db.column("title", width=340, anchor="w")
        self.tree_db.column("units", width=180, anchor="center")
        self.tree_db.column("clos", width=90, anchor="center")
        self.tree_db.column("weeks", width=90, anchor="center")
        self.tree_db.column("updated", width=160, anchor="center")

        sb_db = ttk.Scrollbar(frame_tbl, orient="vertical", command=self.tree_db.yview)
        self.tree_db.configure(yscrollcommand=sb_db.set)
        self.tree_db.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_db.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_db.bind("<Double-1>", lambda e: self._load_selected_course_to_editor())

        # Bottom Actions
        bar_act = tk.Frame(self.tab_database, bg=COLOR_BG)
        bar_act.pack(fill=tk.X, padx=16, pady=(0, 14))

        btn_load_active = ttk.Button(bar_act, text="📂 Load Selected into Active Editor", style="Primary.TButton", command=self._load_selected_course_to_editor)
        btn_load_active.pack(side=tk.LEFT, padx=(0, 6))

        btn_export_sel = ttk.Button(bar_act, text="🌐 Export Selected to HTML", style="Blue.TButton", command=self._export_selected_from_db)
        btn_export_sel.pack(side=tk.LEFT, padx=6)

        btn_del = ttk.Button(bar_act, text="🗑️ Delete Course (Cascade)", command=self._delete_selected_course)
        btn_del.pack(side=tk.RIGHT)

        self._load_database_courses()

    # -------------------------------------------------------------------------
    # TAB 3: SYSTEM HEALTH & QA SUITE
    # -------------------------------------------------------------------------
    def _build_qa_tab(self):
        frame_qa = tk.Frame(self.tab_qa, bg=COLOR_BG)
        frame_qa.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        lbl_h = tk.Label(frame_qa, text="Quality Assurance & Institutional Accreditation Test Suite", font=("Segoe UI Bold", 12), bg=COLOR_BG, fg=COLOR_MAROON)
        lbl_h.pack(anchor="w", pady=(0, 10))

        # Status Cards Frame
        card_env = tk.Frame(frame_qa, bg=COLOR_CARD, bd=1, relief=tk.SOLID, padx=14, pady=12)
        card_env.pack(fill=tk.X, pady=(0, 12))

        tk.Label(card_env, text="Environment & Model Verification", font=("Segoe UI Bold", 10), bg=COLOR_CARD, fg=COLOR_MAROON).pack(anchor="w")
        self.lbl_qa_details = tk.Label(card_env, text="Querying local system environment...", font=("Segoe UI", 9), bg=COLOR_CARD, justify=tk.LEFT)
        self.lbl_qa_details.pack(anchor="w", pady=4)

        btn_run_tests = ttk.Button(card_env, text="🧪 Run 6-Point Automated Test Suite (test_system.py)", style="Primary.TButton", command=self._run_qa_tests)
        btn_run_tests.pack(anchor="w", pady=(6, 0))

        # Test Console
        tk.Label(frame_qa, text="Test Execution Report:", font=("Segoe UI Semibold", 9), bg=COLOR_BG).pack(anchor="w", pady=(4, 2))
        self.txt_qa_log = scrolledtext.ScrolledText(frame_qa, height=18, font=("Consolas", 9), bg="#0F172A", fg="#38BDF8")
        self.txt_qa_log.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # CONTROLLER METHODS & EVENT HANDLERS
    # -------------------------------------------------------------------------
    def _check_ollama_daemon(self):
        def worker():
            is_alive = llm_engine.is_ollama_running()
            if not is_alive:
                is_alive = llm_engine.ensure_ollama_running(timeout_seconds=4)

            models = llm_engine.get_available_ollama_models() if is_alive else []

            def update_ui():
                if is_alive:
                    self.lbl_ollama_status.config(
                        text=f"🟢 Ollama Online (Port 11434 • {len(models)} Models Detected)",
                        fg="#86EFAC"
                    )
                    if models:
                        self.cmb_models.config(values=models)
                        if "qwen2.5:1.5b" in models:
                            self.cmb_models.set("qwen2.5:1.5b")
                        else:
                            self.cmb_models.set(models[0])
                else:
                    self.lbl_ollama_status.config(
                        text="🔴 Ollama Offline (Fallback Generator Active)",
                        fg="#FCA5A5"
                    )

                self.lbl_qa_details.config(
                    text=f"Ollama Status: {'ONLINE' if is_alive else 'OFFLINE'}\n"
                         f"Endpoint: http://localhost:11434\n"
                         f"Installed Models: {', '.join(models) if models else 'None'}\n"
                         f"SQLite Database: {os.path.abspath(self.db_path)}"
                )

            self.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _on_preset_change(self, event=None):
        idx = self.cmb_presets.current()
        if 0 <= idx < len(PRESETS):
            self._load_preset_to_inputs(idx)
        else:
            # Custom selection
            self.ent_code.delete(0, tk.END)
            self.ent_title.delete(0, tk.END)
            self.ent_units.delete(0, tk.END)
            self.ent_units.insert(0, "3 Units (2 Units Lecture, 1 Unit Laboratory)")
            self.ent_prereq.delete(0, tk.END)
            self.txt_desc.delete("1.0", tk.END)

    def _load_preset_to_inputs(self, idx: int):
        p = PRESETS[idx]
        self.ent_code.delete(0, tk.END)
        self.ent_code.insert(0, p["code"])

        self.ent_title.delete(0, tk.END)
        self.ent_title.insert(0, p["title"])

        self.ent_units.delete(0, tk.END)
        self.ent_units.insert(0, p["units"])

        self.ent_prereq.delete(0, tk.END)
        self.ent_prereq.insert(0, p["prereq"])

        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", p["desc"])

    def _log(self, text: str):
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)

    def _start_live_generation(self):
        c_code = self.ent_code.get().strip() or "CS 311"
        c_title = self.ent_title.get().strip() or "Data Mining"
        c_units = self.ent_units.get().strip() or "3 Units (2 Units Lecture, 1 Unit Laboratory)"
        c_prereq = self.ent_prereq.get().strip() or "None"
        c_desc = self.txt_desc.get("1.0", tk.END).strip()
        model_name = self.cmb_models.get().strip() or "qwen2.5:1.5b"

        if not c_desc:
            c_desc = f"Comprehensive study of foundational principles and practical applications of {c_title}."

        self.btn_generate.config(state="disabled")
        self.prog_bar.start(10)
        self.lbl_ticker.config(text=f"Connecting to Ollama '{model_name}' on localhost:11434...", fg=COLOR_MAROON)
        self.txt_log.delete("1.0", tk.END)
        self._log(f"[START] Live generation initiated for {c_code}: {c_title}")
        self._log(f"[CONFIG] Model: {model_name} | Streaming: Enabled")

        def worker():
            t0 = time.time()
            token_tracker = [0]

            def progress_callback(count: int, chunk: str):
                token_tracker[0] = count
                msg = f"Generating live tokens via Ollama ({model_name})... {count:,} tokens produced"
                self.after(0, lambda: self.lbl_ticker.config(text=msg))

            try:
                syllabus = llm_engine.generate_syllabus_data(
                    course_title=c_title,
                    course_description=c_desc,
                    course_code=c_code,
                    prerequisites=c_prereq,
                    credit_units=c_units,
                    model_name=model_name,
                    allow_fallback=True,
                    progress_callback=progress_callback
                )

                elapsed = time.time() - t0
                # Auto-save sample_validated_output.json
                with open("sample_validated_output.json", "w", encoding="utf-8") as f:
                    f.write(syllabus.model_dump_json(indent=2))

                # Auto-ingest into SQLite
                db_manager.ingest_syllabus(syllabus, db_path=self.db_path)

                def on_success():
                    self.current_syllabus = syllabus
                    self.prog_bar.stop()
                    self.btn_generate.config(state="normal")
                    self.lbl_ticker.config(
                        text=f"✓ Live generation complete in {elapsed:.1f}s! Validated and saved to SQLite.",
                        fg=COLOR_SUCCESS
                    )
                    self._log(f"[SUCCESS] Pydantic Schema Validation Passed ({elapsed:.2f}s)!")
                    self._log(f"[STATS] Generated {len(syllabus.course_outcomes)} CLOs and {len(syllabus.weekly_schedule)} Weeks.")
                    self._render_active_syllabus(syllabus)
                    self._load_database_courses()
                    messagebox.showinfo(
                        "Generation Successful",
                        f"OBE Syllabus for '{syllabus.course_code}: {syllabus.course_title}' successfully generated live by Ollama!\n\n"
                        f"• Outcomes: {len(syllabus.course_outcomes)} Bloom CLOs\n"
                        f"• Term: 18 Weeks (W6 Prelim, W12 Midterm, W18 Final)\n"
                        f"• Persisted to: {self.db_path}"
                    )

                self.after(0, on_success)

            except Exception as err:
                def on_fail():
                    self.prog_bar.stop()
                    self.btn_generate.config(state="normal")
                    self.lbl_ticker.config(text=f"Error: {err}", fg="red")
                    self._log(f"[ERROR] Generation failed: {err}")
                    messagebox.showerror("Generation Error", f"Failed to generate syllabus: {err}")

                self.after(0, on_fail)

        threading.Thread(target=worker, daemon=True).start()

    def _render_active_syllabus(self, s: obe_schemas.CourseMetadataSchema):
        self.lbl_active_course.config(text=f"Active Syllabus: {s.course_code} - {s.course_title}")
        total_w = sum(g.percentage_weight for g in s.grading_breakdown)
        self.lbl_stats.config(text=f"CLOs: {len(s.course_outcomes)} | Weeks: {len(s.weekly_schedule)} | Grading: {total_w:.0f}%")

        # 1. Populate CLO Treeview
        for item in self.tree_clo.get_children():
            self.tree_clo.delete(item)
        for co in s.course_outcomes:
            self.tree_clo.insert("", tk.END, values=(
                f"CLO {co.co_number}",
                co.bloom_level,
                str(co.mapped_po),
                co.co_description
            ))

        # 2. Populate Weeks Treeview
        for item in self.tree_weeks.get_children():
            self.tree_weeks.delete(item)
        for w in s.weekly_schedule:
            self.tree_weeks.insert("", tk.END, values=(
                w.week_number,
                w.period,
                w.topic,
                w.teaching_learning_activity,
                w.assessment_task,
                str(w.aligned_co)
            ))

    def _on_clo_select(self, event=None):
        selected = self.tree_clo.selection()
        if not selected or not self.current_syllabus:
            return
        vals = self.tree_clo.item(selected[0], "values")
        if vals:
            co_num_str = vals[0].replace("CLO ", "").strip()
            self.lbl_selected_clo_num.config(text=f"CLO #{co_num_str}")
            self.cmb_bloom.set(vals[1])
            self.ent_clo_desc.delete(0, tk.END)
            self.ent_clo_desc.insert(0, vals[3])

    def _apply_clo_edit(self):
        if not self.current_syllabus:
            messagebox.showwarning("Warning", "No active syllabus loaded to edit.")
            return

        co_num_text = self.lbl_selected_clo_num.cget("text").replace("CLO #", "").strip()
        if not co_num_text.isdigit():
            messagebox.showwarning("Warning", "Please select a Course Outcome to modify.")
            return

        co_num = int(co_num_text)
        new_bloom = self.cmb_bloom.get()
        new_desc = self.ent_clo_desc.get().strip()

        if not new_desc or len(new_desc) < 5:
            messagebox.showerror("Error", "Description must be at least 5 characters.")
            return

        # Check taboo verbs
        first_w = new_desc.split()[0].lower().rstrip("s,.:;")
        if first_w in ["understand", "know", "learn"]:
            messagebox.showerror("Pydantic Schema Violation", f"Cannot use non-measurable verb '{first_w}'. Use active verbs like Implement, Analyze, Evaluate.")
            return

        # Update in memory
        target_co = next((co for co in self.current_syllabus.course_outcomes if co.co_number == co_num), None)
        if target_co:
            target_co.bloom_level = new_bloom
            target_co.co_description = new_desc

        # Update in SQLite
        db_manager.update_course_outcome(
            course_code=self.current_syllabus.course_code,
            co_number=co_num,
            new_description=new_desc,
            new_bloom_level=new_bloom,
            db_path=self.db_path
        )

        self._render_active_syllabus(self.current_syllabus)
        self._log(f"[CRUD] Faculty revised CLO #{co_num} -> [{new_bloom}] {new_desc}")
        messagebox.showinfo("Outcome Updated", f"CLO #{co_num} updated successfully in memory and SQLite!")

    def _on_week_select(self, event=None):
        selected = self.tree_weeks.selection()
        if not selected or not self.current_syllabus:
            return
        vals = self.tree_weeks.item(selected[0], "values")
        wn = int(vals[0])
        w_obj = next((w for w in self.current_syllabus.weekly_schedule if w.week_number == wn), None)
        if w_obj:
            ksa_lines = [f"Week {wn} ({w_obj.period}): {w_obj.topic}"]
            if w_obj.lesson_outcomes:
                for lo in w_obj.lesson_outcomes:
                    badge = "[K - Knowledge]" if lo.category == "K" else ("[S - Skills]" if lo.category == "S" else "[A - Attitude]")
                    ksa_lines.append(f"  • {badge}: {lo.description}")
            else:
                ksa_lines.append("  • Major Examination Week (No lecture LLOs)")
            self.lbl_week_ksa.config(text="\n".join(ksa_lines))

    def _save_to_database(self):
        if not self.current_syllabus:
            messagebox.showwarning("Warning", "No active syllabus to save.")
            return
        cid = db_manager.ingest_syllabus(self.current_syllabus, db_path=self.db_path)
        self._load_database_courses()
        messagebox.showinfo("Saved", f"Syllabus '{self.current_syllabus.course_code}' persisted into SQLite (Course ID: {cid})!")

    def _export_and_open_html(self):
        if not self.current_syllabus:
            messagebox.showwarning("Warning", "Please generate or load a syllabus first.")
            return
        # Ensure latest data in DB
        db_manager.ingest_syllabus(self.current_syllabus, db_path=self.db_path)
        html_path = export_engine.export_syllabus_html(self.current_syllabus.course_code, db_path=self.db_path, auto_open=False)
        self.last_exported_html = html_path
        abs_p = os.path.abspath(html_path)
        self._log(f"[EXPORT] Compiled official HTML syllabus: {abs_p}")
        webbrowser.open(f"file://{abs_p}")

    def _export_json_file(self):
        if not self.current_syllabus:
            messagebox.showwarning("Warning", "No active syllabus to export.")
            return
        initial_name = f"{self.current_syllabus.course_code.replace(' ', '_')}_Syllabus.json"
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile=initial_name, filetypes=[("JSON Files", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.current_syllabus.model_dump_json(indent=2))
            messagebox.showinfo("Exported", f"Saved JSON syllabus to:\n{path}")

    # -------------------------------------------------------------------------
    # DATABASE TAB METHODS
    # -------------------------------------------------------------------------
    def _load_database_courses(self):
        for item in self.tree_db.get_children():
            self.tree_db.delete(item)
        try:
            courses = db_manager.list_courses(self.db_path)
            for c in courses:
                self.tree_db.insert("", tk.END, values=(
                    c["course_code"],
                    c["course_title"],
                    c["credit_units"],
                    c["outcome_count"],
                    c["week_count"],
                    c.get("created_at") or c.get("updated_at", "Recently")
                ))
            if hasattr(self, "lbl_db_count"):
                self.lbl_db_count.config(text=f"Total Courses Stored: {len(courses)} (Double-click any row to view in Editor)")
            self._log(f"[DATABASE] Loaded {len(courses)} courses from SQLite repository.")
        except Exception as e:
            if hasattr(self, "lbl_db_count"):
                self.lbl_db_count.config(text=f"Error reading database: {e}")
            self._log(f"[DATABASE ERROR] Failed to load courses: {e}")
            print(f"Error loading courses: {e}")

    def _seed_library_to_db(self):
        if not os.path.exists("syllabi_library"):
            messagebox.showwarning("Warning", "Directory 'syllabi_library' not found.")
            return
        try:
            results = db_manager.batch_ingest_directory("syllabi_library", db_path=self.db_path)
            successes = [r for r in results if r.get("status") == "SUCCESS"]
            self._load_database_courses()
            messagebox.showinfo("Library Ingested", f"Successfully ingested {len(successes)} course syllabi from 'syllabi_library' into SQLite database!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to ingest library syllabi: {e}")

    def _load_selected_course_to_editor(self):
        selected = self.tree_db.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a course from the database table.")
            return
        vals = self.tree_db.item(selected[0], "values")
        c_code = vals[0]
        data = db_manager.get_course_by_code(c_code, db_path=self.db_path)
        if data:
            try:
                s = obe_schemas.CourseMetadataSchema.model_validate(data)
                self.current_syllabus = s
                self._render_active_syllabus(s)
                # Populate form
                self.ent_code.delete(0, tk.END)
                self.ent_code.insert(0, s.course_code)
                self.ent_title.delete(0, tk.END)
                self.ent_title.insert(0, s.course_title)
                self.ent_units.delete(0, tk.END)
                self.ent_units.insert(0, s.credit_units)
                self.ent_prereq.delete(0, tk.END)
                self.ent_prereq.insert(0, s.prerequisites)
                self.txt_desc.delete("1.0", tk.END)
                self.txt_desc.insert("1.0", s.course_description)
                self.notebook.select(0)
                messagebox.showinfo("Loaded", f"Loaded '{s.course_code}' into the editor!")
            except Exception as err:
                messagebox.showerror("Error", f"Failed to parse course: {err}")

    def _export_selected_from_db(self):
        selected = self.tree_db.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a course to export.")
            return
        c_code = self.tree_db.item(selected[0], "values")[0]
        html_path = export_engine.export_syllabus_html(c_code, db_path=self.db_path, auto_open=False)
        webbrowser.open(f"file://{os.path.abspath(html_path)}")

    def _delete_selected_course(self):
        selected = self.tree_db.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a course to delete.")
            return
        c_code = self.tree_db.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm Deletion", f"Permanently delete '{c_code}' and all child records (CASCADE)?"):
            db_manager.delete_course(c_code, db_path=self.db_path)
            self._load_database_courses()
            messagebox.showinfo("Deleted", f"Course '{c_code}' and relational children successfully deleted.")

    def _import_json_to_db(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            try:
                cid = db_manager.ingest_json_file(path, db_path=self.db_path)
                self._load_database_courses()
                messagebox.showinfo("Ingestion Successful", f"Ingested '{os.path.basename(path)}' into database (Course ID: {cid})!")
            except Exception as err:
                messagebox.showerror("Ingestion Error", f"Failed to ingest JSON: {err}")

    # -------------------------------------------------------------------------
    # QA SUITE METHODS
    # -------------------------------------------------------------------------
    def _run_qa_tests(self):
        self.txt_qa_log.delete("1.0", tk.END)
        self.txt_qa_log.insert(tk.END, "Starting 6-Point Automated Verification Suite...\n\n")

        def worker():
            import subprocess
            try:
                proc = subprocess.Popen(
                    [sys.executable, "test_system.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                for line in proc.stdout:
                    self.after(0, lambda l=line: self.txt_qa_log.insert(tk.END, l))
                proc.wait()
                if proc.returncode == 0:
                    self.after(0, lambda: self.txt_qa_log.insert(tk.END, "\n✓ ALL TESTS PASSED SUCCESSFULLY!\n"))
                else:
                    self.after(0, lambda: self.txt_qa_log.insert(tk.END, f"\n✗ Tests exited with error code {proc.returncode}\n"))
            except Exception as e:
                self.after(0, lambda: self.txt_qa_log.insert(tk.END, f"Execution failed: {e}\n"))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = OBESyllabusDesktopApp()
    app.mainloop()
