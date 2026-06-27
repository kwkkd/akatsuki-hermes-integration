import unittest
import json


class TestAkatsukiPayload(unittest.TestCase):
    def setUp(self):
        self.payload_module = __import__("tools.akatsuki_payload", fromlist=["akatsuki_payload"])

    def test_generate_python(self):
        code, ext = self.payload_module._generate("python", "10.0.0.1", 4444)
        self.assertIn("10.0.0.1", code)
        self.assertIn("4444", code)
        self.assertEqual(ext, ".py")

    def test_generate_bash(self):
        code, ext = self.payload_module._generate("bash", "10.0.0.1", 4444)
        self.assertIn("10.0.0.1", code)
        self.assertIn("4444", code)
        self.assertEqual(ext, ".sh")

    def test_generate_php(self):
        code, ext = self.payload_module._generate("php", "10.0.0.1", 8080)
        self.assertIn("10.0.0.1", code)
        self.assertIn("8080", code)
        self.assertEqual(ext, ".php")

    def test_akatsuki_payload_valid(self):
        result = self.payload_module.akatsuki_payload("python", "10.0.0.1", 4444)
        data = json.loads(result)
        self.assertEqual(data["payload_type"], "python")
        self.assertEqual(data["lhost"], "10.0.0.1")
        self.assertEqual(data["lport"], 4444)
        self.assertIn("code", data)

    def test_akatsuki_payload_invalid_type(self):
        result = self.payload_module.akatsuki_payload("invalid_type", "10.0.0.1", 4444)
        data = json.loads(result)
        self.assertIn("error", data)

    def test_akatsuki_payload_invalid_ip(self):
        result = self.payload_module.akatsuki_payload("python", "not_an_ip_or_domain!", 4444)
        data = json.loads(result)
        self.assertIn("error", data)

    def test_akatsuki_payload_invalid_port_too_high(self):
        result = self.payload_module.akatsuki_payload("python", "10.0.0.1", 99999)
        data = json.loads(result)
        self.assertIn("error", data)

    def test_akatsuki_payload_invalid_port_too_low(self):
        result = self.payload_module.akatsuki_payload("python", "10.0.0.1", 0)
        data = json.loads(result)
        self.assertIn("error", data)

    def test_akatsuki_payload_valid_domain(self):
        result = self.payload_module.akatsuki_payload("bash", "example.com", 443)
        data = json.loads(result)
        self.assertEqual(data["lhost"], "example.com")


if __name__ == "__main__":
    unittest.main()