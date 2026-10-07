#!/usr/bin/env python3
"""Official binaries for hosted synthetic tests only; no product loading API."""
from pathlib import Path
import hashlib, json, tarfile, urllib.request

ROOT = Path('/tmp/gridpass-native-gate')
ART = Path(__file__).resolve().parents[1] / 'artifacts/native'
COMMIT = '5171a0a5864591ee78225a216586fd7535b15085'
PINS = [
    {'repo':'dbeaver/dbeaver','tag':'26.2.2','name':'dbeaver-ce-26.2.2-linux-x86_64.tar.gz','bytes':127503062,'sha256':'27b39a79a69ec70f9f95c6ee3b68514fcc7677acef93287e8df8e13cc53384d5'},
    {'repo':'xerial/sqlite-jdbc','tag':'3.53.4.0','name':'sqlite-jdbc-3.53.4.0.jar','bytes':12002370,'sha256':'bcb1f51e36f940867e83342f9efbf5968ac44a6bef4d397bb4af7b17b45cd2fb'},
]
def get(url, limit):
    req=urllib.request.Request(url, headers={'User-Agent':'GridPass-native-fixture','Accept':'application/vnd.github+json' if 'api.github.com' in url else '*/*'})
    with urllib.request.urlopen(req,timeout=90) as response:
        data=response.read(limit+1)
    assert len(data)<=limit,'Remote byte limit'
    return data

assert not ROOT.exists(), 'Synthetic test root must start absent'
ROOT.mkdir(); ART.mkdir(parents=True,exist_ok=True)
tag=json.loads(get('https://api.github.com/repos/dbeaver/dbeaver/git/ref/tags/26.2.2',1_000_000))
assert tag['object']['type']=='commit' and tag['object']['sha']==COMMIT
for pin in PINS:
    release=json.loads(get(f'https://api.github.com/repos/{pin["repo"]}/releases/tags/{pin["tag"]}',2_000_000))
    assets=[a for a in release['assets'] if a['name']==pin['name']]
    assert len(assets)==1
    asset=assets[0];url=f'https://github.com/{pin["repo"]}/releases/download/{pin["tag"]}/{pin["name"]}'
    assert asset['browser_download_url']==url and asset['size']==pin['bytes'] and asset['digest']=='sha256:'+pin['sha256']
    data=get(url,pin['bytes']);assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256']
    (ROOT/pin['name']).write_bytes(data);pin['url']=url
(ART/'consumer-pin.json').write_text(json.dumps({'beforeExecution':True,'sourceCommit':COMMIT,'assets':PINS},indent=2)+'\n')
with tarfile.open(ROOT/PINS[0]['name'],'r:gz') as archive:
    assert len(archive.getmembers())<20000
    archive.extractall(ROOT/'official',filter='data')
assert (ROOT/'official/dbeaver/dbeaver').is_file()
print('Exact official release metadata and bytes verified before extraction/execution')
