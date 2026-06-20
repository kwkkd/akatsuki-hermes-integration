import json
import logging
import os
from datetime import datetime
from pathlib import Path

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


def generate_report(operation_data: dict = None) -> str:
    if operation_data is None:
        operation_data = {
            "target": "unknown",
            "objective": "penetration test",
            "findings": [],
            "final_report": "No data",
        }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("akatsuki_reports")
    report_dir.mkdir(exist_ok=True)
    fname = f"akatsuki_report_{timestamp}.md"
    fpath = report_dir / fname

    severity_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in operation_data.get("findings", []):
        sev = f.get("severity", "MEDIUM").upper()
        if sev in severity_count:
            severity_count[sev] += 1

    lines = [
        f"# AKATSUKI 침투 테스트 보고서",
        f"",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Target:** {operation_data.get('target', 'N/A')}",
        f"**Objective:** {operation_data.get('objective', 'N/A')}",
        f"**Operation ID:** {operation_data.get('operation_id', 'N/A')}",
        f"**Duration:** {operation_data.get('duration_seconds', 0)}s",
        f"",
        f"## Executive Summary",
        f"",
        f"AKATSUKI 팀의 {operation_data.get('target', 'unknown')} 대상 침투 테스트 결과 보고서입니다.",
        f"총 {sum(severity_count.values())}개의 취약점이 발견되었습니다.",
        f"",
        f"- Critical: {severity_count['CRITICAL']}",
        f"- High: {severity_count['HIGH']}",
        f"- Medium: {severity_count['MEDIUM']}",
        f"- Low: {severity_count['LOW']}",
        f"",
        f"## Findings",
        f"",
    ]
    for i, f in enumerate(operation_data.get("findings", []), 1):
        lines.append(f"### {i}. {f.get('agent', 'Unknown')}")
        lines.append(f"")
        lines.append(f"**Phase:** {f.get('phase', 'N/A')}")
        lines.append(f"")
        lines.append(f"{f.get('result', '')[:500]}")
        lines.append(f"")

    lines.append(f"## Final Assessment")
    lines.append(f"")
    lines.append(operation_data.get("final_report", "")[:2000])

    report_text = "\n".join(lines)
    fpath.write_text(report_text, encoding="utf-8")

    return str(fpath)


def generate_pdf(operation_data: dict = None) -> str:
    md_path = generate_report(operation_data)
    pdf_path = md_path.replace(".md", ".pdf")
    try:
        import markdown
        from weasyprint import HTML
        html = markdown.markdown(open(md_path, encoding="utf-8").read())
        HTML(string=html).write_pdf(pdf_path)
        return pdf_path
    except ImportError:
        return md_path


AKATSUKI_REPORT_SCHEMA = {
    "name": "akatsuki_report",
    "description": "AKATSUKI Report Generator — generate penetration test reports in Markdown (default) or PDF format from operation data including findings, severity counts, and final assessments.",
    "parameters": {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["markdown", "pdf"],
                "description": "Output format (default: markdown; pdf requires markdown + weasyprint)",
            },
            "target": {
                "type": "string",
                "description": "Target name/domain for the report",
            },
            "objective": {
                "type": "string",
                "description": "Operation objective description",
            },
            "operation_id": {
                "type": "string",
                "description": "Optional operation ID for tracking",
            },
            "duration_seconds": {
                "type": "number",
                "description": "Operation duration in seconds",
            },
            "findings_json": {
                "type": "string",
                "description": "JSON array of findings: [{\"agent\": \"...\", \"phase\": \"...\", \"result\": \"...\", \"severity\": \"CRITICAL|HIGH|MEDIUM|LOW\"}]",
            },
            "final_report": {
                "type": "string",
                "description": "Final assessment text",
            },
        },
        "required": ["target"],
    },
}


def akatsuki_report(format: str = "markdown", target: str = "", objective: str = "",
                    operation_id: str = "", duration_seconds: int = 0,
                    findings_json: str = "", final_report: str = "") -> str:
    findings = []
    if findings_json:
        try:
            findings = json.loads(findings_json)
        except json.JSONDecodeError:
            return tool_error("Invalid findings_json: must be valid JSON array")
    op_data = {
        "target": target,
        "objective": objective or f"Penetration test of {target}",
        "operation_id": operation_id or f"OP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "duration_seconds": duration_seconds,
        "findings": findings,
        "final_report": final_report or "AKATSUKI operation completed.",
    }
    if format == "pdf":
        path = generate_pdf(op_data)
    else:
        path = generate_report(op_data)
    return tool_result({
        "format": format,
        "path": path,
        "report_generated": True,
    })


def check_akatsuki_report_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_report",
    toolset="akatsuki",
    schema=AKATSUKI_REPORT_SCHEMA,
    handler=lambda args, **kw: akatsuki_report(
        format=args.get("format", "markdown"),
        target=args.get("target", ""),
        objective=args.get("objective", ""),
        operation_id=args.get("operation_id", ""),
        duration_seconds=args.get("duration_seconds", 0),
        findings_json=args.get("findings_json", ""),
        final_report=args.get("final_report", ""),
    ),
    check_fn=check_akatsuki_report_requirements,
    emoji="📋",
)
