"""Network-free security and inspection regression tests."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import live_ssl
import core


class TestTargetSecurity(unittest.TestCase):
    def test_valid_hosts_and_https_urls(self):
        self.assertEqual(live_ssl.parse_target('www.example.com').host, 'www.example.com')
        self.assertEqual(live_ssl.parse_target('https://www.example.com:8443/path').port, 8443)
        self.assertTrue(live_ssl.parse_target('https://www.example.com/path').path_ignored)
        self.assertEqual(live_ssl.parse_target('https://[::1]:443').host, '::1')

    def test_reject_bad_schemes_credentials_and_control_chars(self):
        bad = ['http://example.com', 'file:///etc/passwd', 'ftp://example.com',
               'https://test@example.com', 'example.com\nHost: evil.com',
               '*.example.com', 'example.com?secret=abc', 'https://example.com/#x',
               'https://example.com:0', 'https://example.com:65536', 'x' * 2500]
        for value in bad:
            with self.subTest(value=value[:30]), self.assertRaises(ValueError):
                live_ssl.parse_target(value)

    def test_wildcard_comparison(self):
        kept, added, removed = live_ssl.compare_sans(
            ('*.example.com','example.com'), ('*.example.com','example.com','api.extra.com'))
        self.assertEqual(kept, ('*.example.com','example.com'))
        self.assertEqual(added, ('api.extra.com',))
        self.assertEqual(removed, ())
        _, _, removed = live_ssl.compare_sans(('*.example.com',), ('www.example.com',))
        self.assertEqual(removed, ('*.example.com',))

    def test_certificate_classification(self):
        self.assertEqual(live_ssl.certificate_type(('*.example.com','example.com')), 'Mixed (Wildcard + SAN)')
        self.assertEqual(live_ssl.certificate_type(('www.example.com',)), 'Single-Domain')

    def test_limited_file_reader(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'too_big.crt'
            target.write_bytes(b'A' * 12)
            with self.assertRaises(ValueError):
                core.read_limited(target, 10)
            self.assertEqual(core.read_limited(target, 12), b'A' * 12)

    def test_live_inspect_does_not_get_web_page(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'www.example.com')])
        now = datetime.now(timezone.utc)
        crt = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
               .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=2))
               .not_valid_after(now+timedelta(days=120))
               .add_extension(x509.SubjectAlternativeName([x509.DNSName('www.example.com')]), critical=False)
               .sign(key, hashes.SHA256()))
        from cryptography.hazmat.primitives.serialization import Encoding
        der = crt.public_bytes(Encoding.DER)
        with patch.object(live_ssl, 'lookup_dns', return_value=(('93.184.215.14',), ())), \
             patch.object(live_ssl, '_tls_connect', side_effect=[(der,'TLSv1.3','TLS_AES_256_GCM_SHA384'), (der,'TLSv1.3','TLS_AES_256_GCM_SHA384')]) as tls:
            result = live_ssl.inspect('www.example.com')
        self.assertEqual(tls.call_count, 2)
        self.assertTrue(result.hostname_ok)
        self.assertTrue(result.trust_ok)
        self.assertEqual(result.health, 'valid')


if __name__ == '__main__':
    unittest.main()
