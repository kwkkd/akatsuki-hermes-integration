import unittest
from unittest.mock import patch, MagicMock
import json


class TestAkatsukiRecon(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.recon_module = __import__("tools.akatsuki_recon", fromlist=["akatsuki_recon"])

    def test_domain_recon_structure(self):
        with patch("tools.akatsuki_recon._resolve_dns", return_value={"A": ["1.2.3.4"]}):
            with patch("tools.akatsuki_recon._quick_whois", return_value={"registrar": "test"}):
                with patch("tools.akatsuki_recon._subdomain_enum", return_value=["www.example.com"]):
                    with patch("tools.akatsuki_recon._tech_detect", return_value={"server": "nginx"}):
                        result = self.recon_module.domain_recon("example.com")
                        self.assertIn("domain", result)
                        self.assertEqual(result["domain"], "example.com")
                        self.assertIn("dns", result)
                        self.assertIn("whois", result)
                        self.assertIn("subdomains", result)
                        self.assertIn("tech", result)

    def test_ip_recon(self):
        with patch("tools.akatsuki_recon._ptr_lookup", return_value="host.example.com"):
            with patch("tools.akatsuki_recon._hosting_detect", return_value="AWS"):
                result = self.recon_module.ip_recon("8.8.8.8")
                self.assertEqual(result["ip"], "8.8.8.8")
                self.assertEqual(result["ptr"], "host.example.com")

    def test_url_recon(self):
        result = self.recon_module.url_recon("https://example.com/path?q=1")
        self.assertEqual(result["hostname"], "example.com")
        self.assertEqual(result["path"], "/path")

    def test_email_recon(self):
        with patch("dns.resolver.resolve", return_value=[MagicMock(exchange="mx.example.com.")]):
            result = self.recon_module.email_recon("user@example.com")
            self.assertEqual(result["email"], "user@example.com")
            self.assertEqual(result["domain"], "example.com")

    @patch("tools.akatsuki_recon.re.match")
    def test_akatsuki_recon_ip_target(self, mock_match):
        mock_match.return_value = True
        with patch("tools.akatsuki_recon.ip_recon", return_value={"ip": "1.2.3.4", "ptr": "", "hosting": ""}):
            result = self.recon_module.akatsuki_recon("1.2.3.4")
            data = json.loads(result)
            self.assertEqual(data["ip"], "1.2.3.4")


if __name__ == "__main__":
    unittest.main()