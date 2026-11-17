from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

import core


def self_signed_ca(subject_name, key, when, expires):
    subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_name)])
    return (x509.CertificateBuilder().subject_name(subj).issuer_name(subj)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(when).not_valid_after(expires)
            .add_extension(x509.BasicConstraints(ca=True, path_length=2), critical=True)
            .sign(key, hashes.SHA256()))


def signed_cert(subject_name, key, ca_cert, ca_key, is_ca, when, expires, sans=()):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_name)])
    builder = (x509.CertificateBuilder().subject_name(name).issuer_name(ca_cert.subject)
               .public_key(key.public_key()).serial_number(x509.random_serial_number())
               .not_valid_before(when).not_valid_after(expires)
               .add_extension(x509.BasicConstraints(ca=is_ca, path_length=0 if is_ca else None), critical=True))
    if sans:
        builder = builder.add_extension(x509.SubjectAlternativeName([x509.DNSName(n) for n in sans]), critical=False)
    return builder.sign(ca_key, hashes.SHA256())


class TestCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        now = datetime.now(timezone.utc)
        before, after = now - timedelta(days=10), now + timedelta(days=200)
        cls.root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.inter_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.root = self_signed_ca("Example Test Root CA", cls.root_key, before, after)
        cls.inter = signed_cert("DigiCert Test Intermediate CA", cls.inter_key, cls.root, cls.root_key, True, before, after)
        cls.leaf = signed_cert("www.example.com", cls.server_key, cls.inter, cls.inter_key, False,
                               before, after, ["www.example.com", "example.com"])

    def test_san_automatic_variants(self):
        self.assertEqual(core.san_names("www.example.com"), ["www.example.com", "example.com"])
        self.assertEqual(core.san_names("example.com"), ["example.com", "www.example.com"])
        self.assertEqual(core.san_names("*.example.com"), ["*.example.com", "example.com"])
        self.assertEqual(core.san_names("www.example.com", ["example.com", "portal.example.com"]),
                         ["www.example.com", "example.com", "portal.example.com"])
        with self.assertRaises(ValueError):
            core.normalize_dns("www.*.example.com")

    def test_folder_and_filename(self):
        dt = datetime(2026, 11, 16)
        self.assertEqual(core.output_stem("www.example.com", dt), "example_202611")
        self.assertEqual(core.output_directory("C:/Users/Andy/Desktop", "www.example.com", dt).as_posix(),
                         "C:/Users/Andy/Desktop/example_202611")
        self.assertEqual(core.output_stem("*.example.com", dt), "example_202611")

    def test_generate_and_verify_csr(self):
        csr_data, key_data = core.generate_csr(core.DEFAULT_SUBJECT, "www.example.com",
                                               ["portal.example.com"], True, "RSA", "2048")
        csr = core.parse_csr(csr_data)
        key = core.load_key(key_data)
        self.assertTrue(csr.is_signature_valid)
        self.assertTrue(core.matches_private_key(csr, key))
        self.assertEqual(core.get_sans(csr), ["www.example.com", "example.com", "portal.example.com"])
        self.assertIn("CSR does not have certificate expiry", core.csr_report(csr))
        self.assertIn("-addext", core.openssl_command(core.DEFAULT_SUBJECT, "www.example.com", [], True, "RSA", "2048", "example_202611"))

    def test_generate_ecdsa_csr(self):
        csr_data, key_data = core.generate_csr(core.DEFAULT_SUBJECT, "*.example.com", [], True, "ECDSA", "P-256")
        csr = core.parse_csr(csr_data)
        self.assertTrue(csr.is_signature_valid)
        self.assertTrue(core.matches_private_key(csr, core.load_key(key_data)))
        self.assertEqual(core.get_sans(csr), ["*.example.com", "example.com"])

    def test_parse_multi_cert_txt_and_der(self):
        combo = (self.leaf.public_bytes(serialization.Encoding.PEM)
                 + self.inter.public_bytes(serialization.Encoding.PEM)
                 + self.root.public_bytes(serialization.Encoding.PEM))
        self.assertEqual(len(core.parse_certificates(combo)), 3)
        self.assertEqual(len(core.parse_certificates(self.root.public_bytes(serialization.Encoding.DER))), 1)
        with self.assertRaises(ValueError):
            core.parse_certificates(b"This is not a certificate")

    def test_chain_auto_classification_order(self):
        items = [core.ImportedCert(self.root, "TrustedRoot.txt"),
                 core.ImportedCert(self.leaf, "domain.crt"),
                 core.ImportedCert(self.inter, "DigiCertCA.crt"),
                 core.ImportedCert(self.root, "CA Bundle.txt")]
        analysis = core.analyze_chain(items)
        self.assertEqual(analysis.leaf, self.leaf)
        self.assertEqual(analysis.ordered_chain, [self.inter, self.root])
        self.assertEqual(analysis.warnings, [])
        pem = core.make_pem(analysis)
        self.assertEqual(len(core.parse_certificates(pem)), 3)
        self.assertIn("VERIFIED", core.validate_outputs(pem, analysis))
        pem_without_root = core.make_pem(analysis, include_root=False)
        self.assertEqual(len(core.parse_certificates(pem_without_root)), 2)
        self.assertIn("VERIFIED", core.validate_outputs(pem_without_root, analysis, include_root=False))

    def test_pfx_matches_and_reopens_modern_legacy(self):
        analysis = core.analyze_chain([core.ImportedCert(self.inter, "DigiCertCA"),
                                       core.ImportedCert(self.root, "TrustedRoot"),
                                       core.ImportedCert(self.leaf, "domain")])
        pem = core.make_pem(analysis)
        for legacy in [False, True]:
            pfx = core.make_pfx(analysis, self.server_key, "TestingStrongPfx27!", legacy_3des=legacy)
            report = core.validate_outputs(pem, analysis, pfx, "TestingStrongPfx27!")
            self.assertIn("PFX: VERIFIED", report)
        with self.assertRaisesRegex(ValueError, "does not match"):
            core.make_pfx(analysis, self.wrong_key, "TestingStrongPfx27!")
        with self.assertRaisesRegex(ValueError, "at least 8"):
            core.make_pfx(analysis, self.server_key, "short")

    def test_missing_ca_warnings(self):
        analysis = core.analyze_chain([core.ImportedCert(self.leaf, "domain.crt"),
                                       core.ImportedCert(self.root, "TrustedRoot.txt")])
        self.assertTrue(any("Incomplete chain" in s for s in analysis.warnings))
        self.assertTrue(any("unrelated" in s for s in analysis.warnings))
        with self.assertRaisesRegex(ValueError, "No server"):
            core.analyze_chain([core.ImportedCert(self.root, "root.crt")])

    def test_wildcard_coverage(self):
        self.assertTrue(core.dns_covers("*.example.com", "abc.example.com"))
        self.assertFalse(core.dns_covers("*.example.com", "example.com"))
        self.assertFalse(core.dns_covers("*.example.com", "a.b.example.com"))

    def test_expiration(self):
        now = datetime.now(timezone.utc)
        cert = signed_cert("expired.example.com", self.server_key, self.inter, self.inter_key, False,
                           now - timedelta(days=20), now - timedelta(days=1))
        self.assertIn("EXPIRED", core.validity_info(cert)[0])

    def test_file_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "example_202611"
            core.safe_write_files(folder, {"example_202611.csr": b"TEST"})
            with self.assertRaises(FileExistsError):
                core.safe_write_files(folder, {"example_202611.csr": b"REPLACE"})
            core.safe_write_files(folder, {"example_202611.csr": b"REPLACE"}, overwrite=True)
            self.assertEqual((folder / "example_202611.csr").read_bytes(), b"REPLACE")


if __name__ == "__main__":
    unittest.main()
