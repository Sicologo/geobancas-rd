#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'app'/'page.tsx'
MAP=ROOT/'components'/'GeoMap.tsx'
CSS=ROOT/'app'/'globals.css'


def replace_once(text:str,old:str,new:str,label:str)->str:
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f'{label}: esperado 1 reemplazo, encontrados {count}')
    return text.replace(old,new,1)


def regex_once(text:str,pattern:str,repl:str,label:str)->str:
    new,count=re.subn(pattern,repl,text,count=1,flags=re.S)
    if count!=1:
        raise RuntimeError(f'{label}: patrón no encontrado o ambiguo')
    return new

page=PAGE.read_text(encoding='utf-8')
geomap=MAP.read_text(encoding='utf-8')
css=CSS.read_text(encoding='utf-8')

# ---------------- page.tsx ----------------
old='''type Sim={point:{lat:number;lng:number};school?:Escuela;schoolD:number;health?:Salud;healthD:number;police?:Destacamento;policeD:number};
type SelectedBanca=Banca&{saludCercana?:Salud;saludDistanciaM:number;destacamentoCercano?:Destacamento;destacamentoDistanciaM:number;nearbyBancas:{banca:Banca;distanceM:number}[]};
type AnalysisTarget={id:string;type:"escuela"|"salud"|"destacamento"|"banca";name:string;lat:number;lng:number;color:string};'''
new='''type ProtectedDistance={layer:ProtectedLayerKey;label:string;color:string;place?:ProtectedPlace;distanceM:number};
type Sim={point:{lat:number;lng:number};school?:Escuela;schoolD:number;health?:Salud;healthD:number;police?:Destacamento;policeD:number;protected:ProtectedDistance[]};
type SelectedBanca=Banca&{saludCercana?:Salud;saludDistanciaM:number;destacamentoCercano?:Destacamento;destacamentoDistanciaM:number;nearbyBancas:{banca:Banca;distanceM:number}[];protected:ProtectedDistance[]};
type SelectedProtected={layer:ProtectedLayerKey;place:ProtectedPlace};
type AnalysisTarget={id:string;type:string;name:string;lat:number;lng:number;color:string};'''
page=replace_once(page,old,new,'tipos proximidad protegida')

old=''' const [selected,setSelected]=useState<SelectedBanca|null>(null),[selectedSchool,setSelectedSchool]=useState<Escuela|null>(null),[selectedHealth,setSelectedHealth]=useState<Salud|null>(null),[selectedPolice,setSelectedPolice]=useState<Destacamento|null>(null);const [simMode,setSimMode]=useState(false),[sim,setSim]=useState<Sim|null>(null);const [measureMode,setMeasureMode]=useState(false),[measureA,setMeasureA]=useState<Banca|null>(null),[measureB,setMeasureB]=useState<Banca|null>(null),[locationStats,setLocationStats]=useState({corrected:0,pending:0});'''
new=''' const [selected,setSelected]=useState<SelectedBanca|null>(null),[selectedSchool,setSelectedSchool]=useState<Escuela|null>(null),[selectedHealth,setSelectedHealth]=useState<Salud|null>(null),[selectedPolice,setSelectedPolice]=useState<Destacamento|null>(null),[selectedProtected,setSelectedProtected]=useState<SelectedProtected|null>(null);const [simMode,setSimMode]=useState(false),[sim,setSim]=useState<Sim|null>(null);const [measureMode,setMeasureMode]=useState(false),[measureA,setMeasureA]=useState<Banca|null>(null),[measureB,setMeasureB]=useState<Banca|null>(null),[locationStats,setLocationStats]=useState({corrected:0,pending:0});'''
page=replace_once(page,old,new,'estado selección protegida')

old=''' const toggleProtected=(key:ProtectedLayerKey)=>setProtectedVisible(prev=>({...prev,[key]:!prev[key]}));
 const filteredStats=useMemo(()=>({total:filtered.length,legal:filtered.filter(x=>x.estatus==="Legal").length,ilegal:filtered.filter(x=>x.estatus==="Ilegal").length,persons:Math.round(filtered.length*1.5),schools:countNearbyEntities(filtered,schools),health:countNearbyEntities(filtered,health),police:countNearbyEntities(filtered,police)}),[filtered,schools,health,police]);'''
new=''' const toggleProtected=(key:ProtectedLayerKey)=>setProtectedVisible(prev=>({...prev,[key]:!prev[key]}));
 const setAllProtected=(visible:boolean)=>setProtectedVisible(prev=>{const next={...prev};for(const cfg of PROTECTED_LAYER_CONFIG)next[cfg.key]=visible;return next});
 const protectedDistances=(point:{lat:number;lng:number}):ProtectedDistance[]=>PROTECTED_LAYER_CONFIG.map(cfg=>{const result=nearest(point,protectedData[cfg.key]);return {layer:cfg.key,label:cfg.title,color:cfg.color,place:result.item,distanceM:result.d}}).sort((a,b)=>a.distanceM-b.distanceM);
 const protectedNearbyTotal=useMemo(()=>PROTECTED_LAYER_CONFIG.reduce((sum,cfg)=>sum+countNearbyEntities(filtered,protectedData[cfg.key]),0),[filtered,protectedData]);
 const selectedProtectedImpact=useMemo(()=>selectedProtected?bancas.map(b=>({banca:b,distanceM:distance(selectedProtected.place,b)})).filter(x=>x.distanceM<=PROTECTED_PLACE_LIMIT).sort((a,b)=>a.distanceM-b.distanceM):[],[selectedProtected,bancas]);
 const selectedProtectedNearestBank=useMemo(()=>selectedProtected?nearest(selectedProtected.place,bancas):{item:undefined as Banca|undefined,d:Infinity},[selectedProtected,bancas]);
 const filteredStats=useMemo(()=>({total:filtered.length,legal:filtered.filter(x=>x.estatus==="Legal").length,ilegal:filtered.filter(x=>x.estatus==="Ilegal").length,persons:Math.round(filtered.length*1.5),schools:countNearbyEntities(filtered,schools),health:countNearbyEntities(filtered,health),police:countNearbyEntities(filtered,police)}),[filtered,schools,health,police]);'''
page=replace_once(page,old,new,'helpers capas protegidas')

old=''' const chooseBanca=(b:Banca)=>{if(measureMode){if(!measureA||measureB){setMeasureA(b);setMeasureB(null)}else if(measureA.id!==b.id){setMeasureB(b)}return}const school=nearest(b,escuelas),healthCenter=nearest(b,salud),policeCenter=nearest(b,destacamentos);const nearbyBancas=bancas.filter(x=>x.id!==b.id).map(x=>({banca:x,distanceM:distance(b,x)})).filter(x=>x.distanceM<LOTTERY_BANK_LIMIT).sort((a,c)=>a.distanceM-c.distanceM);setSelected({...b,escuelaCercanaCodigo:school.item?.codigo||"",escuelaCercanaNombre:school.item?.nombre||"",escuelaDistanciaM:school.d,escuelaLat:school.item?.lat||0,escuelaLng:school.item?.lng||0,saludCercana:healthCenter.item,saludDistanciaM:healthCenter.d,destacamentoCercano:policeCenter.item,destacamentoDistanciaM:policeCenter.d,nearbyBancas});setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setSim(null);setShowSchools(true);setShowHealth(true);setShowPolice(true)};
 const simulate=(point:{lat:number;lng:number})=>{const a=nearest(point,escuelas),h=nearest(point,salud),p=nearest(point,destacamentos);setSim({point,school:a.item,schoolD:a.d,health:h.item,healthD:h.d,police:p.item,policeD:p.d});setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setShowSchools(true);setShowHealth(true);setShowPolice(true)};
 const closeCards=()=>{setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setSim(null)};
 const openSchool=(x?:Escuela)=>{if(!x)return;setSelectedSchool(x);setSelected(null);setSelectedHealth(null);setSelectedPolice(null);setSim(null)};
 const openHealth=(x?:Salud)=>{if(!x)return;setSelectedHealth(x);setSelected(null);setSelectedSchool(null);setSelectedPolice(null);setSim(null)};
 const openPolice=(x?:Destacamento)=>{if(!x)return;setSelectedPolice(x);setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSim(null)};'''
new=''' const chooseBanca=(b:Banca)=>{if(measureMode){if(!measureA||measureB){setMeasureA(b);setMeasureB(null)}else if(measureA.id!==b.id){setMeasureB(b)}return}const school=nearest(b,escuelas),healthCenter=nearest(b,salud),policeCenter=nearest(b,destacamentos),protectedNear=protectedDistances(b);const nearbyBancas=bancas.filter(x=>x.id!==b.id).map(x=>({banca:x,distanceM:distance(b,x)})).filter(x=>x.distanceM<LOTTERY_BANK_LIMIT).sort((a,c)=>a.distanceM-c.distanceM);setSelected({...b,escuelaCercanaCodigo:school.item?.codigo||"",escuelaCercanaNombre:school.item?.nombre||"",escuelaDistanciaM:school.d,escuelaLat:school.item?.lat||0,escuelaLng:school.item?.lng||0,saludCercana:healthCenter.item,saludDistanciaM:healthCenter.d,destacamentoCercano:policeCenter.item,destacamentoDistanciaM:policeCenter.d,nearbyBancas,protected:protectedNear});setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setSelectedProtected(null);setSim(null);setShowSchools(true);setShowHealth(true);setShowPolice(true)};
 const simulate=(point:{lat:number;lng:number})=>{const a=nearest(point,escuelas),h=nearest(point,salud),p=nearest(point,destacamentos);setSim({point,school:a.item,schoolD:a.d,health:h.item,healthD:h.d,police:p.item,policeD:p.d,protected:protectedDistances(point)});setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setSelectedProtected(null);setShowSchools(true);setShowHealth(true);setShowPolice(true)};
 const closeCards=()=>{setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setSelectedProtected(null);setSim(null)};
 const openSchool=(x?:Escuela)=>{if(!x)return;setSelectedSchool(x);setSelected(null);setSelectedHealth(null);setSelectedPolice(null);setSelectedProtected(null);setSim(null)};
 const openHealth=(x?:Salud)=>{if(!x)return;setSelectedHealth(x);setSelected(null);setSelectedSchool(null);setSelectedPolice(null);setSelectedProtected(null);setSim(null)};
 const openPolice=(x?:Destacamento)=>{if(!x)return;setSelectedPolice(x);setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSelectedProtected(null);setSim(null)};
 const openProtected=(layer:ProtectedLayerKey,place:ProtectedPlace)=>{setSelectedProtected({layer,place});setSelected(null);setSelectedSchool(null);setSelectedHealth(null);setSelectedPolice(null);setSim(null)};'''
page=replace_once(page,old,new,'selección y simulación protegidas')

page=replace_once(page,
' const analysisOrigin=selected?{lat:selected.lat,lng:selected.lng}:sim?.point||null;',
' const analysisOrigin=selected?{lat:selected.lat,lng:selected.lng}:selectedProtected?{lat:selectedProtected.place.lat,lng:selectedProtected.place.lng}:sim?.point||null;',
'origen análisis protegido')

pattern=r''' const analysisTargets=useMemo<AnalysisTarget\[\]>\(\(\)=>\{\n  if\(selected\).*?\n  return \[\];\n \},\[selected,sim\]\);'''
repl=''' const analysisTargets=useMemo<AnalysisTarget[]>(()=>{
  if(selected){const targets:AnalysisTarget[]=[];if(selected.escuelaLat&&selected.escuelaLng)targets.push({id:selected.escuelaCercanaCodigo,type:"escuela",name:selected.escuelaCercanaNombre,lat:selected.escuelaLat,lng:selected.escuelaLng,color:"#8b5cf6"});if(selected.saludCercana)targets.push({id:selected.saludCercana.id,type:"salud",name:selected.saludCercana.nombre,lat:selected.saludCercana.lat,lng:selected.saludCercana.lng,color:"#22c9f4"});if(selected.destacamentoCercano)targets.push({id:selected.destacamentoCercano.id,type:"destacamento",name:selected.destacamentoCercano.nombre,lat:selected.destacamentoCercano.lat,lng:selected.destacamentoCercano.lng,color:"#f59e0b"});for(const x of selected.protected){if(x.place)targets.push({id:x.place.id,type:x.layer,name:x.place.nombre,lat:x.place.lat,lng:x.place.lng,color:x.color})}for(const x of selected.nearbyBancas)targets.push({id:x.banca.id,type:"banca",name:x.banca.nombre,lat:x.banca.lat,lng:x.banca.lng,color:"#ff5c73"});return targets}
  if(selectedProtected){const targets:AnalysisTarget[]=selectedProtectedImpact.slice(0,12).map(x=>({id:x.banca.id,type:"banca",name:x.banca.nombre,lat:x.banca.lat,lng:x.banca.lng,color:"#ff5c73"}));if(!targets.length&&selectedProtectedNearestBank.item)targets.push({id:selectedProtectedNearestBank.item.id,type:"banca",name:selectedProtectedNearestBank.item.nombre,lat:selectedProtectedNearestBank.item.lat,lng:selectedProtectedNearestBank.item.lng,color:"#1593e5"});return targets}
  if(sim){const targets:AnalysisTarget[]=[];if(sim.school)targets.push({id:sim.school.codigo,type:"escuela",name:sim.school.nombre,lat:sim.school.lat,lng:sim.school.lng,color:"#8b5cf6"});if(sim.health)targets.push({id:sim.health.id,type:"salud",name:sim.health.nombre,lat:sim.health.lat,lng:sim.health.lng,color:"#22c9f4"});if(sim.police)targets.push({id:sim.police.id,type:"destacamento",name:sim.police.nombre,lat:sim.police.lat,lng:sim.police.lng,color:"#f59e0b"});for(const x of sim.protected){if(x.place)targets.push({id:x.place.id,type:x.layer,name:x.place.nombre,lat:x.place.lat,lng:x.place.lng,color:x.color})}return targets}
  return [];
 },[selected,selectedProtected,selectedProtectedImpact,selectedProtectedNearestBank,sim]);'''
page=regex_once(page,pattern,repl,'líneas análisis protegidas')

page=replace_once(page,
'onSelectDestacamento={openPolice}/>',
'onSelectDestacamento={openPolice} onSelectProtected={openProtected}/>',
'callback selección protegida')

page=replace_once(page,
'<div className="layers-title">Capas territoriales</div><Layer title="Bancas de lotería"',
'<div className="layers-title">Capas territoriales</div><div className="layer-actions"><button onClick={()=>setAllProtected(true)}>Activar nuevas</button><button onClick={()=>setAllProtected(false)}>Ocultar nuevas</button></div><Layer title="Bancas de lotería"',
'acciones rápidas capas')

page=replace_once(page,
'<article><span>Destacamentos cercanos</span><strong>{filteredStats.police.toLocaleString("es-DO")}</strong></article></section>}',
'<article><span>Destacamentos cercanos</span><strong>{filteredStats.police.toLocaleString("es-DO")}</strong></article><article><span>Nuevos protegidos cercanos</span><strong>{protectedNearbyTotal.toLocaleString("es-DO")}</strong><small>registros a ≤500 m de las bancas visibles</small></article></section>}',
'estadística protegidos')

old='''<Compliance label="Cuartel o destacamento más cercano" name={selected.destacamentoCercano?.nombre||"No identificado"} meters={selected.destacamentoDistanciaM} limit={PROTECTED_PLACE_LIMIT} onClick={()=>openPolice(selected.destacamentoCercano)}/><NearbyBanks items={selected.nearbyBancas} onSelect={chooseBanca}/>'''
new='''<Compliance label="Cuartel o destacamento más cercano" name={selected.destacamentoCercano?.nombre||"No identificado"} meters={selected.destacamentoDistanciaM} limit={PROTECTED_PLACE_LIMIT} onClick={()=>openPolice(selected.destacamentoCercano)}/><section className="protected-distance-section"><div className="protected-distance-head"><span>Capas protegidas agregadas</span><strong>Distancia más cercana por categoría</strong></div>{selected.protected.map(x=>x.place&&<ProtectedCompliance key={x.layer} item={x} onClick={()=>openProtected(x.layer,x.place!)}/>)}</section><NearbyBanks items={selected.nearbyBancas} onSelect={chooseBanca}/>'''
page=replace_once(page,old,new,'distancias protegidas en banca')

marker='<Source text={policeMeta.source}/></Detail>}\n   {sim&&showDetails&&!cleanMode&&'
insert='''<Source text={policeMeta.source}/></Detail>}
   {selectedProtected&&showDetails&&!cleanMode&&<Detail title={selectedProtected.place.nombre} code={selectedProtected.place.id} onClose={()=>setSelectedProtected(null)}><span className={`protected-validation ${selectedProtected.place.validated?"validated":"pending"}`}>{selectedProtected.place.validationLabel}: {selectedProtected.place.validationValue}</span><dl><div><dt>Categoría</dt><dd>{selectedProtected.place.categoria}</dd></div><div><dt>Ubicación</dt><dd>{[selectedProtected.place.ciudad,selectedProtected.place.municipio,selectedProtected.place.provincia].filter(Boolean).join(", ")||"No especificada"}</dd></div><div><dt>Dirección</dt><dd>{selectedProtected.place.direccion||"No disponible"}</dd></div><div><dt>Teléfono</dt><dd>{selectedProtected.place.telefono||"No disponible"}</dd></div><div><dt>Coordenadas</dt><dd>{selectedProtected.place.lat.toFixed(6)}, {selectedProtected.place.lng.toFixed(6)}</dd></div><div><dt>Fuente</dt><dd>{selectedProtected.place.fuente}</dd></div></dl><ProtectedDetails place={selectedProtected.place}/><ProtectedBankImpact items={selectedProtectedImpact} nearest={selectedProtectedNearestBank} onSelect={chooseBanca}/>{selectedProtected.place.website&&<a className="data-link" href={selectedProtected.place.website} target="_blank" rel="noreferrer">Abrir sitio web ↗</a>}{selectedProtected.place.osmUrl&&<a className="data-link" href={selectedProtected.place.osmUrl} target="_blank" rel="noreferrer">Ver registro en OpenStreetMap ↗</a>}<small className="legal-note protected-legal-note">{selectedProtected.place.legalNotice||"Registro geográfico pendiente de validación institucional cuando aplique."}</small></Detail>}
   {sim&&showDetails&&!cleanMode&&'''
page=replace_once(page,marker,insert,'ficha blip protegido')

# Reemplaza la tarjeta del simulador para incluir las 9 capas adicionales.
pattern=r'''\{sim&&showDetails&&!cleanMode&&<Detail title="Análisis del local".*?</Detail>\}'''
repl='''{sim&&showDetails&&!cleanMode&&<Detail title="Análisis del local" code="SIMULADOR TERRITORIAL" onClose={()=>setSim(null)}><div className={`viability ${[sim.schoolD,sim.healthD,sim.policeD,...sim.protected.map(x=>x.distanceM)].every(x=>x>=PROTECTED_PLACE_LIMIT)?"ok":"alert"}`}><strong>{[sim.schoolD,sim.healthD,sim.policeD,...sim.protected.map(x=>x.distanceM)].every(x=>x>=PROTECTED_PLACE_LIMIT)?"Sin proximidades detectadas dentro de 500 m":"Ubicación requiere revisión"}</strong><span>Evaluación geodésica contra todas las capas disponibles. Los registros pendientes de validación se muestran como alerta de revisión, no como incumplimiento definitivo.</span></div><Compliance label="Centro educativo" name={sim.school?.nombre||"No identificado"} meters={sim.schoolD} limit={PROTECTED_PLACE_LIMIT}/><Compliance label="Centro de salud" name={sim.health?.nombre||"No identificado"} meters={sim.healthD} limit={PROTECTED_PLACE_LIMIT}/><Compliance label="Cuartel o destacamento policial" name={sim.police?.nombre||"No identificado"} meters={sim.policeD} limit={PROTECTED_PLACE_LIMIT}/><section className="protected-distance-section"><div className="protected-distance-head"><span>Capas protegidas agregadas</span><strong>9 verificaciones adicionales</strong></div>{sim.protected.map(x=>x.place&&<ProtectedCompliance key={x.layer} item={x}/>)}</section><small className="legal-note">Resultado preliminar. Requiere medición oficial, validación de coordenadas y confirmación de la condición jurídica de cada establecimiento.</small><button className="full-button" onClick={()=>setSimMode(true)}>Analizar otro punto</button></Detail>}'''
page=regex_once(page,pattern,repl,'simulador con capas protegidas')

# Componentes auxiliares y resumen regulatorio.
old='''function DistanceInfo({label,name,meters}:{label:string;name:string;meters:number}){return <div className="proximity-box"><span>{label}</span><strong>{name}</strong><div className="distance-value">{fmt(meters)}</div><small>Distancia geodésica en línea recta desde la ubicación seleccionada.</small></div>}

function MeasureBank'''
new='''function DistanceInfo({label,name,meters}:{label:string;name:string;meters:number}){return <div className="proximity-box"><span>{label}</span><strong>{name}</strong><div className="distance-value">{fmt(meters)}</div><small>Distancia geodésica en línea recta desde la ubicación seleccionada.</small></div>}
function ProtectedCompliance({item,onClick}:{item:ProtectedDistance;onClick?:()=>void}){if(!item.place)return null;const ok=item.distanceM>=PROTECTED_PLACE_LIMIT,verified=item.place.validated;const content=<><span>{item.label}</span><strong>{item.place.nombre}</strong><div className="distance-value">{fmt(item.distanceM)}</div><div className={`compliance-result ${ok?"ok":"alert"}`}><b>{ok?"Fuera de la referencia de 500 m":verified?"Dentro de 500 m":"Dentro de 500 m · requiere validación"}</b><em>{item.place.validationLabel}: {item.place.validationValue}</em><small>{ok?`Supera la referencia por ${Math.max(0,Math.floor(item.distanceM-PROTECTED_PLACE_LIMIT))} m.`:verified?`Faltan aproximadamente ${Math.ceil(PROTECTED_PLACE_LIMIT-item.distanceM)} m para la referencia.`:"La distancia es real; la condición legal del lugar todavía debe confirmarse."}</small></div>{onClick&&<small className="open-record">Ver ficha y fuente →</small>}</>;return onClick?<button type="button" className="proximity-box proximity-link protected-proximity" onClick={onClick}>{content}</button>:<div className="proximity-box protected-proximity">{content}</div>}
function ProtectedDetails({place}:{place:ProtectedPlace}){return place.details.length?<div className="protected-details">{place.details.map(x=><div key={x.label}><span>{x.label}</span><strong>{x.value}</strong></div>)}</div>:null}
function ProtectedBankImpact({items,nearest,onSelect}:{items:{banca:Banca;distanceM:number}[];nearest:{item:Banca|undefined;d:number};onSelect:(b:Banca)=>void}){return <section className={`nearby-banks ${items.length?"alert":"ok"}`}><div className="nearby-head"><div><span>Bancas dentro de 500 m</span><strong>{items.length?`${items.length} impactada${items.length===1?"":"s"}`:"Ninguna dentro de 500 m"}</strong></div><b>{items.length}</b></div>{items.slice(0,12).map(x=><button type="button" className="nearby-item nearby-link" key={x.banca.id} onClick={()=>onSelect(x.banca)}><div><strong>{x.banca.nombre}</strong><span>{x.banca.id} · {x.banca.estatus}</span></div><em>{fmt(x.distanceM)}</em></button>)}{!items.length&&nearest.item&&<button type="button" className="nearby-item nearby-link" onClick={()=>onSelect(nearest.item!)}><div><strong>Banca más cercana: {nearest.item.nombre}</strong><span>{nearest.item.id} · fuera del radio de 500 m</span></div><em>{fmt(nearest.d)}</em></button>}{items.length>12&&<small>Se muestran 12 de {items.length}; el conteo considera todas las bancas dentro de 500 m.</small>}</section>}

function MeasureBank'''
page=replace_once(page,old,new,'componentes detalle protegido')

old='''function RegulatorySummary({selected}:{selected:SelectedBanca}){const alerts=[selected.escuelaDistanciaM,selected.saludDistanciaM,selected.destacamentoDistanciaM].filter(x=>x<PROTECTED_PLACE_LIMIT).length+selected.nearbyBancas.length;return <section className={`regulatory-summary ${alerts?"alert":"ok"}`}><span>Evaluación geoespacial · Art. 26</span><strong>{alerts?`${alerts} alerta${alerts===1?"":"s"} territorial${alerts===1?"":"es"}`:"Sin alertas en las capas disponibles"}</strong><small>Referencia: 500 m respecto de lugares protegidos y 200 m entre bancas de lotería. Una banca legal preexistente puede estar alcanzada por la excepción del Art. 178; hace falta la fecha y resolución de autorización para decidirlo.</small></section>}'''
new='''function RegulatorySummary({selected}:{selected:SelectedBanca}){const coreAlerts=[selected.escuelaDistanciaM,selected.saludDistanciaM,selected.destacamentoDistanciaM].filter(x=>x<PROTECTED_PLACE_LIMIT).length,protectedAlerts=selected.protected.filter(x=>x.distanceM<PROTECTED_PLACE_LIMIT).length,bankAlerts=selected.nearbyBancas.length,alerts=coreAlerts+protectedAlerts+bankAlerts;return <section className={`regulatory-summary ${alerts?"alert":"ok"}`}><span>Evaluación geoespacial · Art. 26</span><strong>{alerts?`${alerts} alerta${alerts===1?"":"s"} geográfica${alerts===1?"":"s"}`:"Sin alertas en las capas disponibles"}</strong><small>Referencia: 500 m respecto de lugares protegidos y 200 m entre bancas de lotería. Las capas nuevas distinguen distancia geográfica de validación jurídica: un candidato pendiente no se presenta como incumplimiento definitivo hasta confirmar su condición institucional/legal.</small></section>}'''
page=replace_once(page,old,new,'resumen regulatorio ampliado')

# ---------------- GeoMap.tsx ----------------
geomap=replace_once(geomap,
'import type {ProtectedMapLayer,ProtectedPlace} from "@/lib/protected-layers";',
'import type {ProtectedLayerKey,ProtectedMapLayer,ProtectedPlace} from "@/lib/protected-layers";',
'import tipo clave protegida')
geomap=replace_once(geomap,
'type AnalysisTarget={id:string;type:"escuela"|"salud"|"destacamento"|"banca";name:string;lat:number;lng:number;color:string};',
'type AnalysisTarget={id:string;type:string;name:string;lat:number;lng:number;color:string};',
'tipo analysis target')
geomap=replace_once(geomap,
'onSelectDestacamento:(d:Destacamento)=>void;onSimulationPoint:',
'onSelectDestacamento:(d:Destacamento)=>void;onSelectProtected:(layer:ProtectedLayerKey,p:ProtectedPlace)=>void;onSimulationPoint:',
'prop onSelectProtected')

marker='''   const selectBanca=(e:MapLayerMouseEvent)=>{const id=e.features?.[0]?.properties?.id;const x=refs.current.data.find(v=>v.id===id);if(x)refs.current.onSelect(x)};map.on("click","bancas-blip",selectBanca);map.on("click","bancas-point",selectBanca);map.on("click","search-results",selectBanca);const selectEscuela=(e:MapLayerMouseEvent)=>{const id=e.features?.[0]?.properties?.codigo;const x=refs.current.escuelas.find(v=>v.codigo===id);if(x)refs.current.onSelectEscuela(x)};const selectSalud=(e:MapLayerMouseEvent)=>{const id=e.features?.[0]?.properties?.id;const x=refs.current.salud.find(v=>v.id===id);if(x)refs.current.onSelectSalud(x)};const selectDestacamento=(e:MapLayerMouseEvent)=>{const id=e.features?.[0]?.properties?.id;const x=refs.current.destacamentos.find(v=>v.id===id);if(x)refs.current.onSelectDestacamento(x)};map.on("click","escuelas-blip",selectEscuela);map.on("click","escuelas-point",selectEscuela);map.on("click","salud-blip",selectSalud);map.on("click","salud-point",selectSalud);map.on("click","destacamentos-blip",selectDestacamento);map.on("click","destacamentos-point",selectDestacamento);
'''
extra=marker+'''   refs.current.protectedLayers.forEach(layer=>{const mapId=`protected-${layer.id}`;map.on("click",`${mapId}-blip`,(e:MapLayerMouseEvent)=>{const id=e.features?.[0]?.properties?.id;const current=refs.current.protectedLayers.find(x=>x.id===layer.id);const place=current?.items.find(x=>x.id===id);if(place)refs.current.onSelectProtected(layer.id,place)})});
'''
geomap=replace_once(geomap,marker,extra,'clic blips protegidos')

# ---------------- globals.css ----------------
append='''

/* Capas protegidas: panel completo, fichas y acciones */
@media(min-width:761px){
 .control-panel{max-height:calc(100% - 32px);overflow-x:hidden;overflow-y:auto;scrollbar-width:thin}
 .control-panel .panel-head{position:sticky;top:0;z-index:3;background:rgba(8,17,29,.99)}
 .view-menu{max-height:calc(100% - 84px);overflow-y:auto;scrollbar-width:thin}
}
.layer-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:0 14px 9px}
.layer-actions button{padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--panel3);color:var(--cyan);font-size:9px;font-weight:900}
.protected-distance-section{margin:12px 0;padding-top:10px;border-top:1px solid var(--border)}
.protected-distance-head span,.protected-distance-head strong{display:block}.protected-distance-head span{color:var(--cyan);font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}.protected-distance-head strong{margin-top:4px;font-size:12px}
.protected-validation{display:inline-block;margin-bottom:12px;padding:6px 9px;border-radius:999px;font-size:10px;font-weight:900}.protected-validation.validated{background:rgba(46,204,113,.12);color:var(--success)}.protected-validation.pending{background:rgba(245,185,66,.12);color:var(--warning)}
.protected-details{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.protected-details>div{padding:9px;border:1px solid var(--border);border-radius:9px;background:var(--panel2)}.protected-details span,.protected-details strong{display:block}.protected-details span{color:var(--muted);font-size:8px;text-transform:uppercase}.protected-details strong{margin-top:4px;font-size:10px;line-height:1.35}
.data-link{display:block;margin:8px 0;padding:9px 10px;border:1px solid var(--border);border-radius:9px;background:var(--panel3);color:var(--cyan);text-decoration:none;font-size:10px;font-weight:900}.protected-legal-note{margin-top:12px;padding:10px;border-left:3px solid var(--warning);background:rgba(245,185,66,.06)}
.protected-proximity{width:100%;text-align:left}
.map-stats article small{display:block;margin-top:3px;color:var(--muted);font-size:8px;line-height:1.25}
@media(max-width:760px){.mobile-nav{grid-template-columns:repeat(5,1fr)}.protected-details{grid-template-columns:1fr}.layer-actions{position:sticky;top:67px;z-index:2;background:var(--panel);padding:5px 0}}
'''
if '/* Capas protegidas: panel completo, fichas y acciones */' not in css:
    css+=append
else:
    raise RuntimeError('CSS protegido ya estaba aplicado; abortando para evitar duplicados')

PAGE.write_text(page,encoding='utf-8')
MAP.write_text(geomap,encoding='utf-8')
CSS.write_text(css,encoding='utf-8')
print('Integración funcional completa aplicada')
