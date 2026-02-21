"""
HTML and plain-text formatter for the Niche AI Report Subscription system.
Converts raw report text into a styled HTML email template and a .txt version.
"""

import re
from datetime import datetime
from pathlib import Path

from config import NICHE_NAME

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

# Colors: dark navy header, light background, accent blue
COLOR_HEADER = "#0f172a"
COLOR_BACKGROUND = "#f8fafc"
COLOR_ACCENT = "#2563eb"


def _markdown_to_html(text: str) -> str:
    """Convert simple markdown-style headings, lists, and bold to HTML."""
    # Bold: **text** -> <strong>text</strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    lines = text.split("\n")
    out = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<br>")
            continue
        if re.match(r"^#+\s", stripped):
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(re.match(r"^#+", stripped).group())
            tag = f"h{min(level, 3)}"
            content = re.sub(r"^#+\s*", "", stripped)
            out.append(f"<{tag}>{content}</{tag}>")
        elif re.match(r"^[-*]\s", stripped) or re.match(r"^\d+\.\s", stripped):
            if not in_list:
                out.append("<ul>")
                in_list = True
            content = re.sub(r"^[-*]\s|^\d+\.\s", "", stripped)
            out.append(f"<li>{content}</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{stripped}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _wrap_email_html(body_html: str) -> str:
    """Wrap body in a mobile-responsive, styled email template."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{NICHE_NAME} — Weekly Report</title>
  <style>
    body {{ margin: 0; padding: 0; background: {COLOR_BACKGROUND}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #fff; }}
    .header {{ background: {COLOR_HEADER}; color: #fff; padding: 24px 20px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 1.5rem; font-weight: 600; }}
    .content {{ padding: 24px 20px; line-height: 1.6; color: #334155; }}
    .content h2 {{ color: {COLOR_HEADER}; font-size: 1.2rem; margin-top: 24px; margin-bottom: 8px; }}
    .content h3 {{ color: {COLOR_HEADER}; font-size: 1.05rem; margin-top: 16px; margin-bottom: 6px; }}
    .content p {{ margin: 0 0 12px; }}
    .content ul {{ margin: 8px 0; padding-left: 20px; }}
    .content a {{ color: {COLOR_ACCENT}; text-decoration: none; }}
    .content a:hover {{ text-decoration: underline; }}
    .footer {{ padding: 16px 20px; text-align: center; font-size: 0.85rem; color: #64748b; border-top: 1px solid #e2e8f0; }}
    .footer a {{ color: {COLOR_ACCENT}; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{NICHE_NAME}</h1>
    </div>
    <div class="content">
{body_html}
    </div>
    <div class="footer">
      <a href="#">Unsubscribe</a>
    </div>
  </div>
</body>
</html>"""


def format_and_save(raw_report: str) -> tuple[Path, Path]:
    """
    Convert raw report text to styled HTML and plain text, then save both.

    Creates reports/ if it doesn't exist. Files are named report_YYYY-MM-DD.html
    and report_YYYY-MM-DD.txt. HTML is mobile-responsive with header #0f172a,
    background #f8fafc, accent #2563eb, logo placeholder (NICHE_NAME), and
    footer with Unsubscribe placeholder.

    Returns:
        Tuple of (path_to_html_file, path_to_txt_file).
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    html_path = REPORTS_DIR / f"report_{date_str}.html"
    txt_path = REPORTS_DIR / f"report_{date_str}.txt"

    body_html = _markdown_to_html(raw_report)
    full_html = _wrap_email_html(body_html)
    html_path.write_text(full_html, encoding="utf-8")
    txt_path.write_text(raw_report, encoding="utf-8")

    return html_path, txt_path
