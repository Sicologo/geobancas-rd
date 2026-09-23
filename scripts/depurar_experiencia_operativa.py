#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'app'/'page.tsx'
CSS=ROOT/'app'/'globals.css'


def replace_once(text:str,old:str,new:str,label:str)->str:
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f'{label}: esperado 1 reemplazo, encontrados {count}')
    return text.replace(old,new,1)

page=PAGE.read_text(encoding='utf-8')
css=CSS.read_text(encoding='utf-8')

# 1) Tipos operativos para expediente e inspeccion.
old='type AnalysisTarget={id:string;type:string;name:string;lat:number;lng:number;color:string};\n'
new='''type AnalysisTarget={id:string;type:string;name:string;lat:number;lng:number;color:string};
type InspectionResult="Pendiente"|"Cumple"|"Requiere revisión";
type InspectionDraft={banca:SelectedBanca;inspector:string;result:InspectionResult;notes:string};
'''
if 'type InspectionDraft=' not in page:
    page=replace_once(page,old,new,'tipos operativos')

# 2) Estados para flujos operativos.
old=' const [mapReady,setMapReady]=useState(false);\n'
new=''' const [mapReady,setMapReady]=useState(false);
 const [expediente,setExpediente]=useState<SelectedBanca|null>(null),[inspection,setInspection]=useState<InspectionDraft|null>(null),[notice,setNotice]=useState("");
'''
if '[expediente,setExpediente]' not in page:
    page=replace_once(page,old,new,'estados operativos')

# 3) Las capas nuevas solo forman parte del analisis cuando estan dentro de 500 m.
old=' const protectedDistances=(point:{lat:number;lng:number}):ProtectedDistance[]=>PROTECTED_LAYER_CONFIG.map(cfg=>{const result=nearest(point,protectedData[cfg.key]);return {layer:cfg.key,label:cfg.title,color:cfg.color,place:result.item,distanceM:result.d}}).sort((a,b)=>a.distanceM-b.distanceM);\n'
new=' const protectedDistances=(point:{lat:number;lng:number}):ProtectedDistance[]=>PROTECTED_LAYER_CONFIG.map(cfg=>{const result=nearest(point,protectedData[cfg.key]);return {layer:cfg.key,label:cfg.title,color:cfg.color,place:result.item,distanceM:result.d}}).filter(x=>x.place&&x.distanceM<=PROTECTED_PLACE_LIMIT).sort((a,b)=>a.distanceM-b.distanceM);\n'
page=replace_once(page,old,new,'filtrar protegidos a 500m')

# 4) Un lugar protegido no debe enlazar ni dibujar una banca lejana como fallback.
old=' const selectedProtectedNearestBank=useMemo(()=>selectedProtected?nearest(selectedProtected.place,bancas):{item:undefined as Banca|undefined,d:Infinity},[selectedProtected,bancas]);\n'
if old in page:
    page=page.replace(old,'',1)

# 5) Exportacion real, notificaciones y guardado local de inspecciones.
marker=' const hasActiveFilters=query.trim().length>0||province!==ALL||status!==ALL||risk!==ALL;\n'
if 'const exportVisible=' not in page:
    extra=''' const notify=(text:string)=>{setNotice(text);window.setTimeout(()=>setNotice(""),2800)};
 const exportVisible=()=>{
  const headers=["ID","Nombre","Propietario","Estatus","Riesgo","Provincia","Municipio","Sector","Dirección","Latitud","Longitud"];
  const cell=(value:unknown)=>`"${String(value??"").replaceAll('"','""')}"`;
  const rows=filtered.map(b=>[b.id,b.nombre,b.propietario,b.estatus,b.riesgo,b.provincia,b.municipio,b.sector,b.direccion,b.lat,b.lng].map(cell).join(","));
  const csv="\\ufeff"+[headers.map(cell).join(","),...rows].join("\\n");
  const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
  const a=document.createElement("a");a.href=url;a.download=`geobancas-${new Date().toISOString().slice(0,10)}.csv`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
  notify(`${filtered.length.toLocaleString("es-DO")} bancas exportadas`);
 };
 const saveInspection=()=>{
  if(!inspection||!inspection.inspector.trim())return;
  const record={id:`INSP-${Date.now()}`,bancaId:inspection.banca.id,bancaNombre:inspection.banca.nombre,inspector:inspection.inspector.trim(),result:inspection.result,notes:inspection.notes.trim(),createdAt:new Date().toISOString(),lat:inspection.banca.lat,lng:inspection.banca.lng};
  try{
   const raw=localStorage.getItem("geobancas-inspections-v1")||"[]";const parsed=JSON.parse(raw);const rows:Array<Record<string,unknown>>=Array.isArray(parsed)?parsed:[];rows.unshift(record);localStorage.setItem("geobancas-inspections-v1",JSON.stringify(rows.slice(0,500)));
  }catch(err){console.error("[GeoBancas/inspection]",err);notify("No se pudo guardar la inspección");return}
  setInspection(null);notify("Inspección guardada en este navegador");
 };
'''
    page=replace_once(page,marker,marker+extra,'acciones operativas')

# 6) Cerrar tambien los flujos operativos al cambiar de modo.
old=' const closeCards=()=>{setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setSelectedProtected(null);setSim(null)};\n'
new=' const closeCards=()=>{setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setSelectedProtected(null);setSim(null);setExpediente(null);setInspection(null)};\n'
page=replace_once(page,old,new,'cerrar flujos')

# 7) Lineas: solo proximidades regulatorias, nunca kilometros de distancia.
old='''  if(selected){const targets:AnalysisTarget[]=[];if(selected.escuelaLat&&selected.escuelaLng)targets.push({id:selected.escuelaCercanaCodigo,type:"escuela",name:selected.escuelaCercanaNombre,lat:selected.escuelaLat,lng:selected.escuelaLng,color:"#8b5cf6"});if(selected.saludCercana)targets.push({id:selected.saludCercana.id,type:"salud",name:selected.saludCercana.nombre,lat:selected.saludCercana.lat,lng:selected.saludCercana.lng,color:"#22c9f4"});if(selected.destacamentoCercano)targets.push({id:selected.destacamentoCercano.id,type:"destacamento",name:selected.destacamentoCercano.nombre,lat:selected.destacamentoCercano.lat,lng:selected.destacamentoCercano.lng,color:"#f59e0b"});for(const x of selected.protected){if(x.place)targets.push({id:x.place.id,type:x.layer,name:x.place.nombre,lat:x.place.lat,lng:x.place.lng,color:x.color})}for(const x of selected.nearbyBancas)targets.push({id:x.banca.id,type:"banca",name:x.banca.nombre,lat:x.banca.lat,lng:x.banca.lng,color:"#ff5c73"});return targets}
  if(selectedProtected){const targets:AnalysisTarget[]=selectedProtectedImpact.slice(0,12).map(x=>({id:x.banca.id,type:"banca",name:x.banca.nombre,lat:x.banca.lat,lng:x.banca.lng,color:"#ff5c73"}));if(!targets.length&&selectedProtectedNearestBank.item)targets.push({id:selectedProtectedNearestBank.item.id,type:"banca",name:selectedProtectedNearestBank.item.nombre,lat:selectedProtectedNearestBank.item.lat,lng:selectedProtectedNearestBank.item.lng,color:"#1593e5"});return targets}
  if(sim){const targets:AnalysisTarget[]=[];if(sim.school)targets.push({id:sim.school.codigo,type:"escuela",name:sim.school.nombre,lat:sim.school.lat,lng:sim.school.lng,color:"#8b5cf6"});if(sim.health)targets.push({id:sim.health.id,type:"salud",name:sim.health.nombre,lat:sim.health.lat,lng:sim.health.lng,color:"#22c9f4"});if(sim.police)targets.push({id:sim.police.id,type:"destacamento",name:sim.police.nombre,lat:sim.police.lat,lng:sim.police.lng,color:"#f59e0b"});for(const x of sim.protected){if(x.place)targets.push({id:x.place.id,type:x.layer,name:x.place.nombre,lat:x.place.lat,lng:x.place.lng,color:x.color})}return targets}
  return [];
 },[selected,selectedProtected,selectedProtectedImpact,selectedProtectedNearestBank,sim]);
'''
new='''  if(selected){const targets:AnalysisTarget[]=[];if(selected.escuelaLat&&selected.escuelaLng&&selected.escuelaDistanciaM<=PROTECTED_PLACE_LIMIT)targets.push({id:selected.escuelaCercanaCodigo,type:"escuela",name:selected.escuelaCercanaNombre,lat:selected.escuelaLat,lng:selected.escuelaLng,color:"#8b5cf6"});if(selected.saludCercana&&selected.saludDistanciaM<=PROTECTED_PLACE_LIMIT)targets.push({id:selected.saludCercana.id,type:"salud",name:selected.saludCercana.nombre,lat:selected.saludCercana.lat,lng:selected.saludCercana.lng,color:"#22c9f4"});if(selected.destacamentoCercano&&selected.destacamentoDistanciaM<=PROTECTED_PLACE_LIMIT)targets.push({id:selected.destacamentoCercano.id,type:"destacamento",name:selected.destacamentoCercano.nombre,lat:selected.destacamentoCercano.lat,lng:selected.destacamentoCercano.lng,color:"#f59e0b"});for(const x of selected.protected){if(x.place&&x.distanceM<=PROTECTED_PLACE_LIMIT)targets.push({id:x.place.id,type:x.layer,name:x.place.nombre,lat:x.place.lat,lng:x.place.lng,color:x.color})}for(const x of selected.nearbyBancas)targets.push({id:x.banca.id,type:"banca",name:x.banca.nombre,lat:x.banca.lat,lng:x.banca.lng,color:"#ff5c73"});return targets}
  if(selectedProtected)return selectedProtectedImpact.slice(0,12).map(x=>({id:x.banca.id,type:"banca",name:x.banca.nombre,lat:x.banca.lat,lng:x.banca.lng,color:"#ff5c73"}));
  if(sim){const targets:AnalysisTarget[]=[];if(sim.school&&sim.schoolD<=PROTECTED_PLACE_LIMIT)targets.push({id:sim.school.codigo,type:"escuela",name:sim.school.nombre,lat:sim.school.lat,lng:sim.school.lng,color:"#8b5cf6"});if(sim.health&&sim.healthD<=PROTECTED_PLACE_LIMIT)targets.push({id:sim.health.id,type:"salud",name:sim.health.nombre,lat:sim.health.lat,lng:sim.health.lng,color:"#22c9f4"});if(sim.police&&sim.policeD<=PROTECTED_PLACE_LIMIT)targets.push({id:sim.police.id,type:"destacamento",name:sim.police.nombre,lat:sim.police.lat,lng:sim.police.lng,color:"#f59e0b"});for(const x of sim.protected){if(x.place&&x.distanceM<=PROTECTED_PLACE_LIMIT)targets.push({id:x.place.id,type:x.layer,name:x.place.nombre,lat:x.place.lat,lng:x.place.lng,color:x.color})}return targets}
  return [];
 },[selected,selectedProtected,selectedProtectedImpact,sim]);
'''
page=replace_once(page,old,new,'lineas cercanas')

# 8) Exportar deja de ser decorativo.
old='<button className="ghost-button desktop-only">Exportar</button>'
new='<button className="ghost-button desktop-only" onClick={exportVisible} title="Exportar las bancas visibles según los filtros actuales">Exportar</button>'
page=replace_once(page,old,new,'boton exportar')

# 9) Controles flotantes con clases que permiten posicionarlos sin tapar indicadores.
old='<div className="floating-tools" role="toolbar" aria-label="Controles de visualización">'
new='<div className={`floating-tools ${panel&&!cleanMode?"with-panel":"without-panel"}`} role="toolbar" aria-label="Controles de visualización">'
page=replace_once(page,old,new,'clase controles')
old='{viewMenu&&!cleanMode&&<section className="view-menu">'
new='{viewMenu&&!cleanMode&&<section className={`view-menu ${panel?"with-panel":"without-panel"}`}> '
page=replace_once(page,old,new,'clase menu visualizacion')

# 10) Acciones de expediente e inspeccion.
old='<div className="detail-actions"><button>Ver expediente</button><button className="primary-button">Iniciar inspección</button></div>'
new='<div className="detail-actions"><button onClick={()=>setExpediente(selected)}>Ver expediente</button><button className="primary-button" onClick={()=>setInspection({banca:selected,inspector:"",result:"Pendiente",notes:""})}>Iniciar inspección</button></div>'
page=replace_once(page,old,new,'acciones ficha banca')

# 11) Lugar protegido: no mostrar banca lejana fuera del radio.
old='<ProtectedBankImpact items={selectedProtectedImpact} nearest={selectedProtectedNearestBank} onSelect={chooseBanca}/>'
new='<ProtectedBankImpact items={selectedProtectedImpact} onSelect={chooseBanca}/>'
page=replace_once(page,old,new,'impacto protegido')

# 12) Simulador: contador real y reinicio funcional.
old='<div className="protected-distance-head"><span>Capas protegidas agregadas</span><strong>9 verificaciones adicionales</strong></div>{sim.protected.map(x=>x.place&&<ProtectedCompliance key={x.layer} item={x}/>)}</section>'
new='<div className="protected-distance-head"><span>Capas protegidas agregadas</span><strong>{sim.protected.length} dentro de 500 m</strong></div>{sim.protected.map(x=>x.place&&<ProtectedCompliance key={x.layer} item={x}/>)}</section>'
page=replace_once(page,old,new,'contador simulador')
old='<button className="full-button" onClick={()=>setSimMode(true)}>Analizar otro punto</button>'
new='<button className="full-button" onClick={()=>{setSim(null);setSimMode(true)}}>Analizar otro punto</button>'
page=replace_once(page,old,new,'reinicio simulador')

# 13) Modales operativos y toast.
anchor='   <nav className="mobile-nav">'
if '<ExpedientePanel banca={expediente}' not in page:
    modal='''   {expediente&&!cleanMode&&<ExpedientePanel banca={expediente} onClose={()=>setExpediente(null)}/>}
   {inspection&&!cleanMode&&<InspectionPanel draft={inspection} onChange={setInspection} onSave={saveInspection} onClose={()=>setInspection(null)}/>}
   {notice&&<div className="app-toast" role="status">{notice}</div>}
'''
    page=replace_once(page,anchor,modal+anchor,'modales operativos')

# 14) Componentes: solo mostrar tarjetas de proximidad si realmente estan dentro del radio.
old='function Compliance({label,name,meters,limit,onClick}:{label:string;name:string;meters:number;limit:number;onClick?:()=>void}){const ok=meters>=limit;'
new='function Compliance({label,name,meters,limit,onClick}:{label:string;name:string;meters:number;limit:number;onClick?:()=>void}){if(!Number.isFinite(meters)||meters>limit)return null;const ok=meters>=limit;'
page=replace_once(page,old,new,'compliance cercano')
old='function ProtectedCompliance({item,onClick}:{item:ProtectedDistance;onClick?:()=>void}){if(!item.place)return null;const ok=item.distanceM>=PROTECTED_PLACE_LIMIT,verified=item.place.validated;'
new='function ProtectedCompliance({item,onClick}:{item:ProtectedDistance;onClick?:()=>void}){if(!item.place||item.distanceM>PROTECTED_PLACE_LIMIT)return null;const ok=item.distanceM>=PROTECTED_PLACE_LIMIT,verified=item.place.validated;'
page=replace_once(page,old,new,'protected compliance cercano')

# 15) Impacto de protegido: eliminar por completo el fallback fuera de 500 m.
old='''function ProtectedBankImpact({items,nearest,onSelect}:{items:{banca:Banca;distanceM:number}[];nearest:{item:Banca|undefined;d:number};onSelect:(b:Banca)=>void}){return <section className={`nearby-banks ${items.length?"alert":"ok"}`}><div className="nearby-head"><div><span>Bancas dentro de 500 m</span><strong>{items.length?`${items.length} impactada${items.length===1?"":"s"}`:"Ninguna dentro de 500 m"}</strong></div><b>{items.length}</b></div>{items.slice(0,12).map(x=><button type="button" className="nearby-item nearby-link" key={x.banca.id} onClick={()=>onSelect(x.banca)}><div><strong>{x.banca.nombre}</strong><span>{x.banca.id} · {x.banca.estatus}</span></div><em>{fmt(x.distanceM)}</em></button>)}{!items.length&&nearest.item&&<button type="button" className="nearby-item nearby-link" onClick={()=>onSelect(nearest.item!)}><div><strong>Banca más cercana: {nearest.item.nombre}</strong><span>{nearest.item.id} · fuera del radio de 500 m</span></div><em>{fmt(nearest.d)}</em></button>}{items.length>12&&<small>Se muestran 12 de {items.length}; el conteo considera todas las bancas dentro de 500 m.</small>}</section>}
'''
new='''function ProtectedBankImpact({items,onSelect}:{items:{banca:Banca;distanceM:number}[];onSelect:(b:Banca)=>void}){return <section className={`nearby-banks ${items.length?"alert":"ok"}`}><div className="nearby-head"><div><span>Bancas dentro de 500 m</span><strong>{items.length?`${items.length} impactada${items.length===1?"":"s"}`:"Ninguna dentro de 500 m"}</strong></div><b>{items.length}</b></div>{items.slice(0,12).map(x=><button type="button" className="nearby-item nearby-link" key={x.banca.id} onClick={()=>onSelect(x.banca)}><div><strong>{x.banca.nombre}</strong><span>{x.banca.id} · {x.banca.estatus}</span></div><em>{fmt(x.distanceM)}</em></button>)}{!items.length&&<div className="nearby-empty">No se trazan líneas ni se listan bancas fuera del radio regulatorio.</div>}{items.length>12&&<small>Se muestran 12 de {items.length}; el conteo considera todas las bancas dentro de 500 m.</small>}</section>}
'''
page=replace_once(page,old,new,'impacto solo 500m')

# 16) Agregar componentes de expediente e inspeccion antes de MeasureBank.
anchor='function MeasureBank({label,banca}:{label:"A"|"B";banca:Banca})'
if 'function ExpedientePanel(' not in page:
    components='''function ExpedientePanel({banca,onClose}:{banca:SelectedBanca;onClose:()=>void}){
 const protectedNear=banca.protected.filter(x=>x.place&&x.distanceM<=PROTECTED_PLACE_LIMIT);
 const core=[{label:"Centro educativo",name:banca.escuelaCercanaNombre,meters:banca.escuelaDistanciaM},{label:"Centro de salud",name:banca.saludCercana?.nombre||"",meters:banca.saludDistanciaM},{label:"Cuartel / destacamento",name:banca.destacamentoCercano?.nombre||"",meters:banca.destacamentoDistanciaM}].filter(x=>x.name&&x.meters<=PROTECTED_PLACE_LIMIT);
 const alerts=core.length+protectedNear.length+banca.nearbyBancas.length;
 return <div className="workflow-overlay" role="dialog" aria-modal="true" aria-label={`Expediente ${banca.id}`}><section className="workflow-dialog expediente-dialog"><div className="workflow-head"><div><span className="eyebrow">Expediente territorial</span><h2>{banca.nombre}</h2><small>{banca.id}</small></div><button onClick={onClose}>×</button></div><div className="workflow-grid"><div className="workflow-card"><span>Propietario</span><strong>{banca.propietario}</strong></div><div className="workflow-card"><span>Estatus / riesgo</span><strong>{banca.estatus} · {banca.riesgo}</strong></div><div className="workflow-card"><span>Ubicación</span><strong>{banca.sector}, {banca.municipio}, {banca.provincia}</strong></div><div className={`workflow-card ${alerts?"alert":"ok"}`}><span>Alertas geográficas</span><strong>{alerts}</strong></div></div><section className="workflow-section"><div className="workflow-section-head"><span>Lugares protegidos dentro de 500 m</span><strong>{core.length+protectedNear.length}</strong></div>{core.map(x=><div className="workflow-row" key={x.label}><div><strong>{x.label}</strong><span>{x.name}</span></div><b>{fmt(x.meters)}</b></div>)}{protectedNear.map(x=><div className="workflow-row" key={x.layer}><div><strong>{x.label}</strong><span>{x.place?.nombre}</span></div><b>{fmt(x.distanceM)}</b></div>)}{!core.length&&!protectedNear.length&&<div className="nearby-empty">Sin lugares protegidos detectados dentro de 500 m.</div>}</section><section className="workflow-section"><div className="workflow-section-head"><span>Otras bancas dentro de 200 m</span><strong>{banca.nearbyBancas.length}</strong></div>{banca.nearbyBancas.slice(0,20).map(x=><div className="workflow-row" key={x.banca.id}><div><strong>{x.banca.nombre}</strong><span>{x.banca.id} · {x.banca.estatus}</span></div><b>{fmt(x.distanceM)}</b></div>)}{!banca.nearbyBancas.length&&<div className="nearby-empty">Sin otras bancas dentro de 200 m.</div>}</section><small className="legal-note">Expediente geoespacial preliminar. La condición jurídica definitiva requiere validar la fuente institucional y, cuando corresponda, realizar medición oficial.</small><div className="workflow-actions"><button onClick={onClose}>Cerrar</button><button className="primary-button" onClick={()=>window.print()}>Imprimir expediente</button></div></section></div>
}
function InspectionPanel({draft,onChange,onSave,onClose}:{draft:InspectionDraft;onChange:(draft:InspectionDraft)=>void;onSave:()=>void;onClose:()=>void}){return <div className="workflow-overlay" role="dialog" aria-modal="true" aria-label={`Inspección ${draft.banca.id}`}><section className="workflow-dialog inspection-dialog"><div className="workflow-head"><div><span className="eyebrow">Nueva inspección</span><h2>{draft.banca.nombre}</h2><small>{draft.banca.id} · {draft.banca.direccion}</small></div><button onClick={onClose}>×</button></div><div className="inspection-form"><label><span>Inspector responsable</span><input autoFocus value={draft.inspector} onChange={e=>onChange({...draft,inspector:e.target.value})} placeholder="Nombre del inspector"/></label><label><span>Resultado preliminar</span><select value={draft.result} onChange={e=>onChange({...draft,result:e.target.value as InspectionResult})}><option>Pendiente</option><option>Cumple</option><option>Requiere revisión</option></select></label><label className="inspection-notes"><span>Notas de inspección</span><textarea value={draft.notes} onChange={e=>onChange({...draft,notes:e.target.value})} placeholder="Observaciones, documentos revisados, incidencias..." rows={6}/></label></div><div className="inspection-context"><strong>Contexto automático</strong><span>{draft.banca.nearbyBancas.length} bancas a menos de 200 m · {draft.banca.protected.length} registros protegidos nuevos a 500 m o menos.</span></div><small className="legal-note">Este registro se guarda actualmente en este navegador. Para operación multiusuario y trazabilidad institucional debe conectarse a la base de datos central.</small><div className="workflow-actions"><button onClick={onClose}>Cancelar</button><button className="primary-button" disabled={!draft.inspector.trim()} onClick={onSave}>Guardar inspección</button></div></section></div>}

'''
    page=replace_once(page,anchor,components+anchor,'componentes operativos')

# 17) CSS final: posicion estable, modales y mobile correcto.
if '/* Depuracion operativa Sep 2026 */' not in css:
    css+='''\n\n/* Depuracion operativa Sep 2026 */
@media(min-width:761px){
 .floating-tools{left:16px!important;right:auto!important;top:16px!important;transform:none!important;flex-direction:column!important;gap:7px!important}
 .floating-tools.with-panel{left:326px!important}
 .view-menu{left:70px!important;right:auto!important;top:16px!important;transform:none!important}
 .view-menu.with-panel{left:380px!important}
}
.nearby-empty{padding:12px;border:1px dashed rgba(135,164,191,.28);border-radius:10px;color:var(--muted);font-size:10px;line-height:1.45;background:rgba(13,22,36,.55)}
.workflow-overlay{position:fixed;z-index:70;inset:68px 0 0;display:grid;place-items:center;padding:24px;background:rgba(3,8,14,.72);backdrop-filter:blur(6px)}
.workflow-dialog{width:min(720px,calc(100vw - 32px));max-height:calc(100dvh - 116px);overflow:auto;padding:18px;border:1px solid var(--border);border-radius:17px;background:rgba(8,17,29,.99);box-shadow:0 28px 80px rgba(0,0,0,.58)}
.workflow-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding-bottom:14px;border-bottom:1px solid var(--border)}
.workflow-head h2{margin:5px 0 3px;font-size:22px}.workflow-head small{color:var(--muted)}
.workflow-head button{width:34px;height:34px;border:0;border-radius:9px;background:var(--panel3);color:var(--muted);font-size:22px}
.workflow-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:14px 0}
.workflow-card{padding:12px;border:1px solid var(--border);border-radius:11px;background:var(--panel2)}
.workflow-card span,.workflow-card strong{display:block}.workflow-card span{color:var(--muted);font-size:9px}.workflow-card strong{margin-top:5px;font-size:12px;line-height:1.35}
.workflow-card.alert{border-color:rgba(255,92,115,.38)}.workflow-card.alert strong{color:var(--danger)}.workflow-card.ok strong{color:var(--success)}
.workflow-section{margin:13px 0;padding:13px;border:1px solid var(--border);border-radius:12px;background:rgba(13,22,36,.62)}
.workflow-section-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}.workflow-section-head span{color:var(--cyan);font-size:9px;font-weight:900;text-transform:uppercase}.workflow-section-head strong{font-size:18px}
.workflow-row{display:flex;justify-content:space-between;gap:14px;padding:8px 0;border-top:1px solid rgba(34,201,244,.08)}.workflow-row:first-of-type{border-top:0}.workflow-row strong,.workflow-row span{display:block}.workflow-row strong{font-size:11px}.workflow-row span{margin-top:2px;color:var(--muted);font-size:9px}.workflow-row>b{white-space:nowrap;color:var(--text);font-size:12px}
.workflow-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:15px}.workflow-actions button{padding:10px 14px;border:1px solid var(--border);border-radius:9px;background:var(--panel3);color:var(--text);font-weight:800}.workflow-actions .primary-button{background:var(--primary);border-color:var(--primary)}.workflow-actions button:disabled{opacity:.45;cursor:not-allowed}
.inspection-form{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:15px}.inspection-form label{display:grid;gap:6px}.inspection-form label>span{color:var(--muted);font-size:9px;font-weight:800}.inspection-form input,.inspection-form select,.inspection-form textarea{width:100%;padding:10px 11px;border:1px solid var(--border);border-radius:9px;outline:0;background:var(--panel2);color:var(--text)}.inspection-form input:focus,.inspection-form select:focus,.inspection-form textarea:focus{border-color:var(--cyan)}.inspection-notes{grid-column:1/-1}.inspection-form textarea{resize:vertical;min-height:120px}.inspection-context{margin-top:12px;padding:11px;border:1px solid var(--border);border-radius:10px;background:var(--panel2)}.inspection-context strong,.inspection-context span{display:block}.inspection-context span{margin-top:4px;color:var(--muted);font-size:10px}
.app-toast{position:fixed;z-index:90;left:50%;bottom:24px;transform:translateX(-50%);padding:10px 14px;border:1px solid rgba(46,204,113,.38);border-radius:999px;background:rgba(8,17,29,.97);color:var(--success);box-shadow:0 14px 38px rgba(0,0,0,.4);font-size:11px;font-weight:800}
@media(max-width:760px){
 .mobile-nav{grid-template-columns:repeat(5,1fr)!important}
 .workflow-overlay{inset:58px 0 62px;padding:10px;align-items:end}.workflow-dialog{width:100%;max-height:78dvh;border-radius:18px 18px 0 0}.workflow-grid,.inspection-form{grid-template-columns:1fr}.inspection-notes{grid-column:auto}.floating-tools{left:50%!important;top:10px!important;transform:translateX(-50%)!important;flex-direction:row!important}.view-menu{left:10px!important;right:10px!important;top:auto!important;bottom:72px!important;transform:none!important}.app-toast{bottom:76px;max-width:calc(100vw - 24px);text-align:center}
}
@media print{
 body *{visibility:hidden!important}.workflow-overlay,.workflow-overlay *{visibility:visible!important}.workflow-overlay{position:fixed;inset:0;background:#fff!important;color:#111!important;padding:0}.workflow-dialog{width:100%;max-height:none;box-shadow:none;border:0;background:#fff!important;color:#111!important}.workflow-actions,.workflow-head button{display:none!important}.workflow-card,.workflow-section{background:#fff!important;color:#111!important;border-color:#bbb!important}.workflow-row span,.workflow-card span,.legal-note{color:#555!important}
}
'''

PAGE.write_text(page,encoding='utf-8')
CSS.write_text(css,encoding='utf-8')
print('Depuracion operativa aplicada')
