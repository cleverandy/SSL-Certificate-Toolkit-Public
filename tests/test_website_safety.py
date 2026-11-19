import unittest
from website_safety import assess_target
class SafetyTests(unittest.TestCase):
    def test_no_false_safety_certification(self):
        self.assertIn('No malware/phishing reputation lookup', ' '.join(assess_target('www.example.com')))
    def test_ip_warning(self):
        self.assertIn('IP address', ' '.join(assess_target('https://127.0.0.1:443')))
if __name__=='__main__':unittest.main()
