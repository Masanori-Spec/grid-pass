#!/usr/bin/env python3
"""Independent literal oracle and exact controlled faults, fixed native fixtures only."""
from pathlib import Path
import hashlib,json,re,sys,xml.etree.ElementTree as ET
from xml.parsers import expat
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'artifacts/native'
assert len(sys.argv)==2 and sys.argv[1] in ['inputs','final','selftest']
PINS=[] if sys.argv[1]=='selftest' else json.loads((ART/'canonical-pins.json').read_text())
STRING_C='rO0ABXQAAUM='
NAMES=['id','name','status','note']
LAYOUT={'id':(0,True,2,True,0),'name':(2,True,None,False,None),'status':(1,True,1,False,None),'note':(3,False,None,False,None)}
def sha(b):return hashlib.sha256(b).hexdigest()
def filters(raw):
    root=ET.fromstring(raw);assert root.tag=='data-filters'
    result={}
    for node in root:
        assert node.tag=='filter';table=node.attrib['objectId'].split('@@/@@')[-1]
        assert table not in result;result[table]=node
    assert set(result)=={'source_table','target_table','unrelated_table'}
    return result
def columns(node):
    result={c.attrib['name']:c for c in node.findall('constraint')};assert set(result)==set(NAMES) and len(node.findall('constraint'))==4
    return result
def layout(node):
    result={}
    for name,c in columns(node).items():
        pin=c.findall("option[@name='pinned']");assert len(pin)<=1
        p=None if not pin else PINS.index(pin[0].text)
        result[name]=(int(c.attrib['pos']),c.get('visible','true')=='true',int(c.get('order')) if c.get('order') is not None else None,c.get('orderDesc','false')=='true',p)
    return result
def signature(n,remove_layout=False):
    if remove_layout and n.tag=='option' and n.get('name')=='pinned':return None
    attrs=sorted((k,v) for k,v in n.attrib.items() if not(remove_layout and n.tag=='constraint' and k in ['pos','visible','order','orderDesc']))
    content=n.text if n.tag in ['option','value'] else (n.text or '').strip()
    return (n.tag,attrs,content,[s for c in n if (s:=signature(c,remove_layout)) is not None])
def chunks(raw):
    result={}
    for m in re.finditer(rb'<filter\b[^>]*>[\s\S]*?</filter>',raw):
        node=ET.fromstring(m.group());table=node.attrib['objectId'].split('@@/@@')[-1];assert table not in result;result[table]=m.group()
    assert set(result)=={'source_table','target_table','unrelated_table'}
    return result
def opening_end(raw,start):
    quote=None
    for i in range(start,len(raw)):
        char=raw[i]
        if quote:
            if char==quote:quote=None
        elif char in (34,39):quote=char
        elif char==62:return i+1
    raise AssertionError('Unterminated native start tag')
def target_mask(raw):
    # Expat identifies real elements, so fake tags in comments cannot be masked.
    # Only attributes on direct constraint start tags are mutable; filter-level
    # order is a protected SQL expression and every inter-element byte remains.
    parser=expat.ParserCreate();stack=[];patches=[]
    def start(name,attrs):
        offset=parser.CurrentByteIndex;end=opening_end(raw,offset);tag=raw[offset:end]
        direct=stack and stack[-1]['path']==('filter',)
        node={'name':name,'start':offset,'openEnd':end,'selfClosing':tag.endswith(b'/>'),'path':tuple(n['name'] for n in stack)+(name,),'pin':False}
        if direct and name=='constraint':
            for m in re.finditer(rb"\s+([A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*([\"'])(.*?)\2",tag,re.S):
                if m[1] in [b'pos',b'visible',b'order',b'orderDesc']:patches.append((offset+m.start(),offset+m.end(),b''))
            if node['selfClosing']:patches.append((end-2,end,b'></constraint>'))
        if node['path']==('filter','constraint','option') and attrs.get('name')=='pinned':node['pin']=True
        stack.append(node)
    def end(name):
        node=stack.pop();assert node['name']==name
        if node['pin']:
            stop=node['openEnd'] if node['selfClosing'] else opening_end(raw,parser.CurrentByteIndex)
            patches.append((node['start'],stop,b''))
    parser.StartElementHandler=start;parser.EndElementHandler=end
    parser.Parse(raw,True)
    last=len(raw)
    for begin,end,replacement in sorted(patches,reverse=True):
        assert end<=last;raw=raw[:begin]+replacement+raw[end:];last=begin
    return raw
def own_nonlayout_raw(before,after):
    assert before[:opening_end(before,0)]==after[:opening_end(after,0)],'Target filter identity/predicate bytes changed'
    assert target_mask(before)==target_mask(after),'Protected target bytes changed outside allowed constraint layout fields'
def edit_column(raw,name,change):
    blocks=chunks(raw);target=blocks['target_table']
    pattern=rb'<constraint\b[^>]*\bname="'+name.encode()+rb'"[^>]*(?:/>|>[\s\S]*?</constraint>)'
    matches=list(re.finditer(pattern,target));assert len(matches)==1
    m=matches[0];new=target[:m.start()]+change(m.group())+target[m.end():]
    assert raw.count(target)==1;return raw.replace(target,new,1)
def set_attribute(raw,key,value):
    end=raw.index(b'>');tag=raw[:end+1];tail=raw[end+1:]
    pattern=rb'\s+'+key.encode()+rb'="[^"]*"';assert len(re.findall(pattern,tag))==1
    return re.sub(pattern,b' '+key.encode()+b'="'+value.encode()+b'"',tag,count=1)+tail
def add_pin(raw):
    assert b'name="pinned"' not in raw
    option=b'<option name="pinned">'+PINS[1].encode()+b'</option>'
    return raw[:-2]+b'>'+option+b'</constraint>' if raw.endswith(b'/>') else raw[:-len(b'</constraint>')]+option+b'</constraint>'

if sys.argv[1]=='selftest':
    before=b'<filter objectId="target" order="protected SQL"><!-- keep <constraint pos="9"/> -->\n<constraint name="id" pos="0" criteria="opaque"/>\n<constraint name="name" pos="1"><!-- inner --><value>opaque</value><option name="pinned">PIN</option> </constraint></filter>'
    after=before.replace(b'pos="0" criteria="opaque"/>',b'pos="1" criteria="opaque"><option name="pinned">NEW</option></constraint>').replace(b'pos="1"><!-- inner -->',b'pos="0" visible="false"><!-- inner -->').replace(b'<option name="pinned">PIN</option>',b'')
    own_nonlayout_raw(before,after)
    for fault in [after.replace(b'<!-- inner -->',b'<!-- altered -->'),after.replace(b'\n<constraint',b'  <constraint',1),after.replace(b'protected SQL',b'leaked SQL'),after.replace(b'pos="9"',b'pos="8"'),after.replace(b'<value>opaque',b'<value>changed')]:
        try:own_nonlayout_raw(before,fault)
        except AssertionError:pass
        else:raise AssertionError('Protected-byte fault was hidden by the mask')
    print('PASS entire-target mask and five protected-byte fault controls');sys.exit(0)

original=(ART/'original-saved-data-filter.xml').read_bytes();base=filters(original);original_parts=chunks(original)
assert layout(base['source_table'])==LAYOUT,'Native-authored source layout differs from literal contract'
sc=columns(base['source_table']);tc=columns(base['target_table']);uc=columns(base['unrelated_table'])
assert sc['id'].get('operator')=='GREATER' and sc['id'].findtext('value'),'Native source predicate was not authored'
assert tc['status'].get('operator')=='NOT_EQUALS' and tc['status'].findtext('value')==STRING_C
assert tc['id'].get('operator') is None and not tc['id'].findall('value')
assert uc['status'].get('operator')=='EQUALS' and uc['status'].findtext('value')==STRING_C
assert layout(base['target_table'])=={'id':(0,True,None,False,None),'name':(1,True,None,False,0),'status':(2,True,None,False,None),'note':(3,True,None,False,None)}
def name_binding(node):
    matches=node.findall("flatten-attribute-bindings/attribute[@name='name']");assert len(matches)==1
    return matches[0]
assert name_binding(base['source_table']).get('typeName')=='TEXT','Source name binding must be native TEXT'
assert name_binding(base['target_table']).get('typeName')=='VARCHAR','Target name binding must be native VARCHAR'

positive=(ART/'variants/positive.xml').read_bytes();p=filters(positive);parts=chunks(positive)
assert layout(p['target_table'])==LAYOUT
assert signature(base['target_table'],True)==signature(p['target_table'],True)
assert original.replace(original_parts['target_table'],b'TARGET')==positive.replace(parts['target_table'],b'TARGET'),'Outside-target bytes changed'
own_nonlayout_raw(original_parts['target_table'],parts['target_table'])
receipt=json.loads((ART/'layout-receipt.json').read_text());assert receipt['inputSHA256']==sha(original) and receipt['outputSHA256']==sha(positive)
assert receipt['sourceId']==base['source_table'].get('objectId') and receipt['targetId']==base['target_table'].get('objectId')
assert [c['name'] for c in receipt['columns']]==NAMES and receipt['changedColumns']==4
for c in receipt['columns']:
    for field,expected in [('before',layout(base['target_table'])[c['name']]),('after',LAYOUT[c['name']])]:
        row=c[field];assert row['name']==c['name']
        assert (row['position'],row['visible'],row['sortPriority'],row['descending'],row['pinIndex'])==expected
    assert c['changed'] is True
faults={
 'negative-visibility':edit_column(positive,'note',lambda b:set_attribute(b,'visible','true')),
 'negative-position':edit_column(edit_column(positive,'name',lambda b:set_attribute(b,'pos','1')),'status',lambda b:set_attribute(b,'pos','2')),
 'negative-pin':edit_column(positive,'name',add_pin),
 'negative-sort':edit_column(positive,'id',lambda b:set_attribute(b,'orderDesc','false')),
}
expected_layouts={'positive':LAYOUT}
for mode in faults:
    expected=dict(LAYOUT)
    if mode=='negative-visibility':expected['note']=(3,True,None,False,None)
    if mode=='negative-position':expected['name']=(1,True,None,False,None);expected['status']=(2,True,1,False,None)
    if mode=='negative-pin':expected['name']=(2,True,None,False,1)
    if mode=='negative-sort':expected['id']=(0,True,2,False,0)
    expected_layouts[mode]=expected
for mode,raw in faults.items():
    target=filters(raw)['target_table'];assert layout(target)==expected_layouts[mode]
    assert signature(target,True)==signature(base['target_table'],True)
    changed=chunks(raw);assert positive.replace(parts['target_table'],b'TARGET')==raw.replace(changed['target_table'],b'TARGET')
    own_nonlayout_raw(parts['target_table'],changed['target_table'])
    if sys.argv[1]=='inputs':(ART/'variants'/f'{mode}.xml').write_bytes(raw)
    else:assert (ART/'variants'/f'{mode}.xml').read_bytes()==raw,'Negative input is not the exact intended fault'
if sys.argv[1]=='inputs':
    (ART/'layout-input-report.json').write_text(json.dumps({'status':'PASS','inputSHA256':sha(original),'positiveSHA256':sha(positive),'targetNonlayoutSubtreesUnchanged':True,'allTargetBytesOutsideLayoutFieldsUnchanged':True,'nameBindingTypes':{'source':'TEXT','target':'VARCHAR'},'allOutsideTargetBytesUnchanged':True,'sourcePredicateNotTransferred':True,'faultHashes':{m:sha(b) for m,b in faults.items()}},indent=2)+'\n')
    print('PASS actual native fixture, selected-target byte patch and four exact layout faults');sys.exit(0)

# These row arrays and dialog orders are handwritten; nothing is derived from JS.
EXPECT={
 'positive':([['5','A','Elm'],['2','A','Basil'],['3','B','Cedar'],['1','B','Alba']],['id','status','name','note']),
 'positive-reloaded':([['5','A','Elm'],['2','A','Basil'],['3','B','Cedar'],['1','B','Alba']],['id','status','name','note']),
 'negative-visibility':([['5','A','Elm','note5'],['2','A','Basil','note2'],['3','B','Cedar','note3'],['1','B','Alba','note1']],['id','status','name','note']),
 'negative-position':([['5','Elm','A'],['2','Basil','A'],['3','Cedar','B'],['1','Alba','B']],['id','name','status','note']),
 'negative-pin':([['5','Elm','A'],['2','Basil','A'],['3','Cedar','B'],['1','Alba','B']],['id','status','name','note']),
 'negative-sort':([['2','A','Basil'],['5','A','Elm'],['1','B','Alba'],['3','B','Cedar']],['id','status','name','note']),
}
obs=json.loads((ART/'gui-observations.json').read_text());assert obs['databaseRowsUnchanged'] is True and obs['sourceFixtureAuthorExit']['exit']==0
assert [o['mode'] for o in obs['observations']]==list(EXPECT)
checks=[]
for o in obs['observations']:
    mode=o['mode'];rows,order=EXPECT[mode]
    assert o['rows']==rows and [r['name'] for r in o['dialogRows']]==order
    assert o['lifecycle']['exit']==0
    raw=(ART/o['rawFile']).read_text().rstrip('\r\n').splitlines()
    if o['copiedHeader']:raw=raw[1:]
    assert [r.split('\t') for r in raw]==rows
    saved=filters((ART/f'{mode}-native-saved.xml').read_bytes())
    assert layout(saved['target_table'])==expected_layouts['positive' if mode=='positive-reloaded' else mode]
    assert signature(saved['target_table'],True)==signature(base['target_table'],True),'Native save changed nonlayout target semantics'
    for other in ['source_table','unrelated_table']:assert signature(saved[other])==signature(base[other]),'Native save changed another entry'
    negative=mode.startswith('negative-')
    if negative:assert rows!=EXPECT['positive'][0],'Positive grid oracle accepted negative control'
    checks.append({'mode':mode,'literalNativeGridAndDialogOrder':'PASS','nativeSaveAndExit':'PASS','positiveGridOracleRejected':negative})
(ART/'native-layout-report.json').write_text(json.dumps({'status':'PASS','scope':'Actual unchanged official DBeaver GUI and saved-data-filter loader; original synthetic fixtures only','checks':checks,'sourceFixtureSHA256':sha(original),'patchedSHA256':sha(positive),'targetNonlayoutPreserved':True,'otherEntriesPreserved':True,'fourExactFaultsObserved':True,'nativePinCheckboxScreenshotsRequireIndependentReview':True,'normalizationBoundary':'Product output preserves protected bytes. Subsequent native save is checked for the same protected semantics, not whole-file byte identity.'},indent=2)+'\n')
print('PASS actual native target grids, save/fresh reopen, preserved predicates/bindings and four exact controls')
