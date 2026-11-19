import tempfile,unittest
from pathlib import Path
from datetime import datetime, timezone
import watch_store,activity_log

class WatchStoreTests(unittest.TestCase):
    def test_roundtrip_and_duplicate_normalization(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'watch.json'
            watch_store.save_watchlist([{'target':'www.example.com:443','last_good':None,'last_attempt':'','error':'Not checked'}],path)
            self.assertEqual(watch_store.read_watchlist(path)[0]['target'],'www.example.com:443')
            self.assertEqual(watch_store.watch_key('https://www.example.com'),'www.example.com:443')
    def test_invalid_watch_entries_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'watch.json';path.write_text('[{"target":"file:///etc/passwd"},{"target":"www.example.com"}]')
            self.assertEqual(len(watch_store.read_watchlist(path)),1)
    def test_last_known_days(self):
        item={'last_good':{'expires_at':'2027-01-01T00:00:00+00:00'}}
        self.assertEqual(watch_store.remaining_days(item,datetime(2026,12,31,tzinfo=timezone.utc)),1)
    def test_activity_does_not_require_network(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'activity.db'
            activity_log.record('CSR Generated','example.com','C:/out',path=path)
            self.assertEqual(activity_log.recent(path=path)[0][1],'CSR Generated')
            activity_log.clear(path)
            self.assertEqual(activity_log.recent(path=path),[])
if __name__=='__main__':unittest.main()
