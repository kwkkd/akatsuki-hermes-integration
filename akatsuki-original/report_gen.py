import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from akatsuki_config import CONFIG

class ReportGenerator:
    def __init__(self):
        self.report_dir = CONFIG.paths.evaluations
        os.makedirs(self.report_dir, exist_ok=True)

    def generate(self, operation_data: dict = None) -> str:
        if operation_data is None:
            operation_data = {"target": "unknown", "objective": "penetration test",
                              "findings": [], "final_report": "No data"}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"akatsuki_report_{timestamp}.md"
        fpath = os.path.join(self.report_dir, fname)

        severity_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in operation_data.get("findings", []):
            sev = f.get("severity", "MEDIUM").upper()
            if sev in severity_count: severity_count[sev] += 1

        report = [
            f"# AKATSUKI 침투 테스트 보고서",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Target:** {operation_data.get('target', 'N/A')}",
            f"**Objective:** {operation_data.get('objective', 'N/A')}",
            f"**Operation ID:** {operation_data.get('operation_id', 'N/A')}",
            f"**Duration:** {operation_data.get('duration_seconds', 0)}s",
            f"",
            f"## Executive Summary",
            f"AKATSUKI 팀의 {operation_data.get('target', 'unknown')} 대상 침투 테스트 결과 보고서입니다.",
            f"총 {sum(severity_count.values())}개의 취약점이 발견되었습니다.",
            f"- Critical: {severity_count['CRITICAL']}",
            f"- High: {severity_count['HIGH']}",
            f"- Medium: {severity_count['MEDIUM']}",
            f"- Low: {severity_count['LOW']}",
            f"",
            f"## Findings",
        ]
        for i, f in enumerate(operation_data.get("findings", []), 1):
            report.append(f"### {i}. {f.get('agent', 'Unknown')}")
            report.append(f"**Phase:** {f.get('phase', 'N/A')}")
            report.append(f"**Detail:** {f.get('result', '')[:500]}")
            report.append("")

        report.append(f"## Final Assessment")
        report.append(operation_data.get("final_report", "")[:2000])

        with open(fpath, "w", encoding="utf-8") as f:
            f.write("\n".join(report))

        return fpath

    def generate_pdf(self, operation_data: dict = None) -> str:
        md_path = self.generate(operation_data)
        pdf_path = md_path.replace(".md", ".pdf")
        try:
            import markdown
            from weasyprint import HTML
            html = markdown.markdown(open(md_path, encoding="utf-8").read())
            HTML(string=html).write_pdf(pdf_path)
            return pdf_path
        except ImportError:
            return md_path

if __name__ == "__main__":
    rg = ReportGenerator()
    test_data = {
        "target": "testcorp.com", "objective": "Full penetration test",
        "operation_id": "OP-1234", "duration_seconds": 3600,
        "findings": [
            {"agent": "initial_access", "phase": "recon", "result": "Open ports: 80,443,8080", "severity": "MEDIUM"},
            {"agent": "rnd_exploit", "phase": "exploit", "result": "SQL Injection found on /login", "severity": "CRITICAL"},
        ],
        "final_report": "The target has critical vulnerabilities requiring immediate remediation."
    }
    path = rg.generate_pdf(test_data)
    print(f"Report: {path}")
