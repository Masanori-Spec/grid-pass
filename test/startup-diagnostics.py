"""Replay pure startup/diagnostic helpers without importing or launching the GUI."""
import ast,json,tempfile
from pathlib import Path
from types import SimpleNamespace
import re
source=Path(__file__).resolve().parents[1]/'scripts/gui-gate.py'
module=ast.parse(source.read_text())
selected=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ['wait_native_window','crash_excerpt']],type_ignores=[])
def harness(observe,guard=lambda p:None):
    clock=SimpleNamespace(value=0.0)
    clock.monotonic=lambda:clock.value
    def sleep(seconds):clock.value+=seconds
    clock.sleep=sleep
    temp=tempfile.TemporaryDirectory();space={'time':clock,'json':json,'re':re,'ART':Path(temp.name),'x_window_snapshot':lambda:observe(clock.value),'assert_native_alive':guard}
    exec(compile(selected,str(source),'exec'),space)
    return space,clock,temp
window={'windowId':'1','title':'DBeaver','geometry':'WIDTH=1000\nHEIGHT=700'}
space,clock,temp=harness(lambda t:window if t>=2 else None);space['wait_native_window'](None);assert clock.value==12;assert json.loads((space['ART']/'startup-readiness.json').read_text())['minimumStableWindowSeconds']==6;temp.cleanup()
space,clock,temp=harness(lambda t:dict(window,title='Loading' if t<10 else 'DBeaver'));space['wait_native_window'](None);assert clock.value==16;temp.cleanup()
space,clock,temp=harness(lambda t:None)
try:space['wait_native_window'](None)
except AssertionError:assert clock.value==60
else:raise AssertionError('Missing window was accepted')
temp.cleanup()
def fatal(p):raise AssertionError('Fatal native marker')
space,clock,temp=harness(lambda t:window,fatal)
try:space['wait_native_window'](None)
except AssertionError as e:assert str(e)=='Fatal native marker' and clock.value==0
else:raise AssertionError('Fatal process was accepted')
sample='''#  SIGSEGV (0xb)
# JRE version: Temurin25
# Java VM: OpenJDK
# Problematic frame:
# C  [libgtk.so+0x123]
Command Line: PRIVATE_COMMAND
Current thread (0x123): JavaThread "main"
Native frames: (J=compiled Java code)
C  [libgtk.so+0x123] gtk_widget_get_allocation
J  java.method()V

Java frames: (J=compiled Java code)
j  org.eclipse.swt.internal.gtk.OS.call()V

siginfo: PRIVATE_SIGINFO
Registers:
RAX=PRIVATE_REGISTER
Stack memory: PRIVATE_MEMORY
Environment Variables:
API_KEY=PRIVATE_SECRET
Java frames: PRIVATE_FAKE_HEADER
j  PRIVATE_FAKE_FRAME
'''
excerpt=space['crash_excerpt'](sample);assert len(excerpt)==11,excerpt;assert all('PRIVATE_' not in line for line in excerpt);assert any('gtk_widget_get_allocation' in line for line in excerpt);assert any('org.eclipse.swt' in line for line in excerpt);temp.cleanup()
print('PASS bounded X-window settling, timeout/fatal failure and safe crash-frame extraction')
