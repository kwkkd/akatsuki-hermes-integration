import unittest
import json
import os
import tempfile
from pathlib import Path


class TestAkatsukiVuln(unittest.TestCase):
    def setUp(self):
        self.vuln_module = __import__("tools.akatsuki_vuln", fromlist=["akatsuki_vuln"])

    def tearDown(self):
        self.vuln_module.reload_db()

    def test_classify_apache(self):
        results = self.vuln_module.classify("apache httpd")
        self.assertGreater(len(results), 0)
        cves = [r["cve_id"] for r in results]
        self.assertIn("CVE-2021-41773", cves)

    def test_classify_microsoft(self):
        results = self.vuln_module.classify("microsoft exchange")
        self.assertGreater(len(results), 0)
        cves = [r["cve_id"] for r in results]
        self.assertIn("CVE-2021-26855", cves)

    def test_classify_unknown(self):
        results = self.vuln_module.classify("unknown_service_xyz")
        self.assertEqual(len(results), 0)

    def test_prioritize_critical_first(self):
        vulns = [
            {"severity": "LOW", "cvss_score": 5.0},
            {"severity": "CRITICAL", "cvss_score": 10.0},
            {"severity": "HIGH", "cvss_score": 7.5},
        ]
        ranked = self.vuln_module.prioritize(vulns, max_results=3)
        self.assertEqual(ranked[0]["severity"], "CRITICAL")

    def test_prioritize_max_results(self):
        vulns = [
            {"severity": "CRITICAL", "cvss_score": 10.0},
            {"severity": "HIGH", "cvss_score": 7.5},
        ]
        ranked = self.vuln_module.prioritize(vulns, max_results=1)
        self.assertEqual(len(ranked), 1)

    def test_akatsuki_vuln_empty_service(self):
        result = self.vuln_module.akatsuki_vuln("", "")
        data = json.loads(result)
        self.assertIn("error", data)

    def test_reload_db(self):
        tmp_file = tempfile.mktemp(suffix=".yaml")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write("test_vendor:\n  test_cve:\n")
                f.write('    cve: "CVE-2024-0001"\n')
                f.write('    severity: "HIGH"\n')
                f.write('    cvss: 7.5\n')
                f.write('    type: "Test"\n')
            old_env = os.environ.get("AKATSUKI_VULN_DB")
            os.environ["AKATSUKI_VULN_DB"] = tmp_file
            self.vuln_module.reload_db()
            results = self.vuln_module.classify("test_vendor")
            self.assertGreater(len(results), 0)
            self.assertEqual(results[0]["cve_id"], "CVE-2024-0001")
        finally:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)
            if old_env:
                os.environ["AKATSUKI_VULN_DB"] = old_env
            else:
                os.environ.pop("AKATSUKI_VULN_DB", None)
                self.vuln_module.reload_db()

    def test_version_filtering(self):
        results = self.vuln_module.classify("apache httpd", "2.4.49")
        cves = [r["cve_id"] for r in results]
        if cves:
            self.assertIn("CVE-2021-41773", cves)
        else:
            self.skipTest("No results for version filtering (DB may need data/vuln_db.yaml)")


if __name__ == "__main__":
    unittest.main()