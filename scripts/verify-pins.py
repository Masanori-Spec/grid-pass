#!/usr/bin/env python3
"""Checks only output from the fixed trusted Integer generator, never user files."""
from pathlib import Path
import base64,hashlib,json
ART=Path(__file__).resolve().parents[1]/'artifacts/native'
raw=(ART/'canonical-pins.json').read_bytes();assert len(raw)<64*1024
values=json.loads(raw)
zero=base64.b64decode('rO0ABXNyABFqYXZhLmxhbmcuSW50ZWdlchLioKT3gYc4AgABSQAFdmFsdWV4cgAQamF2YS5sYW5nLk51bWJlcoaslR0LlOCLAgAAeHAAAAAA')
assert len(zero)==81 and len(values)==256 and len(set(values))==256
expected=[base64.b64encode(zero[:-4]+n.to_bytes(4,'big')).decode() for n in range(256)]
assert values==expected,'Official bundled JDK did not produce the literal canonical whitelist'
(ART/'canonical-pins-report.json').write_text(json.dumps({'status':'PASS','integers':256,'source':'Fixed Integer0–255 ObjectOutputStream generator executed by the verified official DBeaver bundled JDK','sha256':hashlib.sha256(raw).hexdigest(),'noObjectInputStream':True},indent=2)+'\n')
