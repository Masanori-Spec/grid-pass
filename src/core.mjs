import { DOMParser } from '@xmldom/xmldom';
import { PIN_VALUES } from './pinned-values.mjs';
export const LIMITS=Object.freeze({fileBytes:4*1024*1024,elements:30000,depth:32,entries:512,columns:256});
export class LayoutError extends Error { constructor(code,message){super(message);this.name='LayoutError';this.code=code;} }
const fail=(code,message)=>{throw new LayoutError(code,message);};
const els=n=>Array.from(n.childNodes||[]).filter(x=>x.nodeType===1);
const pinLookup=new Map(PIN_VALUES.map((value,index)=>[value,index]));
export function decodePinned(value){if(!pinLookup.has(value))fail('PIN_ENCODING','Pinned values must exactly match the canonical Integer0–255 whitelist');return pinLookup.get(value);}
export function encodePinned(value){if(!Number.isInteger(value)||value<0||value>255)fail('PIN_RANGE','Pin index must be0–255');return PIN_VALUES[value];}
const xmlSpace=c=>c===' '||c==='\t'||c==='\r'||c==='\n';
const xmlChar=n=>n===9||n===10||n===13||(n>=32&&n<=0xd7ff)||(n>=0xe000&&n<=0xfffd)||(n>=0x10000&&n<=0x10ffff);
const nameStart=c=>c==='_'||(c>='A'&&c<='Z')||(c>='a'&&c<='z');
const namePart=c=>nameStart(c)||(c>='0'&&c<='9')||c==='.'||c==='-';
// One advancing cursor, bounded names/references/attributes, and no searching regex.
// Comments and CDATA are consumed once; their apparent markup is never rescanned.
function lexXML(text) {
  let i=text.charCodeAt(0)===0xfeff?1:0, tokens=0,totalAttributes=0,roots=0;
  const beginning=i,stack=[],spans=[];
  const name=()=>{
    const start=i;if(!nameStart(text[i]))fail('INVALID_XML','Expected an unprefixed XML name');
    while(i<text.length&&namePart(text[i])){if(i-start>=128)fail('XML_LIMIT','XML names are bounded');i++;}
    if(text[i]===':')fail('UNSUPPORTED_XML','XML namespaces are unsupported');
    return text.slice(start,i);
  };
  const reference=()=>{
    const start=i++;while(i<text.length&&text[i]!==';'&&i-start<=32)i++;
    if(text[i]!==';'||i-start>32)fail('INVALID_XML','Malformed or oversized XML reference');
    const ref=text.slice(start+1,i++);
    if(['amp','lt','gt','apos','quot'].includes(ref))return;
    if(!/^#(?:[0-9]+|x[0-9a-fA-F]+)$/.test(ref))fail('INVALID_XML','Unsupported XML entity reference');
    const n=ref[1]==='x'?parseInt(ref.slice(2),16):Number(ref.slice(1));
    if(!xmlChar(n))fail('INVALID_XML','Forbidden numeric XML character');
  };
  while(i<text.length){
    if(++tokens>80000)fail('XML_LIMIT','XML token limit exceeded');
    if(text[i]!=='<'){
      while(i<text.length&&text[i]!=='<'){
        if(!stack.length&&!xmlSpace(text[i]))fail('INVALID_XML','Text outside the root element');
        if(text.startsWith(']]>',i))fail('INVALID_XML','CDATA terminator in ordinary text');
        if(text[i]==='&')reference();else i++;
      }
      continue;
    }
    const start=i;
    if(text.startsWith('<!--',i)){
      const end=text.indexOf('--',i+4);
      if(end<0||text[end+2]!=='>')fail('INVALID_XML','Malformed or unterminated XML comment');
      i=end+3;continue;
    }
    if(text.startsWith('<![CDATA[',i)){
      if(!stack.length)fail('INVALID_XML','CDATA outside root');
      const end=text.indexOf(']]>',i+9);if(end<0)fail('INVALID_XML','Unterminated CDATA');
      i=end+3;continue;
    }
    if(text.startsWith('<?',i)){
      const end=text.indexOf('?>',i+2);
      if(end<0||end+2-start>256)fail('INVALID_XML','Unterminated or oversized processing instruction');
      const token=text.slice(start,end+2);
      if(!token.startsWith('<?xml ')&&!token.startsWith('<?xml\t')&&!token.startsWith('<?xml\r')&&!token.startsWith('<?xml\n'))fail('UNSUPPORTED_XML','Processing instructions are unsupported');
      if(start!==beginning)fail('INVALID_XML','XML declaration must occur once at the start');
      if(!/^<\?xml[ \t\r\n]+version[ \t\r\n]*=[ \t\r\n]*(?:"1\.0"|'1\.0')(?:[ \t\r\n]+encoding[ \t\r\n]*=[ \t\r\n]*(?:"[Uu][Tt][Ff]-8"|'[Uu][Tt][Ff]-8'))?(?:[ \t\r\n]+standalone[ \t\r\n]*=[ \t\r\n]*(?:"(?:yes|no)"|'(?:yes|no)'))?[ \t\r\n]*\?>$/.test(token))fail('XML_VERSION','Only XML1.0 with optional UTF-8 encoding declaration is supported');
      i=end+2;continue;
    }
    if(text.startsWith('<!',i))fail('XML_DOCTYPE','DTD and entity declarations are unsupported');
    i++;
    if(text[i]==='/'){
      i++;const tag=name();while(xmlSpace(text[i]))i++;
      if(text[i++]!=='>')fail('INVALID_XML','Malformed closing tag');
      const opened=stack.pop();if(!opened||opened.name!==tag)fail('INVALID_XML','Mismatched XML elements');
      opened.closeStart=start;opened.end=i;continue;
    }
    const tag=name(),attributes=new Map();let selfClosing=false;
    while(true){
      const attrStart=i;while(xmlSpace(text[i]))i++;
      if(text[i]==='>'){i++;break;}
      if(text[i]==='/'&&text[i+1]==='>'){i+=2;selfClosing=true;break;}
      if(i===attrStart)fail('INVALID_XML','Attributes require separating whitespace');
      const key=name();if(key==='xmlns')fail('UNSUPPORTED_XML','XML namespaces are unsupported');
      if(attributes.has(key))fail('INVALID_XML','Duplicate XML attribute');
      if(attributes.size>=64||++totalAttributes>120000)fail('XML_LIMIT','XML attribute limit exceeded');
      while(xmlSpace(text[i]))i++;
      if(text[i++]!=='=')fail('INVALID_XML','Expected attribute equals sign');
      while(xmlSpace(text[i]))i++;
      const quote=text[i++];if(quote!=='"'&&quote!=="'")fail('INVALID_XML','Attributes require quotes');
      while(i<text.length&&text[i]!==quote){
        if(text[i]==='<')fail('INVALID_XML','Raw markup in XML attribute');
        if(text[i]==='&')reference();else i++;
      }
      if(text[i++]!==quote)fail('INVALID_XML','Unterminated attribute');
      attributes.set(key,{start:attrStart,end:i});
    }
    if(!stack.length&&++roots!==1)fail('INVALID_XML','Exactly one root is required');
    const span={name:tag,start,openEnd:i,selfClosing,attributes};spans.push(span);
    if(stack.length+1>LIMITS.depth||spans.length>LIMITS.elements)fail('XML_LIMIT','XML depth/element limit exceeded');
    if(selfClosing){span.closeStart=start;span.end=i;}else stack.push(span);
  }
  if(stack.length||roots!==1)fail('INVALID_XML','Incomplete XML document');
  return spans;
}
function xmlDocument(bytes) {
  if(!(bytes instanceof Uint8Array)||bytes.length>LIMITS.fileBytes)fail('INPUT_LIMIT','Configuration must be a byte array up to4 MiB');
  let text;try{text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);}catch{fail('XML_ENCODING','Configuration must be UTF-8');}
  for(const c of text)if(!xmlChar(c.codePointAt(0)))fail('INVALID_XML','Forbidden XML character');
  const spans=lexXML(text);let document;
  try{document=new DOMParser({onError:(level,message)=>{throw Error(`${level}: ${message}`);}}).parseFromString(text.replace(/^\uFEFF/,''),'application/xml');}
  catch(e){fail('INVALID_XML',e.message);}
  if(document.documentElement?.tagName!=='data-filters')fail('INVALID_XML','A complete data-filters document is required');
  const all=Array.from(document.getElementsByTagName('*'));
  if(all.length!==spans.length)fail('INVALID_XML','Ambiguous XML token structure');
  const ranges=new Map();all.forEach((node,index)=>{
    const span=spans[index];
    if(node.tagName!==span.name||node.attributes.length!==span.attributes.size||node.namespaceURI)fail('INVALID_XML','Ambiguous XML element/attribute structure');
    ranges.set(node,span);
  });
  return {document,text,ranges,elementCount:all.length};
}

function attrs(node,allowed){
  for(const a of Array.from(node.attributes))if(!allowed.includes(a.name))
    fail('UNSUPPORTED_ATTRIBUTE',`Unsupported ${node.tagName} attribute: ${a.name}`);
}
function children(node,allowed){
  for(const n of Array.from(node.childNodes)){
    if(n.nodeType===1&&!allowed.includes(n.tagName))fail('UNSUPPORTED_STRUCTURE',`Unsupported child of ${node.tagName}`);
    if(n.nodeType===3&&n.data.trim())fail('UNSUPPORTED_STRUCTURE',`Unexpected text in ${node.tagName}`);
    if(![1,3,8].includes(n.nodeType))fail('UNSUPPORTED_STRUCTURE',`Unsupported content in ${node.tagName}`);
  }
}
function label(value,kind){
  if(typeof value!=='string'||!value||value.length>512)fail('IDENTITY',`Explicit bounded ${kind} required`);
  return value;
}
function integer(value,min,max,kind){
  if(!/^(0|[1-9]\d{0,2})$/.test(value)||Number(value)<min||Number(value)>max)
    fail('LAYOUT_INTEGER',`${kind} must be a canonical integer ${min}–${max}`);
  return Number(value);
}
function bool(node,name,otherwise){
  if(!node.hasAttribute(name))return otherwise;
  const value=node.getAttribute(name);
  if(!['true','false'].includes(value))fail('LAYOUT_BOOLEAN',`Unsupported ${name} value`);
  return value==='true';
}
function opaque(node){
  if(Array.from(node.childNodes).some(n=>n.nodeType!==3))fail('OPAQUE_STRUCTURE','Serialized values must be plain text nodes; they are never deserialized');
}
function entry(parsed,node){
  attrs(node,['objectId','anyConstraint','where','order']);
  children(node,['flatten-attribute-bindings','constraint']);
  const containers=els(node).filter(n=>n.tagName==='flatten-attribute-bindings');
  if(containers.length!==1)fail('BINDINGS','One explicit native binding list is required');
  const container=containers[0];attrs(container,[]);children(container,['attribute']);
  const bindings=new Map(),bindingNames=new Set();
  for(const n of els(container)){
    attrs(n,['attrEntryId','name','typeName','typeId','dataKind','ordinalPosition','maxLength','scale','precision','isRequired','isAutoGenerated','isPseudoAttribute','parentAttrEntryId']);children(n,[]);
    const id=label(n.getAttribute('attrEntryId'),'binding ID'),name=label(n.getAttribute('name'),'binding name');
    if(bindings.has(id)||bindingNames.has(name)||n.hasAttribute('parentAttrEntryId')||bool(n,'isPseudoAttribute',false))
      fail('BINDINGS','Only unique ordinary flat native bindings are supported');
    bindings.set(id,{node:n,name});bindingNames.add(name);
  }
  const columns=[],names=new Set(),usedBindings=new Set(),positions=new Set(),orders=new Set(),pins=new Set();
  for(const n of els(node).filter(n=>n.tagName==='constraint')){
    attrs(n,['name','attrEntryId','pos','visible','order','orderDesc','criteria','operator','entity']);children(n,['value','option']);
    const name=label(n.getAttribute('name'),'column name'),bindingId=label(n.getAttribute('attrEntryId'),'binding reference');
    if(names.has(name)||usedBindings.has(bindingId)||!bindings.has(bindingId)||bindings.get(bindingId).name!==name)fail('COLUMN_IDENTITY','Columns must have unique exact names equal to their referenced native binding names');
    names.add(name);usedBindings.add(bindingId);
    const pos=integer(n.getAttribute('pos'),0,255,'Column position'),visible=bool(n,'visible',true);
    const order=n.hasAttribute('order')?integer(n.getAttribute('order'),1,256,'Sort priority'):null;
    const orderDesc=bool(n,'orderDesc',false);
    if(order===null&&n.hasAttribute('orderDesc'))fail('SORT','Direction without an active sort priority is unsupported');
    if(positions.has(pos)||order!==null&&orders.has(order))fail('LAYOUT_COLLISION','Column positions and active sort priorities must be unique');
    positions.add(pos);if(order!==null)orders.add(order);
    const values=els(n).filter(x=>x.tagName==='value');if(values.length>1)fail('OPAQUE_STRUCTURE','At most one opaque value is supported');
    for(const value of values){attrs(value,[]);opaque(value);}
    let pin=null,pinNode=null;const optionNames=new Set();
    for(const option of els(n).filter(x=>x.tagName==='option')){
      attrs(option,['name']);opaque(option);const optionName=label(option.getAttribute('name'),'option name');
      if(optionNames.has(optionName))fail('OPTION_COLLISION','Duplicate native options are unsupported');optionNames.add(optionName);
      if(optionName==='pinned'){
        const range=parsed.ranges.get(option),raw=parsed.text.slice(range.openEnd,range.closeStart);
        pin=decodePinned(raw);pinNode=option;
        if(!visible||pins.has(pin))fail('PIN_LAYOUT','Pins must be visible and have distinct indices');pins.add(pin);
      }
    }
    columns.push({name,bindingId,bindingName:bindings.get(bindingId).name,pos,visible,order,orderDesc,pin,node:n,pinNode});
  }
  if(!columns.length||columns.length>LIMITS.columns||bindings.size!==columns.length)fail('COLUMN_LIMIT','One to256 complete native flat columns are required');
  if(!columns.some(c=>c.visible))fail('VISIBILITY','At least one column must remain visible');
  if(!columns.every((_,i)=>positions.has(i)))fail('POSITIONS','Column positions must be the complete0-based permutation');
  return {objectId:node.getAttribute('objectId'),node,columns};
}
export function inspectConfiguration(bytes){
  const parsed=xmlDocument(bytes),root=parsed.document.documentElement;attrs(root,[]);children(root,['filter']);
  const filters=new Map();
  for(const node of els(root)){
    const id=label(node.getAttribute('objectId'),'object ID');
    if(filters.has(id))fail('DUPLICATE_OBJECT','Duplicate object IDs are unsupported');filters.set(id,node);
  }
  if(!filters.size||filters.size>LIMITS.entries)fail('ENTRY_LIMIT','Configuration must contain1–512 native entries');
  return {entries:[...filters.keys()],parsed,filters};
}
function selected(inspected,id){
  if(!inspected.filters.has(id))fail('MISSING_ENTRY','Select an existing source and target entry');
  return entry(inspected.parsed,inspected.filters.get(id));
}
const publicColumn=c=>({name:c.name,position:c.pos,visible:c.visible,sortPriority:c.order,descending:c.orderDesc,pinIndex:c.pin});
function sameLayout(a,b){return a.pos===b.pos&&a.visible===b.visible&&a.order===b.order&&a.orderDesc===b.orderDesc&&a.pin===b.pin;}
export function reviewTransfer(sourceBytes,targetBytes,sourceId,targetId){
  const source=inspectConfiguration(sourceBytes),target=inspectConfiguration(targetBytes),from=selected(source,sourceId),to=selected(target,targetId);
  const desired=new Map(from.columns.map(c=>[c.name,c]));
  if(desired.size!==to.columns.length||!to.columns.every(c=>desired.has(c.name)&&desired.get(c.name).bindingName===c.bindingName))
    fail('COLUMN_MISMATCH','Source and target must have the exact same unique column and binding names');
  return {source,target,from,to,desired,review:{sourceId,targetId,columns:to.columns.map(c=>({name:c.name,before:publicColumn(c),after:publicColumn(desired.get(c.name)),changed:!sameLayout(c,desired.get(c.name))})),preserved:['target objectId','target bindings','target predicates and expressions','target opaque values and other options','all other target entries'],omitted:['source predicates','source expressions','source bindings','source opaque values and other options'],pinEncoding:'Exact finite canonical Integer0–255 whitelist; no Java deserialization'}};
}
function attrTokens(parsed,node){
  const span=parsed.ranges.get(node);
  return {span,out:span.attributes};
}

export function transferLayout(sourceBytes,targetBytes,sourceId,targetId){
  const plan=reviewTransfer(sourceBytes,targetBytes,sourceId,targetId),parsed=plan.target.parsed,patches=[];
  for(const target of plan.to.columns){
    const desired=plan.desired.get(target.name);if(sameLayout(target,desired))continue;
    const {span,out}=attrTokens(parsed,target.node);
    const fields={pos:String(desired.pos),visible:desired.visible?null:'false',order:desired.order===null?null:String(desired.order),orderDesc:desired.order===null?null:String(desired.orderDesc)};
    let added='';
    for(const [name,value] of Object.entries(fields)){
      const old=out.get(name);
      if(old){
        if(value===null)patches.push({start:old.start,end:old.end,text:''});
        else if(target.node.getAttribute(name)!==value)patches.push({start:old.start,end:old.end,text:` ${name}="${value}"`});
      }else if(value!==null)added+=` ${name}="${value}"`;
    }
    if(target.pinNode){
      const r=parsed.ranges.get(target.pinNode);
      if(desired.pin===null)patches.push({start:r.start,end:r.end,text:''});
      else if(target.pin!==desired.pin)patches.push({start:r.openEnd,end:r.closeStart,text:encodePinned(desired.pin)});
    }
    const addPin=desired.pin!==null&&!target.pinNode?`<option name="pinned">${encodePinned(desired.pin)}</option>`:'';
    if(span.selfClosing){
      const closing=span.openEnd-2;
      patches.push({start:closing,end:span.openEnd,text:added+(addPin?`>${addPin}</constraint>`:'/>')});
    }else{
      if(added)patches.push({start:span.openEnd-1,end:span.openEnd-1,text:added});
      if(addPin)patches.push({start:span.closeStart,end:span.closeStart,text:addPin});
    }
  }
  patches.sort((a,b)=>b.start-a.start||b.end-a.end);let text=parsed.text,last=text.length;
  for(const p of patches){if(p.end>last)fail('PATCH_OVERLAP','Overlapping layout edits');text=text.slice(0,p.start)+p.text+text.slice(p.end);last=p.start;}
  const bytes=new TextEncoder().encode(text);if(bytes.length>LIMITS.fileBytes)fail('OUTPUT_LIMIT','Output exceeds supported file size');
  const final=selected(inspectConfiguration(bytes),targetId);
  if(!final.columns.every(c=>sameLayout(c,plan.desired.get(c.name))))fail('PATCH_PARITY','Patched layout did not match the reviewed source');
  return {bytes,receipt:{...plan.review,changedColumns:plan.review.columns.filter(c=>c.changed).length,sourceBytes:sourceBytes.length,targetBytes:targetBytes.length,outputBytes:bytes.length,warning:'Apply a reviewed copy only while DBeaver is closed. Opaque target values are unchanged, not security-certified.'}};
}
