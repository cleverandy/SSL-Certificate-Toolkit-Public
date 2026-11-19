"""Local-only certificate and private-key operations for SSL Certificate Toolkit.

Requires cryptography >= 45.0. No network calls or external OpenSSL process.
"""
from __future__ import annotations

import re
import os
import shlex
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, ed448, padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtensionOID, NameOID

DEFAULT_SUBJECT = {
    "C": "US",
    "ST": "",
    "L": "",
    "O": "",
    "OU": "",
}
OID_MAP = {"C": NameOID.COUNTRY_NAME, "ST": NameOID.STATE_OR_PROVINCE_NAME,
           "L": NameOID.LOCALITY_NAME, "O": NameOID.ORGANIZATION_NAME,
           "OU": NameOID.ORGANIZATIONAL_UNIT_NAME, "CN": NameOID.COMMON_NAME}
DOMAIN_PATTERN = re.compile(r"^(?:\*\.)?(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.I)
PEM_CERT_PATTERN = re.compile(rb"-----BEGIN CERTIFICATE-----\s*.*?-----END CERTIFICATE-----", re.S)


def normalize_dns(value: str) -> str:
    value = value.strip().rstrip(".").lower()
    wildcard = value.startswith("*.")
    name = value[2:] if wildcard else value
    try:
        ascii_name = name.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeEncodeError) as exc:
        raise ValueError(f"Invalid DNS name: {value!r}") from exc
    result = ("*." if wildcard else "") + ascii_name
    if not DOMAIN_PATTERN.fullmatch(result):
        raise ValueError(f"Invalid DNS name: {value!r}")
    return result


def san_names(primary: str, extra: Sequence[str] = (), auto_www: bool = True) -> list[str]:
    primary = normalize_dns(primary)
    result = [primary]
    if auto_www:
        other = primary[2:] if primary.startswith("*.") else (primary[4:] if primary.startswith("www.") else "www." + primary)
        if other not in result:
            result.append(other)
    for x in extra:
        if x.strip():
            name = normalize_dns(x)
            if name not in result:
                result.append(name)
    return result


def domain_label(value: str) -> str:
    """Directory and file prefix: first meaningful label + YYYYMM, never name the file YYYYMMDD."""
    host = normalize_dns(value)
    host = host.removeprefix("*.").removeprefix("www.")
    label = re.sub(r"[^A-Za-z0-9_-]", "_", host.split(".", 1)[0])
    return label or "certificate"


def output_stem(primary: str, now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"{domain_label(primary)}_{now:%Y%m}"


def desktop_path() -> Path:
    """Use the user's Desktop, including redirected OneDrive Desktop when known."""
    if os.name == "nt":
        # Query known-folder redirection, with standard fallback when unavailable.
        try:
            import ctypes
            from ctypes import wintypes
            from uuid import UUID
            guid = UUID("B4BFCC3A-DB2C-424C-B029-7FE99A87C641")
            raw = guid.bytes_le
            class GUID(ctypes.Structure):
                _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                            ("Data3", wintypes.WORD), ("Data4", ctypes.c_byte * 8)]
            g = GUID.from_buffer_copy(raw)
            path_ptr = ctypes.c_void_p()
            shell_func = ctypes.windll.shell32.SHGetKnownFolderPath
            shell_func.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p)]
            shell_func.restype = ctypes.c_long
            hr = shell_func(ctypes.byref(g), 0, None, ctypes.byref(path_ptr))
            if hr == 0 and path_ptr.value:
                result = Path(ctypes.cast(path_ptr, ctypes.c_wchar_p).value)
                free = ctypes.windll.ole32.CoTaskMemFree
                free.argtypes = [ctypes.c_void_p]
                free.restype = None
                free(path_ptr)
                return result
        except Exception:
            pass
    return Path.home() / "Desktop"


def output_directory(base: str | Path, primary: str, now: datetime | None = None) -> Path:
    return Path(base).expanduser() / output_stem(primary, now)


def make_subject(fields: dict[str, str], primary: str) -> x509.Name:
    country = fields.get("C", "").strip().upper()
    if not re.fullmatch("[A-Z]{2}", country):
        raise ValueError("Country must be a two-letter code such as US.")
    attributes = [x509.NameAttribute(NameOID.COUNTRY_NAME, country)]
    for name in ("ST", "L", "O", "OU"):
        val = fields.get(name, "").strip()
        if val:
            attributes.append(x509.NameAttribute(OID_MAP[name], val))
    attributes.append(x509.NameAttribute(NameOID.COMMON_NAME, normalize_dns(primary)))
    return x509.Name(attributes)


def make_private_key(kind: str = "RSA", parameter: str = "2048"):
    if kind == "RSA":
        bits = int(parameter)
        if bits not in (2048, 3072, 4096):
            raise ValueError("RSA key size must be 2048, 3072 or 4096.")
        return rsa.generate_private_key(public_exponent=65537, key_size=bits)
    if kind == "ECDSA":
        curves = {"P-256": ec.SECP256R1, "P-384": ec.SECP384R1}
        if parameter not in curves:
            raise ValueError("ECDSA curve must be P-256 or P-384.")
        return ec.generate_private_key(curves[parameter]())
    raise ValueError(f"Unsupported private key type: {kind}")


def generate_csr(fields: dict[str, str], primary: str, extra: Sequence[str] = (),
                 auto_www: bool = True, key_kind: str = "RSA", key_parameter: str = "2048") -> tuple[bytes, bytes]:
    key = make_private_key(key_kind, key_parameter)
    csr = (x509.CertificateSigningRequestBuilder()
           .subject_name(make_subject(fields, primary))
           .add_extension(x509.SubjectAlternativeName([x509.DNSName(n) for n in san_names(primary, extra, auto_www)]), critical=False)
           .sign(key, hashes.SHA256()))
    csr_bytes = csr.public_bytes(serialization.Encoding.PEM)
    key_bytes = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                  serialization.NoEncryption())
    return csr_bytes, key_bytes


def openssl_command(fields: dict[str, str], primary: str, extra: Sequence[str], auto_www: bool,
                    key_kind: str, key_parameter: str, stem: str) -> str:
    subject_data = dict(fields)
    subject_data["CN"] = normalize_dns(primary)
    sub = "".join("/" + k + "=" + subject_data[k].replace("\\", "\\\\").replace("/", "\\/")
                  for k in ("C", "ST", "L", "O", "OU", "CN") if subject_data.get(k))
    san_ext = "subjectAltName=" + ",".join("DNS:" + n for n in san_names(primary, extra, auto_www))
    if key_kind == "RSA":
        key_flags = f"-newkey rsa:{key_parameter}"
    else:
        curve = {"P-256": "prime256v1", "P-384": "secp384r1"}[key_parameter]
        key_flags = f"-newkey ec -pkeyopt ec_paramgen_curve:{curve}"
    return (f"openssl req -new {key_flags} -nodes \\\n"
            f"  -keyout {shlex.quote(stem + '.key')} \\\n"
            f"  -out {shlex.quote(stem + '.csr')} \\\n"
            f"  -subj {shlex.quote(sub)} \\\n"
            f"  -addext {shlex.quote(san_ext)}")


def read_limited(path: str | Path, max_bytes: int = 5 * 1024 * 1024) -> bytes:
    """Prevent giant/malicious local inputs from unbounded allocation."""
    path = Path(path)
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f'Input file is too large ({size} bytes; limit {max_bytes} bytes).')
    with path.open('rb') as stream:
        result = stream.read(max_bytes + 1)
    if len(result) > max_bytes:
        raise ValueError(f'Input file exceeds the {max_bytes} byte limit.')
    return result


def load_csr(path: str | Path) -> x509.CertificateSigningRequest:
    return parse_csr(read_limited(path))


def parse_csr(data: bytes) -> x509.CertificateSigningRequest:
    try:
        return x509.load_pem_x509_csr(data)
    except ValueError:
        return x509.load_der_x509_csr(data)


def parse_certificates(data: bytes) -> list[x509.Certificate]:
    """Handle PEM blocks in .crt/.txt/.pem, and a single DER X.509 cert."""
    pem_blocks = PEM_CERT_PATTERN.findall(data)
    if pem_blocks:
        return [x509.load_pem_x509_certificate(b) for b in pem_blocks]
    try:
        return [x509.load_der_x509_certificate(data)]
    except ValueError as exc:
        raise ValueError("No X.509 certificate found (PEM or DER).") from exc


def load_key(data: bytes, password: str = ""):
    pw = password.encode("utf-8") if password else None
    try:
        return serialization.load_pem_private_key(data, password=pw)
    except ValueError:
        return serialization.load_der_private_key(data, password=pw)


def fingerprint(key) -> bytes:
    return key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)


def matches_private_key(cert_or_csr, key) -> bool:
    return fingerprint(cert_or_csr.public_key()) == fingerprint(key.public_key())


def display_name(name: x509.Name) -> str:
    return name.rfc4514_string()


def common_name(name: x509.Name) -> str:
    attrs = name.get_attributes_for_oid(NameOID.COMMON_NAME)
    return str(attrs[0].value) if attrs else ""


def get_sans(cert_or_csr) -> list[str]:
    try:
        extension = cert_or_csr.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        return extension.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        return []


def is_ca(cert: x509.Certificate) -> bool:
    try:
        return cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    except x509.ExtensionNotFound:
        return False


def is_self_signed(cert: x509.Certificate) -> bool:
    return cert.subject == cert.issuer and verifies_issuer(cert, cert)


def cert_sha(cert: x509.Certificate) -> bytes:
    return cert.fingerprint(hashes.SHA256())


def key_info(key) -> str:
    if isinstance(key, (rsa.RSAPrivateKey, rsa.RSAPublicKey)):
        return f"RSA {key.key_size} bit"
    if isinstance(key, (ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey)):
        return f"ECDSA {key.curve.name}"
    return type(key).__name__


def validity_info(cert: x509.Certificate, now: datetime | None = None) -> tuple[str, int]:
    now = now or datetime.now(timezone.utc)
    if cert.not_valid_before_utc > now:
        days = (cert.not_valid_before_utc - now).days
        return f"NOT YET VALID ({days} days until activation)", days
    remaining = int((cert.not_valid_after_utc - now).total_seconds() // 86400)
    if cert.not_valid_after_utc <= now:
        return f"EXPIRED ({abs(remaining)} days ago)", remaining
    if remaining <= 30:
        return f"EXPIRING SOON ({remaining} days left)", remaining
    return f"VALID ({remaining} days left)", remaining


def signature_info(obj) -> str:
    """Return signature OID and digest without assuming RSA-only certificates."""
    try:
        digest = obj.signature_hash_algorithm.name.upper() if obj.signature_hash_algorithm else "(not separately specified)"
    except (ValueError, Exception):
        digest = "(not separately specified)"
    return f"{obj.signature_algorithm_oid._name or obj.signature_algorithm_oid.dotted_string} / {digest}"


def cert_report(cert: x509.Certificate, now: datetime | None = None) -> str:
    status, _ = validity_info(cert, now)
    sans = get_sans(cert)
    report = [
        f"Subject: {display_name(cert.subject)}",
        f"Issuer:  {display_name(cert.issuer)}",
        f"Serial:  {hex(cert.serial_number)}",
        f"Type:    {'Root CA' if is_self_signed(cert) and is_ca(cert) else 'Intermediate CA' if is_ca(cert) else 'Server / End-entity'}",
        f"Public key: {key_info(cert.public_key())}",
        f"Signature: {signature_info(cert)}",
        f"SHA-256 fingerprint: {cert.fingerprint(hashes.SHA256()).hex(':').upper()}",
        f"Not Before (UTC): {cert.not_valid_before_utc:%Y-%m-%d %H:%M:%S}",
        f"Not After  (UTC): {cert.not_valid_after_utc:%Y-%m-%d %H:%M:%S}",
        f"Validity: {status}",
        "SAN DNS: " + (", ".join(sans) if sans else "(none)"),
    ]
    try:
        bc = cert.extensions.get_extension_for_class(x509.BasicConstraints).value
        report.append(f"Basic Constraints: CA={bc.ca}, path_length={bc.path_length}")
    except x509.ExtensionNotFound:
        report.append("Basic Constraints: (not present)")
    try:
        ekus = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
        report.append("Extended Key Usage: " + ", ".join(oid._name or oid.dotted_string for oid in ekus))
    except x509.ExtensionNotFound:
        report.append("Extended Key Usage: (not present)")
    return "\n".join(report)


def csr_report(csr: x509.CertificateSigningRequest) -> str:
    subj = csr.subject
    report = [
        f"CSR Signature: {'VALID' if csr.is_signature_valid else 'INVALID'}",
        f"Signature: {signature_info(csr)}",
        f"Subject (RFC4514): {display_name(subj)}",
        "",
        "Subject fields:",
    ]
    for k in ("C", "ST", "L", "O", "OU", "CN"):
        vals = subj.get_attributes_for_oid(OID_MAP[k])
        report.append(f"  {k}: {', '.join(str(x.value) for x in vals) or '(not set)'}")
    report.extend([
        "",
        f"Public Key: {key_info(csr.public_key())}",
        f"Public Key SHA-256: {__import__('hashlib').sha256(fingerprint(csr.public_key())).hexdigest().upper()}",
        "SAN DNS: " + (", ".join(get_sans(csr)) or "(none)"),
        "",
        f"Requested extensions: {len(csr.extensions)}",
    ])
    for extension in csr.extensions:
        report.append(f"  {extension.oid._name or extension.oid.dotted_string}; critical={extension.critical}")
    report.append("Note: A CSR does not have certificate expiry dates.")
    return "\n".join(report)


def dns_covers(pattern: str, domain: str) -> bool:
    """Match exactly or wildcard matching one host label only."""
    pattern = pattern.lower().rstrip(".")
    domain = domain.lower().rstrip(".")
    if pattern == domain:
        return True
    if pattern.startswith("*."):
        suffix = pattern[1:]
        return domain.endswith(suffix) and domain.count(".") == suffix.count(".")
    return False


def compare_csr_cert(csr: x509.CertificateSigningRequest, cert: x509.Certificate) -> str:
    requested = get_sans(csr) or ([common_name(csr.subject)] if common_name(csr.subject) else [])
    issued = get_sans(cert) or ([common_name(cert.subject)] if common_name(cert.subject) else [])
    missing = [r for r in requested if not any(dns_covers(x, r) for x in issued)]
    added = [i for i in issued if i not in requested]
    return "\n".join([
        f"CSR / CRT Public Key: {'MATCH' if fingerprint(csr.public_key()) == fingerprint(cert.public_key()) else 'DIFFERENT'}",
        f"CSR CN: {common_name(csr.subject)}",
        f"CRT CN: {common_name(cert.subject)}",
        f"CSR / CRT CN: {'MATCH' if common_name(csr.subject).lower() == common_name(cert.subject).lower() else 'DIFFERENT'}",
        f"Requested SANs: {', '.join(requested) or '(none)'}",
        f"Issued SANs: {', '.join(issued) or '(none)'}",
        f"Required names covered: {'YES' if not missing else 'NO'}",
        f"Uncovered requested names: {', '.join(missing) or '(none)'}",
        f"Additional issued names: {', '.join(added) or '(none)'}",
    ])


def verifies_issuer(child: x509.Certificate, parent: x509.Certificate) -> bool:
    if child.issuer != parent.subject:
        return False
    pub = parent.public_key()
    try:
        if isinstance(pub, rsa.RSAPublicKey):
            params = child.signature_algorithm_parameters
            if not isinstance(params, padding.AsymmetricPadding):
                return False
            pub.verify(child.signature, child.tbs_certificate_bytes, params, child.signature_hash_algorithm)
        elif isinstance(pub, ec.EllipticCurvePublicKey):
            pub.verify(child.signature, child.tbs_certificate_bytes, ec.ECDSA(child.signature_hash_algorithm))
        elif isinstance(pub, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
            pub.verify(child.signature, child.tbs_certificate_bytes)
        else:
            return False
        return True
    except Exception:
        return False


@dataclass
class ImportedCert:
    certificate: x509.Certificate
    filename: str
    role: str = "Auto"  # Auto, Server, Intermediate CA, Trusted Root, Ignore

    @property
    def guessed_role(self) -> str:
        c = self.certificate
        if not is_ca(c):
            return "Server"
        if is_self_signed(c):
            return "Trusted Root"
        return "Intermediate CA"

    @property
    def effective_role(self) -> str:
        return self.guessed_role if self.role == "Auto" else self.role


@dataclass
class ChainAnalysis:
    leaf: x509.Certificate
    ordered_chain: list[x509.Certificate]
    warnings: list[str]
    ignored: list[x509.Certificate]


def analyze_chain(items: Sequence[ImportedCert]) -> ChainAnalysis:
    items = [i for i in items if i.effective_role != "Ignore"]
    if not items:
        raise ValueError("Import at least one certificate first.")
    # Repeated certificates in CA Bundle and separate DigiCertCA/Root files are deduplicated.
    by_digest: dict[bytes, ImportedCert] = {}
    for item in items:
        ident = cert_sha(item.certificate)
        if ident in by_digest:
            other = by_digest[ident]
            if other.role == "Auto" and item.role != "Auto":
                by_digest[ident] = item
        else:
            by_digest[ident] = item
    items = list(by_digest.values())
    leaves = [i.certificate for i in items if i.effective_role == "Server"]
    if not leaves:
        raise ValueError("No server/domain certificate found. Set its role to Server if needed.")
    if len(leaves) != 1:
        raise ValueError(f"Detected {len(leaves)} server certificates; leave only one Server role (set others to Ignore).")
    leaf = leaves[0]
    if is_ca(leaf):
        raise ValueError("The selected server certificate has CA=TRUE; choose the issued domain certificate.")
    candidates = [i.certificate for i in items if cert_sha(i.certificate) != cert_sha(leaf)]
    chain = []
    warnings = []
    current = leaf
    used = {cert_sha(leaf)}
    for _ in range(len(candidates) + 1):
        if is_self_signed(current):
            break
        parents = [x for x in candidates if cert_sha(x) not in used and is_ca(x) and verifies_issuer(current, x)]
        if len(parents) > 1:
            warnings.append("Multiple valid issuer certificates found; selected one path. Check cross-signed CA chains.")
        if not parents:
            warnings.append("Incomplete chain: issuer certificate not found or cryptographic signature verification failed.")
            break
        parent = parents[0]
        chain.append(parent)
        used.add(cert_sha(parent))
        current = parent
    if chain and not is_self_signed(chain[-1]):
        warnings.append("Trusted self-signed root not supplied; server trust depends on the target platform.")
    if not chain:
        warnings.append("Only the server certificate is in the ordered chain; check the CA intermediates.")
    ignored = [x for x in candidates if cert_sha(x) not in used]
    if ignored:
        warnings.append(f"{len(ignored)} imported certificate(s) are unrelated to the chosen chain and will be omitted.")
    for c in [leaf] + chain:
        status, _ = validity_info(c)
        if not status.startswith("VALID"):
            warnings.append(f"{common_name(c.subject) or display_name(c.subject)}: {status}")
    return ChainAnalysis(leaf, chain, warnings, ignored)


def make_pem(analysis: ChainAnalysis, include_root: bool = True) -> bytes:
    certs = [analysis.leaf] + [c for c in analysis.ordered_chain if include_root or not is_self_signed(c)]
    return b"".join(c.public_bytes(serialization.Encoding.PEM) for c in certs)


def make_pfx(analysis: ChainAnalysis, private_key, password: str, include_root: bool = True,
             legacy_3des: bool = False) -> bytes:
    if not password or len(password) < 8:
        raise ValueError("PFX password must be at least 8 characters.")
    if not matches_private_key(analysis.leaf, private_key):
        raise ValueError("Private key does not match the server certificate; PFX was not generated.")
    ca = [x for x in analysis.ordered_chain if include_root or not is_self_signed(x)]
    if legacy_3des:
        # Use only when a legacy F5 / IIS importer cannot open AES-encrypted PKCS#12.
        # 3DES + SHA-1 is weaker, hence this mode is opt-in only.
        encryption = (serialization.PrivateFormat.PKCS12.encryption_builder()
                      .kdf_rounds(50000)
                      .key_cert_algorithm(pkcs12.PBES.PBESv1SHA1And3KeyTripleDESCBC)
                      .hmac_hash(hashes.SHA1())
                      .build(password.encode("utf-8")))
    else:
        encryption = (serialization.PrivateFormat.PKCS12.encryption_builder()
                      .kdf_rounds(50000)
                      .key_cert_algorithm(pkcs12.PBES.PBESv2SHA256AndAES256CBC)
                      .hmac_hash(hashes.SHA256())
                      .build(password.encode("utf-8")))
    return pkcs12.serialize_key_and_certificates(
        name=(common_name(analysis.leaf.subject) or "SSL Certificate").encode("utf-8"),
        key=private_key, cert=analysis.leaf, cas=ca,
        encryption_algorithm=encryption,
    )


def validate_outputs(pem: bytes, analysis: ChainAnalysis, pfx: bytes | None = None,
                     password: str = "", include_root: bool = True) -> str:
    loaded = parse_certificates(pem)
    expected = [analysis.leaf] + [c for c in analysis.ordered_chain if include_root or not is_self_signed(c)]
    if [cert_sha(c) for c in loaded] != [cert_sha(c) for c in expected]:
        raise ValueError("Generated PEM certificates do not match the assembled chain.")
    report = [f"PEM: VERIFIED ({len(loaded)} certificate(s), leaf first)"]
    for i, cert in enumerate(loaded):
        status, _ = validity_info(cert)
        report.append(f"  [{i+1}] {common_name(cert.subject)}: {status}")
    for i in range(len(loaded)-1):
        if not verifies_issuer(loaded[i], loaded[i+1]):
            raise ValueError("Generated PEM certificates are not a valid issuer sequence.")
    report.append("PEM chain adjacency signatures: VERIFIED")
    if pfx is not None:
        key, cert, cas = pkcs12.load_key_and_certificates(pfx, password.encode("utf-8"))
        if key is None or cert is None or not matches_private_key(cert, key):
            raise ValueError("PFX cannot be parsed or private key does not match.")
        if cert_sha(cert) != cert_sha(analysis.leaf):
            raise ValueError("PFX leaf certificate differs from PEM leaf.")
        expected_ca = {cert_sha(x) for x in expected[1:]}
        if {cert_sha(x) for x in cas or []} != expected_ca:
            raise ValueError("PFX CA certificates differ from the assembled chain.")
        report.append(f"PFX: VERIFIED (encrypted private key matches leaf; {len(cas or [])} CA cert(s))")
    report.extend("WARNING: " + w for w in analysis.warnings)
    report.append("NOTE: Chain signatures/structure were checked; OS/browser trust-store acceptance was not tested.")
    return "\n".join(report)


def safe_write_files(directory: Path, outputs: dict[str, bytes], overwrite: bool = False) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    existing = [directory / name for name in outputs if (directory / name).exists()]
    if existing and not overwrite:
        raise FileExistsError("These files already exist: " + ", ".join(str(p) for p in existing))
    written = []
    for name, data in outputs.items():
        if Path(name).name != name or name in ('.', '..'):
            raise ValueError("Unsafe output file name")
        path = directory / name
        if path.is_symlink():
            raise ValueError('Refusing to overwrite a symbolic link: ' + str(path))
        path.write_bytes(data)
        if path.suffix.lower() in (".key", ".pfx"):
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
        written.append(path)
    return written
