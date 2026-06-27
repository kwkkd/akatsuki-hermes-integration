import unittest
import json


class TestAkatsukiEvasion(unittest.TestCase):
    def setUp(self):
        self.evasion_module = __import__("tools.akatsuki_evasion", fromlist=["akatsuki_evasion"])

    def test_amsi_bypass_powershell(self):
        result = self.evasion_module.amsi_bypass("powershell")
        self.assertEqual(result["language"], "powershell")
        self.assertIn("code", result)
        self.assertGreater(len(result["code"]), 10)

    def test_amsi_bypass_csharp(self):
        result = self.evasion_module.amsi_bypass("csharp")
        self.assertEqual(result["language"], "csharp")
        self.assertIn("code", result)

    def test_amsi_bypass_unsupported(self):
        result = self.evasion_module.amsi_bypass("ruby")
        self.assertIn("error", result)

    def test_base64_encode_decode(self):
        original = "test payload data"
        encoded = self.evasion_module.base64_encode(original)
        decoded = self.evasion_module.base64_decode(encoded)
        self.assertEqual(decoded, original)

    def test_xor_obfuscate(self):
        data = "hello"
        result = self.evasion_module.xor_obfuscate(data, 0x42)
        self.assertNotEqual(result, data)
        restored = self.evasion_module.xor_obfuscate(result, 0x42)
        self.assertEqual(restored, data)

    def test_split_string(self):
        data = "abcdefghijklmnop"
        result = self.evasion_module.split_string(data, parts=4)
        self.assertIn('"abcd"', result)
        self.assertIn('"efgh"', result)

    def test_evade_sandbox(self):
        payload = "evil_code()"
        wrapped = self.evasion_module.evade_sandbox(payload, "powershell")
        self.assertIn(payload, wrapped)
        self.assertIn("Start-Sleep", wrapped)

    def test_akatsuki_evasion_amsi(self):
        result = self.evasion_module.akatsuki_evasion("amsi_bypass", "powershell")
        data = json.loads(result)
        self.assertEqual(data["language"], "powershell")

    def test_akatsuki_evasion_obfuscate_base64(self):
        result = self.evasion_module.akatsuki_evasion("obfuscate", payload="test", obfuscation_method="base64")
        data = json.loads(result)
        self.assertEqual(data["method"], "base64")

    def test_akatsuki_evasion_sandbox_wrap(self):
        result = self.evasion_module.akatsuki_evasion("sandbox_wrap", payload="evil()")
        data = json.loads(result)
        self.assertEqual(data["method"], "sandbox_evasion")

    def test_akatsuki_evasion_unknown_action(self):
        result = self.evasion_module.akatsuki_evasion("invalid_action")
        data = json.loads(result)
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()