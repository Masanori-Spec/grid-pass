#!/usr/bin/env python3
"""Bounded native GUI bootstrap. Only fixed original SQLite fixtures are opened."""
from pathlib import Path
import json, os, sqlite3, subprocess, time, traceback
import pyatspi

ROOT=Path('/tmp/gridpass-native-gate')
ART=Path(__file__).resolve().parents[1]/'artifacts/native'
DB=ROOT/'fixture.sqlite'; WORK=ROOT/'workspace'; HOME_DIR=ROOT/'profile'
BIN=ROOT/'official/dbeaver/dbeaver'; JAR=ROOT/'sqlite-jdbc-3.53.4.0.jar'; DRIVERS=ROOT/'drivers.xml'
assert (ART/'consumer-pin.json').is_file() and BIN.is_file() and JAR.is_file()
assert not DB.exists() and not HOME_DIR.exists() and not WORK.exists()
for p in [HOME_DIR,WORK,ROOT/'xdg-data',ROOT/'xdg-config',ROOT/'xdg-cache']:p.mkdir()
env=os.environ.copy();env.update(XDG_DATA_HOME=str(ROOT/'xdg-data'),XDG_CONFIG_HOME=str(ROOT/'xdg-config'),XDG_CACHE_HOME=str(ROOT/'xdg-cache'),GTK_MODULES='gail:atk-bridge',LANG='en_US.UTF-8')
DRIVERS.write_text(f'<drivers><provider id="sqlite"><driver id="sqlite_jdbc" class="org.sqlite.JDBC" url="jdbc:sqlite:{{file}}" custom="false" embedded="true" anonymous="true"><library type="jar" path="{JAR}" custom="true"/></driver></provider></drivers>\n')
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
        try: rows.append({'depth':depth,'role':n.getRoleName(),'name':n.name,'description':n.description,'rect':rect(n),'states':[str(s) for s in n.getState().getStates()]})
        except Exception:pass
    (ART/f'{label}-tree.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    cmd('scrot',str(ART/f'{label}.png'))
    return rows
def click(n,count=1):
    r=rect(n);assert r and r[2]>0 and r[3]>0,'Control has no real screen extent'
    x,y=r[0]+r[2]//2,r[1]+r[3]//2
    assert 0<=x<1600 and 0<=y<1000,'Control is outside the hosted screen'
    cmd('xdotool','mousemove',str(x),str(y));cmd('xdotool','click','--repeat',str(count),'--delay','150','1');time.sleep(.5)
def unique_screen(items):
    # R2 exposes identical native controls through both tab subtrees. Collapse
    # only the same role/name/description at the exact same screen rectangle.
    # Different physical locations remain ambiguous; raw snapshots retain all.
    result=[];seen=set()
    for n in items:
        r=rect(n)
        if r is None:continue
        key=(n.getRoleName(),n.name,n.description,tuple(r))
        if key not in seen:seen.add(key);result.append(n)
    return result
def matching(name,role=None,scope=None):
    found=[]
    for n,_ in (walk(scope,[12000]) if scope is not None else nodes()):
        try:
            if n.name==name and (role is None or n.getRoleName() in role) and n.getState().contains(pyatspi.STATE_SHOWING):found.append(n)
        except Exception:pass
    return unique_screen(found)
def one(name,roles=None,seconds=20,scope=None):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        found=matching(name,roles,scope)
        if len(found)==1:return found[0]
        time.sleep(.25)
    raise AssertionError(f'Expected one visible native control: {name!r}; got {len(found)}')
def modal_frame(title):
    found=[]
    for n,_ in nodes():
        try:
            if n.getRoleName() in ['frame','dialog'] and n.name.strip()==title and n.getState().contains(pyatspi.STATE_SHOWING) and n.getState().contains(pyatspi.STATE_MODAL):found.append(n)
        except Exception:pass
    found=unique_screen(found);assert len(found)==1,f'Expected one actual modal frame: {title}'
    return found[0]
def configure():
    assert matching('Configure DBeaver',['label']),'Expected the observed initial native wizard'
    opted_out=False
    for step in range(8):
        snapshot(f'03-wizard-{step}')
        if matching('Data collection',['label']):
            radio=one('Do not share anonymous usage statistics',['radio button'])
            if not radio.getState().contains(pyatspi.STATE_CHECKED):click(radio)
            assert radio.getState().contains(pyatspi.STATE_CHECKED)
            opted_out=True
        if matching('Final steps',['label']):
            assert opted_out,'Native data-collection choice was not reviewed'
            for name in ['Create sample database','Turn on "Tip of the day"']:
                for n in matching(name,['check box']):
                    if n.getState().contains(pyatspi.STATE_CHECKED):click(n)
            # Final-page actions are limited to these source-confirmed optional
            # sample/tip choices. No unknown checked action may be accepted.
            for n,_ in nodes():
                if n.getRoleName()=='check box' and n.getState().contains(pyatspi.STATE_SHOWING) and n.getState().contains(pyatspi.STATE_CHECKED):
                    assert n.name in ['Create sample database','Turn on "Tip of the day"'],'Unexpected checked final action'
            snapshot('04-reviewed-final-steps');click(one('Apply',['push button']));return
        click(one('Next >',['push button']))
    raise AssertionError('Unexpected product-configuration page sequence')
def open_table():
    one('Connections',['page tab'],seconds=40)
    for _ in range(12):
        found=matching('source_table',['table cell','tree item'])
        if found:
            assert len(found)==1;click(found[0],2);break
        progressed=False
        for name in ['GridPass Fixture','main','Tables']:
            for n in matching(name,['table cell','tree item']):
                state=n.getState()
                if not state.contains(pyatspi.STATE_EXPANDED):
                    click(n);cmd('xdotool','key','--clearmodifiers','Right');time.sleep(1);progressed=True;break
            if progressed:break
        time.sleep(1)
    else:raise AssertionError('Synthetic source table was not exposed by the native navigator')
    click(one('Data',['page tab'],seconds=30));time.sleep(2);snapshot('05-source-data')
    grids=[]
    for n,_ in nodes():
        try:
            if n.description=='Results grid' and n.getState().contains(pyatspi.STATE_SHOWING):grids.append(n)
        except Exception:pass
    grids=unique_screen(grids)
    assert len(grids)==1,'One actual native Results grid is required'
    grid=grids[0];r=rect(grid);assert r and r[2]>100 and r[3]>70
    subprocess.run(['xclip','-selection','clipboard'],input='GRIDPASS_PENDING',text=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=10)
    cmd('xdotool','mousemove',str(r[0]+60),str(r[1]+50));cmd('xdotool','click','1')
    cmd('xdotool','key','--clearmodifiers','ctrl+a');cmd('xdotool','key','--clearmodifiers','ctrl+c');time.sleep(.5)
    copied=cmd('xclip','-selection','clipboard','-o');(ART/'native-source-grid.tsv').write_text(copied)
    rows=copied.rstrip('\r\n').splitlines()
    if rows and rows[0]=='id\tname\tstatus\tnote':rows=rows[1:]
    assert rows==['1\tAlba\tB\tnote1','2\tBasil\tA\tnote2','3\tCedar\tB\tnote3','4\tDahlia\tC\tnote4','5\tElm\tA\tnote5'],'Actual grid differs from literal original SQLite rows'
    snapshot('06-copied-native-grid');cmd('xdotool','key','Escape');cmd('xdotool','key','F11');time.sleep(.5)
    snapshot('07-filter-menu');click(one('Customize filters ...',['menu item']));time.sleep(.5)
    snapshot('08-native-filter-settings')
    dialog=modal_frame('Result Set Order/Filter Settings')
    click(one('Cancel',['push button'],scope=dialog))
    return rows
def normal_exit(proc):
    cmd('xdotool','key','--clearmodifiers','Alt+F4')
    deadline=time.monotonic()+30;answered=False
    while proc.poll() is None and time.monotonic()<deadline:
        titles=[]
        for n,_ in nodes():
            try:
                if n.getRoleName() in ['dialog','frame']:titles.append(n.name.strip())
            except Exception:
                # Native accessibles can retire before the process is reaped.
                # Their disappearance is never a substitute for exit status0.
                continue
        if 'Exit DBeaver' in titles and not answered:
            dialog=modal_frame('Exit DBeaver')
            snapshot('09-native-exit-confirmation')
            click(one('Yes',['push button'],scope=dialog));answered=True
            break
        time.sleep(.3)
    code=proc.wait(timeout=max(.1,deadline-time.monotonic()))
    assert code==0,f'Normal native exit did not succeed: {code}'
    return answered

log=open(ART/'dbeaver.log','w')
args=[str(BIN),'-newInstance','-nosplash','-nl','en_US','-data',str(WORK),'-con',f'driver=sqlite:sqlite_jdbc|database={DB}|name=GridPass Fixture|save=true|connect=true','-vmargs',f'-Duser.home={HOME_DIR}',f'-Ddbeaver.drivers.configuration-file={DRIVERS}','-Xmx1200m']
proc=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT)
try:
    for i in range(60):
        assert proc.poll() is None,'Official GUI exited during startup'
        time.sleep(1)
        if matching('Configure DBeaver',['label']):break
    startup=snapshot('01-startup')
    assert len(startup)>3 and any('DBeaver' in row['name'] for row in startup),'Native accessibility evidence is missing'
    titles=[n.name for n,_ in nodes() if n.getRoleName() in ['dialog','frame']]
    (ART/'startup-titles.json').write_text(json.dumps(titles,indent=2)+'\n')
    windows=cmd('xdotool','search','--onlyvisible','--name','DBeaver').splitlines()
    if windows:cmd('xdotool','windowsize',windows[-1],'1500','950')
    time.sleep(2);snapshot('02-native-window')
    assert any('DBeaver' in s for s in titles),'No native DBeaver window exposed'
    configure();time.sleep(2);snapshot('04-main-window');rows=open_table()
    profile_jars=[str(p) for base in [WORK,HOME_DIR,ROOT/'xdg-data',ROOT/'xdg-config',ROOT/'xdg-cache'] for p in base.rglob('*.jar')]
    assert not profile_jars,'Unexpected driver download into the disposable profile'
    exit_confirmed=normal_exit(proc);log.flush()
    assert 'A fatal error has been detected' not in (ART/'dbeaver.log').read_text(),'Native runtime reported a fatal error'
    (ART/'provided-drivers.xml').write_bytes(DRIVERS.read_bytes())
    report={'status':'CONNECTED_TABLE_OBSERVED','fullNativeLayoutGate':'PENDING','normalExit':proc.returncode,'nativeExitConfirmation':exit_confirmed,'disposableWorkspace':str(WORK),'disposableJavaUserHome':str(HOME_DIR),'syntheticTables':['source_table','target_table','unrelated_table'],'localDriverJar':JAR.name,'profileDownloadedJars':profile_jars,'literalNativeGridRows':rows,'note':'Native local-driver/table/filter-dialog compatibility only; no layout transfer or product UI acceptance'}
    (ART/'bootstrap-report.json').write_text(json.dumps(report,indent=2)+'\n')
except Exception:
    (ART/'failure.txt').write_text(traceback.format_exc());snapshot('failure');raise
finally:
    if proc.poll() is None:
        proc.terminate()
        try:proc.wait(timeout=20)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
    log.close()
