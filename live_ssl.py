"""Read-only TLS certificate inspection. No HTTP requests, cookies or page content.

Each inspection resolves the host afresh and uses newly-created TLS contexts/sockets.
The observed certificate may still vary across CDNs, load balancers or DNS caches.
"""
from __future__ import annotations

import ipaddress
import re
import socket
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import ExtensionOID, NameOID

import core

MAX_TARGET_LENGTH = 2048
SOCKET_TIMEOUT = 4.0
MAX_CERT_BYTES = 128 * 1024
MAX_IP_RESULTS = 32


@dataclass(frozen=True)
class Target:
    host: str
    port: int
    path_ignored: bool = False


@dataclass(frozen=True)
class LiveResult:
    target: Target
    checked_at: datetime
    connected_ip: str
    resolved_ips: tuple[str, ...]
    cnames: tuple[str, ...]
    certificate: x509.Certificate
    sans: tuple[str, ...]
    issuer: str
    subject_cn: str
    certificate_type: str
    fingerprint: str
    not_before: datetime
    expires_at: datetime
    hostname_ok: bool
    trust_ok: bool
    trust_message: str
    tls_version: str
    cipher: str
    remarks: tuple[str, ...]

    @property
    def remaining_days(self) -> int:
        return int((self.expires_at - self.checked_at).total_seconds() // 86400)

    @property
    def issues(self) -> tuple[str, ...]:
        issues = []
        if self.not_before > self.checked_at:
            issues.append('Certificate is not yet valid.')
        if self.expires_at <= self.checked_at:
            issues.append('Certificate has expired.')
        if not self.hostname_ok:
            issues.append('Certificate does not cover the requested hostname.')
        if not self.trust_ok:
            issues.append('Certificate trust validation failed: ' + self.trust_message)
        return tuple(issues)

    @property
    def health(self) -> str:
        if self.issues or self.remaining_days <= 15:
            return 'critical'
        if self.remaining_days <= 30:
            return 'warning'
        return 'valid'


def parse_target(raw: str) -> Target:
    raw = raw.strip()
    if not raw or len(raw) > MAX_TARGET_LENGTH or re.search(r'[\x00-\x1f\x7f\\]', raw):
        raise ValueError('Enter a valid website hostname or HTTPS URL (max 2048 characters).')
    if not re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://', raw):
        raw = 'https://' + raw
    try:
        parsed = urlsplit(raw)
        if parsed.scheme.lower() != 'https' or parsed.username or parsed.password:
            raise ValueError('Only HTTPS targets without embedded credentials are permitted.')
        if parsed.query or parsed.fragment:
            raise ValueError('Remove URL query strings and fragments; only the TLS hostname and port are inspected.')
        host = parsed.hostname
        if not host:
            raise ValueError('Enter a hostname.')
        port = parsed.port if parsed.port is not None else 443
        if not 1 <= port <= 65535:
            raise ValueError('Invalid TCP port.')
        try:
            host = str(ipaddress.ip_address(host))
        except ValueError:
            host = core.normalize_dns(host)
        if host.startswith('*.'):
            raise ValueError('Use an actual host, e.g. www.example.com, not a wildcard pattern.')
        return Target(host, port, bool(parsed.path and parsed.path != '/'))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('Invalid HTTPS URL or port.') from exc


def lookup_dns(target: Target) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Fresh DNS queries, with OS resolver fallback for local split-horizon/hosts mappings."""
    try:
        ipaddress.ip_address(target.host)
        return (target.host,), ()
    except ValueError:
        pass
    addresses: list[str] = []
    cnames: list[str] = []
    try:
        import dns.resolver
        import dns.exception
        resolver = dns.resolver.Resolver(configure=True)
        resolver.timeout = 2.0
        resolver.lifetime = 3.0
        for typ in ('A', 'AAAA', 'CNAME'):
            try:
                answers = resolver.resolve(target.host, typ, raise_on_no_answer=False, lifetime=3.0)
                for answer in answers or ():
                    if typ == 'CNAME':
                        value = str(answer.target).rstrip('.')
                        if value not in cnames:
                            cnames.append(value)
                    else:
                        value = str(answer.address)
                        if value not in addresses:
                            addresses.append(value)
            except (dns.exception.DNSException, OSError):
                pass
    except (ImportError, OSError):
        pass
    # Local DNS and hosts entries are authoritative for the client's actual connection.
    try:
        entries = socket.getaddrinfo(target.host, target.port, type=socket.SOCK_STREAM)
        system_ips = list(dict.fromkeys(item[4][0] for item in entries))
        if system_ips:
            addresses = system_ips
    except (OSError, ValueError):
        pass
    if not addresses:
        raise ValueError('DNS lookup failed: no A/AAAA address could be resolved.')
    return tuple(addresses[:MAX_IP_RESULTS]), tuple(cnames[:MAX_IP_RESULTS])


def _tls_connect(ip: str, target: Target, *, verify: bool):
    context = ssl.create_default_context() if verify else ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.options |= ssl.OP_NO_COMPRESSION
    if hasattr(context, 'keylog_filename'):
        context.keylog_filename = None  # Do not write TLS session secrets to SSLKEYLOGFILE.
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    elif hasattr(context, 'hostname_checks_common_name'):
        context.hostname_checks_common_name = False
    # Never share contexts or SSL sessions between checks.
    with socket.create_connection((ip, target.port), timeout=SOCKET_TIMEOUT) as sock:
        sock.settimeout(SOCKET_TIMEOUT)
        with context.wrap_socket(sock, server_hostname=target.host) as tls:
            return tls.getpeercert(binary_form=True), tls.version() or 'Unknown', (tls.cipher() or ('Unknown',))[0]


def _common_name(name: x509.Name) -> str:
    attrs = name.get_attributes_for_oid(NameOID.COMMON_NAME)
    return str(attrs[0].value) if attrs else '(none)'


def certificate_type(sans: tuple[str, ...]) -> str:
    wild = any(name.startswith('*.') for name in sans)
    if wild and any(not name.startswith('*.') for name in sans):
        return 'Mixed (Wildcard + SAN)'
    if wild:
        return 'Wildcard'
    if len(sans) > 1:
        return 'Multi-Domain (SAN)'
    return 'Single-Domain' if sans else 'No DNS SAN'


def _hostname_match(cert: x509.Certificate, host: str) -> bool:
    try:
        san = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value
    except x509.ExtensionNotFound:
        return False  # Modern browser matching relies on SAN, not CN alone.
    try:
        wanted = ipaddress.ip_address(host)
    except ValueError:
        return any(core.dns_covers(n, host) for n in san.get_values_for_type(x509.DNSName))
    return wanted in san.get_values_for_type(x509.IPAddress)


def inspect(raw: str) -> LiveResult:
    target = parse_target(raw)
    addresses, cnames = lookup_dns(target)
    failures = []
    der = None
    connected = ''
    tls_version = ''
    cipher = ''
    for addr in addresses[:3]:
        try:
            der, tls_version, cipher = _tls_connect(addr, target, verify=False)
            connected = addr
            break
        except (OSError, ssl.SSLError) as exc:
            failures.append(f'{addr}: {type(exc).__name__}: {exc}')
    if not der:
        raise ValueError('TLS handshake failed. ' + '; '.join(failures)[:450])
    if len(der) > MAX_CERT_BYTES:
        raise ValueError('Server certificate exceeds maximum allowed size.')
    cert = x509.load_der_x509_certificate(der)
    now = datetime.now(timezone.utc).astimezone()
    san_values = tuple(core.get_sans(cert))
    trust = False
    trust_message = ''
    try:
        verified_der, _verified_tls, _verified_cipher = _tls_connect(connected, target, verify=True)
        if verified_der != der:
            trust_message = 'Different certificates were served on the separate verification handshake; retry inspection.'
        else:
            trust = True
            trust_message = 'Trusted by the operating system / Python trust configuration'
    except (OSError, ssl.SSLError) as exc:
        trust_message = str(exc)[:260] or type(exc).__name__
    remarks = []
    if target.path_ignored:
        remarks.append('URL path is not fetched; only the TLS endpoint is inspected.')
    if len(addresses) > 1:
        remarks.append('Multiple IP addresses: this result represents only the connected endpoint; other nodes may differ.')
    try:
        if ipaddress.ip_address(connected).is_private or ipaddress.ip_address(connected).is_loopback:
            remarks.append('Connected to a private/local IP; trust can differ from public browsers.')
    except ValueError:
        pass
    return LiveResult(
        target=target, checked_at=now, connected_ip=connected, resolved_ips=addresses, cnames=cnames,
        certificate=cert, sans=san_values, issuer=_common_name(cert.issuer), subject_cn=_common_name(cert.subject),
        certificate_type=certificate_type(san_values), fingerprint=cert.fingerprint(hashes.SHA256()).hex(':').upper(),
        not_before=cert.not_valid_before_utc, expires_at=cert.not_valid_after_utc,
        hostname_ok=_hostname_match(cert, target.host), trust_ok=trust, trust_message=trust_message,
        tls_version=tls_version, cipher=cipher, remarks=tuple(remarks),
    )


def compare_sans(current: tuple[str, ...], proposed: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return (retained/covered, added, removed/uncovered) using wildcard coverage.

    A wildcard in *current* cannot be retained by a finite list of explicit names.
    """
    current = tuple(dict.fromkeys(x.lower() for x in current))
    proposed = tuple(dict.fromkeys(x.lower() for x in proposed))
    retained = tuple(x for x in current if any(core.dns_covers(p, x) for p in proposed))
    removed = tuple(x for x in current if x not in retained)
    added = tuple(x for x in proposed if not any(core.dns_covers(c, x) for c in current))
    return retained, added, removed
