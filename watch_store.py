"""Local, bounded and atomic watch-list persistence. No private keys stored."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from datetime import datetime, timezone
from live_ssl import parse_target
MAX_WATCHED = 100

def data_dir() -> Path:
    root = Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.local'/'share')/'SSL_Certificate_Toolkit'
    root.mkdir(parents=True, exist_ok=True)
    return root

def watch_key(raw: str) -> str:
    t = parse_target(raw)
    return t.host.lower()+':'+str(t.port)

def read_watchlist(path: Path | None = None) -> list[dict]:
    path = path or data_dir()/'watchlist.json'
    try:
        if path.stat().st_size > 1024*1024: return []
        data=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data,list): return []
        output=[]; seen=set()
        for item in data[:MAX_WATCHED]:
            if not isinstance(item,dict): continue
            try: key=watch_key(str(item['target']))
            except (KeyError, ValueError, TypeError): continue
            if key in seen: continue
            seen.add(key)
            output.append({'target':key,'last_good':item.get('last_good') if isinstance(item.get('last_good'),dict) else None,
                           'last_attempt':str(item.get('last_attempt',''))[:48], 'error':str(item.get('error',''))[:350]})
        return output
    except (OSError,ValueError,TypeError): return []

def save_watchlist(items: list[dict], path: Path | None = None) -> None:
    path=path or data_dir()/'watchlist.json'
    if len(items)>MAX_WATCHED: raise ValueError('Watch list limit reached (100).')
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.watch-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(items,f,ensure_ascii=False,indent=2)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def snapshot(result) -> dict:
    return {'checked_at':result.checked_at.isoformat(),'expires_at':result.expires_at.isoformat(),
            'issuer':result.issuer[:240], 'subject_cn':result.subject_cn[:240],
            'certificate_type':result.certificate_type[:100], 'fingerprint':result.fingerprint[:130],
            'connected_ip':result.connected_ip[:64], 'hostname_ok':result.hostname_ok,
            'trust_ok':result.trust_ok, 'health':result.health,'sans':list(result.sans[:128])}

def remaining_days(item: dict, now: datetime | None = None) -> int | None:
    try:
        dt=datetime.fromisoformat(item['last_good']['expires_at'])
        if dt.tzinfo is None: return None
        return int((dt-(now or datetime.now(timezone.utc))).total_seconds()//86400)
    except (KeyError,TypeError,ValueError): return None
