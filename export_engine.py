"""
Export Engine Module: Jinja2 Compilation and Institutional Document Assembly.
Queries normalized SQLite records and renders the official browser-ready HTML/PDF syllabus.
"""

import os
import sys
import base64
import webbrowser
from jinja2 import Environment, FileSystemLoader, select_autoescape

import db_manager

DEFAULT_TEMPLATE_DIR = "templates"
DEFAULT_TEMPLATE_FILE = "uphsd_ccs_template.html"
DEFAULT_EXPORTS_DIR = "exports"
DEFAULT_LOGO_PATH = "assets/UPHSD-logo-yellow.png"
DEFAULT_HEADER_BANNER_PATH = "assets/uphsd_molino_header.png"


def _get_logo_base64(logo_path: str = DEFAULT_LOGO_PATH) -> str:
    """
    Encodes the institutional logo as base64 string for zero-dependency portability.
    """
    if not os.path.isabs(logo_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, logo_path)

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def export_syllabus_html(
    course_code: str,
    output_dir: str = DEFAULT_EXPORTS_DIR,
    template_dir: str = DEFAULT_TEMPLATE_DIR,
    template_file: str = DEFAULT_TEMPLATE_FILE,
    db_path: str = db_manager.DEFAULT_DB_PATH,
    auto_open: bool = False
) -> str:
    """
    Queries course from SQLite, compiles with Jinja2, and saves browser-ready HTML.
    """
    # 1. Fetch relational course data
    course_data = db_manager.get_course_by_code(course_code, db_path=db_path)
    if not course_data:
        available = [c["course_code"] for c in db_manager.list_courses(db_path=db_path)]
        raise ValueError(
            f"Course '{course_code}' not found in database '{db_path}'. "
            f"Available courses: {available}"
        )

    # 2. Setup Jinja2 Template Environment
    base_dir = os.path.dirname(os.path.abspath(__file__))
    t_dir = template_dir if os.path.isabs(template_dir) else os.path.join(base_dir, template_dir)

    env = Environment(
        loader=FileSystemLoader(t_dir),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template(template_file)

    # 3. Embed Logo & Molino Header Banner
    logo_base64 = _get_logo_base64(DEFAULT_LOGO_PATH)
    header_banner_base64 = _get_logo_base64(DEFAULT_HEADER_BANNER_PATH)

    # 4. Render Document
    rendered_html = template.render(
        course=course_data,
        logo_base64=logo_base64,
        header_banner_base64=header_banner_base64
    )

    # 5. Write to output file
    out_dir = output_dir if os.path.isabs(output_dir) else os.path.join(base_dir, output_dir)
    os.makedirs(out_dir, exist_ok=True)

    clean_code = course_code.replace(" ", "_").replace("/", "_")
    out_file = os.path.join(out_dir, f"{clean_code}_Syllabus.html")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"[Export Engine] [OK] Successfully generated official syllabus: {out_file}")

    if auto_open:
        webbrowser.open(f"file://{os.path.abspath(out_file)}")

    return out_file


if __name__ == "__main__":
    target_code = sys.argv[1] if len(sys.argv) > 1 else "CS 211"
    print(f"[Export Engine] Compiling syllabus for course '{target_code}'...")
    try:
        exported_path = export_syllabus_html(target_code, auto_open=False)
        print(f"[Export Engine] Browser-ready document available at:\n  {exported_path}")
    except Exception as e:
        print(f"[Export Engine] Error: {e}")
