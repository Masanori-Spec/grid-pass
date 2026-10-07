#!/usr/bin/env python3
"""Real native GUI authoring and layout-consumption gate; fixed synthetic inputs only."""
from pathlib import Path
import json, os, sqlite3, subprocess, time, traceback, shutil
import pyatspi

PROJECT=Path(__file__).resolve().parents[1]
ROOT=Path('/tmp/gridpass-native-gate')
BASE_ART=PROJECT/'artifacts/native'; ART=BASE_ART/'author';ART.mkdir(parents=True,exist_ok=True)
DB=ROOT/'fixture.sqlite'; WORK=ROOT/'workspace'; HOME_DIR=ROOT/'profile'
BIN=ROOT/'official/dbeaver/dbeaver';JAR=ROOT/'sqlite-jdbc-3.53.4.0.jar';DRIVERS=ROOT/'drivers.xml'
assert (BASE_ART/'consumer-pin.json').is_file() and BIN.is_file() and JAR.is_file()
assert not DB.exists() and not HOME_DIR.exists() and not WORK.exists()
for p in [HOME_DIR,WORK,ROOT/'xdg-data',ROOT/'xdg-config',ROOT/'xdg-cache']:p.mkdir()
env=os.environ.copy();env.update(XDG_DATA_HOME=str(ROOT/'xdg-data'),XDG_CONFIG_HOME=str(ROOT/'xdg-config'),XDG_CACHE_HOME=str(ROOT/'xdg-cache'),GTK_MODULES='gail:atk-bridge',LANG='en_US.UTF-8')
DRIVERS.write_text(f'<drivers><provider id="sqlite"><driver id="sqlite_jdbc" class="org.sqlite.JDBC" url="jdbc:sqlite:{{file}}" custom="false" embedded="true" anonymous="true"><library type="jar" path="{JAR}" custom="true"/></driver></provider></drivers>\n')
DATA=[(1,'Alba','B','note1'),(2,'Basil','A','note2'),(3,'Cedar','B','note3'),(4,'Dahlia','C','note4'),(5,'Elm','A','note5')]
with sqlite3.connect(DB) as db:
    for table in ['source_table','target_table','unrelated_table']:
        name_type='VARCHAR(40)' if table=='target_table' else 'TEXT'
        db.execute(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY, name {name_type}, status TEXT, note TEXT)')
        db.executemany(f'INSERT INTO {table} (id,name,status,note) VALUES (?,?,?,?)',DATA)
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

def by_description(description,scope=None):
    result=[]
    for n,_ in (walk(scope,[12000]) if scope is not None else nodes()):
        try:
            if n.description==description and n.getState().contains(pyatspi.STATE_SHOWING):result.append(n)
        except Exception:pass
    return unique_screen(result)
def grid():
    result=by_description('Results grid');assert len(result)==1,'One physical native results grid required'
    return result[0]
def focus_grid():
    r=rect(grid());assert r and r[2]>100 and r[3]>70
    # R5 pixels place the first data row35px below the grid top. This also works
    # for the one-row unrelated sentinel, without clicking an empty second row.
    cmd('xdotool','mousemove',str(r[0]+60),str(r[1]+35));cmd('xdotool','click','1')
def clear_clipboard():
    subprocess.run(['xclip','-selection','clipboard'],input='GRIDPASS_PENDING',text=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=10)
def copy_grid(label,columns,expected):
    clear_clipboard();focus_grid();cmd('xdotool','key','--clearmodifiers','ctrl+a');cmd('xdotool','key','--clearmodifiers','ctrl+c');time.sleep(.3)
    raw=cmd('xclip','-selection','clipboard','-o');(ART/f'{label}.tsv').write_text(raw)
    lines=raw.rstrip('\r\n').splitlines();header=False
    if lines and lines[0]=='\t'.join(columns):header=True;lines=lines[1:]
    rows=[line.split('\t') for line in lines]
    snapshot(label)
    assert rows==expected,(label,'Actual native grid mismatch',rows)
    return {'rows':rows,'copiedHeader':header,'columnsExpected':columns,'rawFile':str((ART/f'{label}.tsv').relative_to(BASE_ART))}
def open_table(name):
    one('Connections',['page tab'],seconds=40)
    for _ in range(12):
        found=matching(name,['table cell','tree item'])
        if found:
            assert len(found)==1;click(found[0],2);break
        progressed=False
        for branch in ['GridPass Fixture','main','Tables']:
            for n in matching(branch,['table cell','tree item']):
                if not n.getState().contains(pyatspi.STATE_EXPANDED):
                    click(n);cmd('xdotool','key','--clearmodifiers','Right');time.sleep(.5);progressed=True;break
            if progressed:break
        time.sleep(.5)
    else:raise AssertionError(f'Native table not exposed: {name}')
    tab=one(name,['page tab'],seconds=30);assert tab.getState().contains(pyatspi.STATE_SELECTED),'Wrong active native table'
    click(one('Data',['page tab'],seconds=30));time.sleep(1);grid()
def select_cell(row,column,literal):
    focus_grid();cmd('xdotool','key','--clearmodifiers','ctrl+Home')
    for _ in range(row):cmd('xdotool','key','Down')
    for _ in range(column):cmd('xdotool','key','Right')
    clear_clipboard();cmd('xdotool','key','--clearmodifiers','ctrl+c');time.sleep(.3)
    actual=cmd('xclip','-selection','clipboard','-o').rstrip('\r\n')
    assert actual==literal,('Selected native cell',literal,actual)
def cell_filter(label):
    cmd('xdotool','key','F11');time.sleep(.3)
    lo=rect(one('Cell value',['menu item']));hi=rect(one('Custom',['menu item']))
    options=[n for n in matching(label,['menu item']) if lo[1]+lo[3]<=rect(n)[1]<hi[1]]
    assert len(options)==1,'One exact Cell value action required; Clipboard/Custom actions excluded'
    assert options[0].getState().contains(pyatspi.STATE_ENABLED)
    snapshot('filter-'+str(len(list(ART.glob('filter-*.png')))))
    click(options[0]);time.sleep(1)
def settings():
    focus_grid();cmd('xdotool','key','F11');time.sleep(.3);click(one('Customize filters ...',['menu item']));time.sleep(.3)
    return modal_frame('Result Set Order/Filter Settings')
def row_node(dialog,name):return one(name,['table cell'],scope=dialog)
def cell_click(dialog,name,column):
    row=row_node(dialog,name);click(row)
    header=one(column,['table column header'],scope=dialog);r=rect(row);h=rect(header)
    cmd('xdotool','mousemove',str(h[0]+h[2]//2),str(r[1]+r[3]//2));cmd('xdotool','click','1');time.sleep(.5)
def dialog_rows(dialog):
    rows=[{'name':name,'rect':rect(row_node(dialog,name))} for name in ['id','name','status','note']]
    return sorted(rows,key=lambda x:x['rect'][1])
def source_layout():
    dialog=settings()
    cell_click(dialog,'id','Pinned');cell_click(dialog,'note','Visible')
    click(row_node(dialog,'status'));up=by_description('Move up',dialog);assert len(up)==1 and up[0].getState().contains(pyatspi.STATE_ENABLED);click(up[0])
    assert [r['name'] for r in dialog_rows(dialog)]==['id','status','name','note']
    cell_click(dialog,'status','Order');cell_click(dialog,'id','Order');cell_click(dialog,'id','Order')
    snapshot('source-authored-settings');click(one('OK',['push button'],scope=dialog));time.sleep(1)
def target_layout():
    dialog=settings();cell_click(dialog,'name','Pinned');snapshot('target-original-settings');click(one('OK',['push button'],scope=dialog));time.sleep(1)
def save_default(label):
    focus_grid();cmd('xdotool','key','F11');time.sleep(.3)
    save=one('Save as default filter',['menu item']);assert save.getState().contains(pyatspi.STATE_ENABLED)
    snapshot(label+'-save-default');click(save);time.sleep(4) # native ConfigSaver delay is3000ms
def observe_settings(label,expected_order):
    dialog=settings();rows=dialog_rows(dialog)
    assert [r['name'] for r in rows]==expected_order
    snapshot(label);click(one('Cancel',['push button'],scope=dialog));return rows
def launch(first,phase):
    global ART,LIVE_PROC,LIVE_LOG
    ART=BASE_ART/phase;ART.mkdir(parents=True,exist_ok=True)
    log=open(ART/'dbeaver.log','w')
    args=[str(BIN),'-newInstance','-nosplash','-nl','en_US','-data',str(WORK)]
    if first:args+=['-con',f'driver=sqlite:sqlite_jdbc|database={DB}|name=GridPass Fixture|save=true|connect=true']
    args+=['-vmargs',f'-Duser.home={HOME_DIR}',f'-Ddbeaver.drivers.configuration-file={DRIVERS}','-Xmx1200m']
    proc=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT)
    LIVE_PROC,LIVE_LOG=proc,log
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        assert proc.poll() is None,'Native app exited during startup'
        if matching('Configure DBeaver',['label']) if first else matching('Connections',['page tab']):break
        time.sleep(.5)
    else:raise AssertionError('Native startup timed out')
    snapshot('startup')
    if first:configure()
    one('Connections',['page tab'],seconds=40)
    windows=cmd('xdotool','search','--onlyvisible','--name','^DBeaver').splitlines();assert windows
    cmd('xdotool','windowsize',windows[-1],'1500','950');time.sleep(.5)
    return proc,log
def close_run(proc,log):
    global LIVE_PROC,LIVE_LOG
    confirmed=normal_exit(proc);log.flush()
    text=(ART/'dbeaver.log').read_text();assert 'A fatal error has been detected' not in text and 'Platform shutdown completed' in text
    assert "driverVersion='3.53.4.0'" in text,'The fresh native process did not report the pinned local JDBC version'
    log.close();LIVE_PROC=None;LIVE_LOG=None
    return {'exit':proc.returncode,'confirmation':confirmed}
def configuration_path():
    found=set()
    for base in [WORK,HOME_DIR,ROOT/'xdg-data',ROOT/'xdg-config']:
        found.update(base.rglob('saved-data-filter.xml'))
    assert len(found)==1,'Exactly one native-emitted fixture config is required'
    return next(iter(found))

EXPECTED={
 'positive':(['id','status','name'],[['5','A','Elm'],['2','A','Basil'],['3','B','Cedar'],['1','B','Alba']],['id','status','name','note']),
 'positive-reloaded':(['id','status','name'],[['5','A','Elm'],['2','A','Basil'],['3','B','Cedar'],['1','B','Alba']],['id','status','name','note']),
 'negative-visibility':(['id','status','name','note'],[['5','A','Elm','note5'],['2','A','Basil','note2'],['3','B','Cedar','note3'],['1','B','Alba','note1']],['id','status','name','note']),
 'negative-position':(['id','name','status'],[['5','Elm','A'],['2','Basil','A'],['3','Cedar','B'],['1','Alba','B']],['id','name','status','note']),
 'negative-pin':(['id','name','status'],[['5','Elm','A'],['2','Basil','A'],['3','Cedar','B'],['1','Alba','B']],['id','status','name','note']),
 'negative-sort':(['id','status','name'],[['2','A','Basil'],['5','A','Elm'],['1','B','Alba'],['3','B','Cedar']],['id','status','name','note']),
}
proc=None;log=None;LIVE_PROC=None;LIVE_LOG=None;observations=[]
try:
    proc,log=launch(True,'author')
    open_table('source_table');copy_grid('source-original',['id','name','status','note'],[[str(v) for v in r] for r in DATA])
    select_cell(1,0,'2');cell_filter("id > '2'");source_layout()
    copy_grid('source-authored',['id','status','name'],[['5','A','Elm'],['3','B','Cedar'],['4','C','Dahlia']]);save_default('source')
    open_table('target_table');select_cell(3,2,'C');cell_filter("status <> 'C'");target_layout()
    copy_grid('target-original',['name','id','status','note'],[['Alba','1','B','note1'],['Basil','2','A','note2'],['Cedar','3','B','note3'],['Elm','5','A','note5']]);save_default('target')
    open_table('unrelated_table');select_cell(3,2,'C');cell_filter("status = 'C'")
    copy_grid('unrelated-original',['id','name','status','note'],[['4','Dahlia','C','note4']]);save_default('unrelated')
    author_exit=close_run(proc,log);proc=None;log=None
    config=configuration_path();shutil.copyfile(config,BASE_ART/'original-saved-data-filter.xml')
    (BASE_ART/'configuration-location.json').write_text(json.dumps({'relativeToDisposableRoot':str(config.relative_to(ROOT)),'authorExit':author_exit},indent=2)+'\n')
    cmd('node',str(PROJECT/'scripts/prepare-layout.mjs'))
    cmd('/usr/bin/python3',str(PROJECT/'scripts/verify-layout.py'),'inputs')
    for mode,(columns,rows,order) in EXPECTED.items():
        if mode!='positive-reloaded':shutil.copyfile(BASE_ART/'variants'/f'{mode}.xml',config)
        proc,log=launch(False,mode);open_table('target_table')
        observed=copy_grid('actual-target-grid',columns,rows);observed['mode']=mode
        observed['dialogRows']=observe_settings('actual-target-settings',order)
        save_default('target');observed['lifecycle']=close_run(proc,log);proc=None;log=None
        shutil.copyfile(config,BASE_ART/f'{mode}-native-saved.xml');observations.append(observed)
    with sqlite3.connect(f'file:{DB}?mode=ro',uri=True) as db:
        for table in ['source_table','target_table','unrelated_table']:
            assert db.execute(f'SELECT id,name,status,note FROM {table} ORDER BY id').fetchall()==DATA,'Fixture data was edited'
    assert not [p for base in [WORK,HOME_DIR,ROOT/'xdg-data',ROOT/'xdg-config',ROOT/'xdg-cache'] for p in base.rglob('*.jar')]
    (BASE_ART/'gui-observations.json').write_text(json.dumps({'observations':observations,'databaseRowsUnchanged':True,'sourceFixtureAuthorExit':author_exit},indent=2)+'\n')
    cmd('/usr/bin/python3',str(PROJECT/'scripts/verify-layout.py'),'final')
except Exception:
    (ART/'failure.txt').write_text(traceback.format_exc());snapshot('failure');raise
finally:
    if LIVE_PROC is not None and LIVE_PROC.poll() is None:
        LIVE_PROC.terminate()
        try:LIVE_PROC.wait(timeout=20)
        except subprocess.TimeoutExpired:LIVE_PROC.kill();LIVE_PROC.wait(timeout=10)
    if LIVE_LOG is not None:LIVE_LOG.close()
