#!/usr/bin/env python3
"""Bounded native GUI bootstrap. Only fixed original SQLite fixtures are opened."""
from pathlib import Path
import json, os, sqlite3, subprocess, time, traceback
import pyatspi

ROOT=Path('/tmp/gridpass-native-gate')
ART=Path(__file__).resolve().parents[1]/'artifacts/native'
DB=ROOT/'fixture.sqlite'; WORK=ROOT/'workspace'; HOME_DIR=ROOT/'profile'
BIN=ROOT/'official/dbeaver/dbeaver'; JAR=ROOT/'sqlite-jdbc-3.53.4.0.jar'
assert (ART/'consumer-pin.json').is_file() and BIN.is_file() and JAR.is_file()
assert not DB.exists() and not HOME_DIR.exists() and not WORK.exists()
for p in [HOME_DIR,WORK,ROOT/'xdg-data',ROOT/'xdg-config',ROOT/'xdg-cache']:p.mkdir()
env=os.environ.copy();env.update(XDG_DATA_HOME=str(ROOT/'xdg-data'),XDG_CONFIG_HOME=str(ROOT/'xdg-config'),XDG_CACHE_HOME=str(ROOT/'xdg-cache'),GTK_MODULES='gail:atk-bridge',LANG='en_US.UTF-8')
with sqlite3.connect(DB) as db:
    for table in ['source_table','target_table','unrelated_table']:
        db.execute(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY, name TEXT, status TEXT, note TEXT)')
        db.executemany(f'INSERT INTO {table} VALUES (?,?,?,?)',[(1,'Alba','B','note1'),(2,'Basil','A','note2'),(3,'Cedar','B','note3'),(4,'Dahlia','C','note4'),(5,'Elm','A','note5')])
def cmd(*args):return subprocess.run(args,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15).stdout
def walk(node,budget,depth=0):
    if depth>30 or budget[0]<=0:return
    budget[0]-=1
    yield node,depth
    try:count=min(node.childCount,budget[0])
    except Exception:return
    for index in range(count):
        if budget[0]<=0:break
        try:child=node[index]
        except Exception:continue
        if child is not None:yield from walk(child,budget,depth+1)
def nodes():return list(walk(pyatspi.Registry.getDesktop(0),[12000]))
def rect(n):
    try:
        r=n.queryComponent().getExtents(pyatspi.DESKTOP_COORDS);return [r.x,r.y,r.width,r.height]
    except Exception:return None
def snapshot(label):
    rows=[]
    for n,depth in nodes():
        try: rows.append({'depth':depth,'role':n.getRoleName(),'name':n.name,'description':n.description,'rect':rect(n),'states':[pyatspi.stateToString(s) for s in n.getState().getStates()]})
        except Exception:pass
    (ART/f'{label}-tree.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    cmd('scrot',str(ART/f'{label}.png'))
    return rows
def click(n,count=1):
    r=rect(n);assert r and r[2]>0 and r[3]>0,'Control has no real screen extent'
    x,y=r[0]+r[2]//2,r[1]+r[3]//2
    cmd('xdotool','mousemove',str(x),str(y));cmd('xdotool','click','--repeat',str(count),'--delay','150','1');time.sleep(.5)
def matching(name,role=None):
    found=[]
    for n,_ in nodes():
        try:
            if n.name==name and (role is None or n.getRoleName() in role) and n.getState().contains(pyatspi.STATE_SHOWING):found.append(n)
        except Exception:pass
    return found

log=open(ART/'dbeaver.log','w')
args=[str(BIN),'-newInstance','-nosplash','-nl','en_US','-data',str(WORK),'-con',f'driver=sqlite|database={DB}|name=GridPass Fixture','-vmargs',f'-Duser.home={HOME_DIR}','-Xmx1200m']
proc=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT)
try:
    for i in range(60):
        assert proc.poll() is None,'Official GUI exited during startup'
        time.sleep(1)
        if matching('Database Navigator'):break
    snapshot('01-startup')
    # This diagnostic does not accept dialogs. They remain as actual evidence
    # for the next bounded source-reviewed fixture-registration revision.
    titles=[n.name for n,_ in nodes() if n.getRoleName() in ['dialog','frame']]
    (ART/'startup-titles.json').write_text(json.dumps(titles,indent=2)+'\n')
    windows=cmd('xdotool','search','--onlyvisible','--name','DBeaver').splitlines()
    if windows:cmd('xdotool','windowsize',windows[-1],'1500','950')
    time.sleep(2);snapshot('02-native-window')
    # Compatibility discovery only: it must visibly identify the official GUI.
    assert any('DBeaver' in s for s in titles),'No native DBeaver window exposed'
    report={'status':'BOOTSTRAP_OBSERVED','fullNativeLayoutGate':'PENDING','disposableWorkspace':str(WORK),'disposableJavaUserHome':str(HOME_DIR),'syntheticTables':['source_table','target_table','unrelated_table'],'downloadedDriverJar':JAR.name,'driverRegistration':'PENDING','note':'Startup evidence only; pinned jar is downloaded, not yet registered; no layout transfer or product UI acceptance'}
    (ART/'bootstrap-report.json').write_text(json.dumps(report,indent=2)+'\n')
except Exception:
    (ART/'failure.txt').write_text(traceback.format_exc());snapshot('failure');raise
finally:
    if proc.poll() is None:
        proc.terminate()
        try:proc.wait(timeout=20)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
    log.close()
