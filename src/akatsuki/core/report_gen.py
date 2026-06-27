"""Report generator for producing markdown and PDF security assessment reports."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .logger import logger


@dataclass
class ReportSection:
    title: str
    content: str
    level: int = 1
    order: int = 0


@dataclass
class Report:
    title: str
    author: str = "AKATSUKI AI"
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sections: list[ReportSection] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    raw_data: dict = field(default_factory=dict)


class ReportGenerator:
    """Generates markdown and PDF reports from operation data."""

    def __init__(self):
        self._sections: list[ReportSection] = []

    def add_section(self, title: str, content: str, level: int = 1) -> "ReportGenerator":
        self._sections.append(ReportSection(title=title, content=content, level=level, order=len(self._sections)))
        return self

    def _dict_to_markdown(self, data: dict, indent: int = 0) -> str:
        lines = []
        for key, value in data.items():
            prefix = "  " * indent
            if isinstance(value, dict):
                lines.append(f"{prefix}- **{key}**:")
                lines.append(self._dict_to_markdown(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}- **{key}**:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._dict_to_markdown(item, indent + 1))
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}- **{key}**: {value}")
        return "\n".join(lines)

    async def generate_markdown(
        self,
        title: str,
        author: str = "AKATSUKI AI",
        sections: Optional[list[ReportSection]] = None,
        raw_data: Optional[dict] = None,
    ) -> str:
        all_sections = sections or self._sections
        lines = [
            f"# {title}",
            "",
            f"**Author:** {author}",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]
        if raw_data:
            lines.append("## Raw Data\n")
            lines.append(self._dict_to_markdown(raw_data))
            lines.append("")

        for i, section in enumerate(all_sections):
            heading = "#" * section.level
            lines.append(f"{heading} {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    async def generate_json(self, title: str, data: dict) -> str:
        report = {
            "title": title,
            "generated_by": "AKATSUKI AI",
            "generated_at": datetime.now().isoformat(),
            "data": data,
        }
        return json.dumps(report, indent=2, ensure_ascii=False, default=str)

    async def save_markdown(self, filepath: str, markdown: str):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown)
            logger.info(f"Report saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save report to {filepath}: {e}")
            raise

    async def generate_pdf(self, markdown_content: str, output_path: str) -> Optional[str]:
        try:
            from weasyprint import HTML
            html_content = f"<html><body><pre>{markdown_content}</pre></body></html>"
            HTML(string=html_content).write_pdf(output_path)
            logger.info(f"PDF report saved to {output_path}")
            return output_path
        except ImportError:
            logger.warning("weasyprint not installed. Install with: pip install weasyprint")
            try:
                import markdown
                import pdfkit
                html = markdown.markdown(markdown_content)
                pdfkit.from_string(html, output_path)
                logger.info(f"PDF report saved to {output_path}")
                return output_path
            except ImportError:
                logger.error("Neither weasyprint nor pdfkit are available for PDF generation")
                return None
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return None
