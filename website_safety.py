"""Offline URL risk indicators, not malware/phishing reputation or safety certification."""
from __future__ import annotations
import ipaddress
import unicodedata
from live_ssl import parse_target

def assess_target(raw: str) -> tuple[str, ...]:
    target = parse_target(raw)
    host=target.host
    notes=[]
    try:
        ipaddress.ip_address(host)
        notes.append('The target is an IP address, not a DNS hostname. Verify its ownership.')
    except ValueError:
        if 'xn--' in host.lower():
            notes.append('Punycode/IDN hostname: verify the intended spelling and organization.')
        if host.count('-') >= 5:
            notes.append('Many hyphens in hostname: review the spelling carefully.')
        if len(host)>100:
            notes.append('Unusually long hostname: verify the intended destination.')
    if target.port != 443:
        notes.append('Non-standard HTTPS port: verify that this endpoint is expected.')
    notes.append('No malware/phishing reputation lookup was performed. A valid TLS certificate does not establish website safety.')
    return tuple(notes)
