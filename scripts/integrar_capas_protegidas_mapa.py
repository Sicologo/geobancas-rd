#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'app'/'page.tsx'
MAP=ROOT/'components'/'GeoMap.tsx'


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

if '@/lib/protected-layers' not in page:
    page=replace_once(
        page,
        'import {expandirBanca,expandirEscuela,expandirSalud,expandirDestacamento,type Banca,type BancasPayload,type Escuela,type EscuelasPayload,type Salud,type SaludPayload,type Destacamento,type DestacamentosPayload} from "@/lib/sample-data";\n',
        'import {expandirBanca,expandirEscuela,expandirSalud,expandirDestacamento,type Banca,type BancasPayload,type Escuela,type EscuelasPayload,type Salud,type SaludPayload,type Destacamento,type DestacamentosPayload} from "@/lib/sample-data";\nimport {PROTECTED_LAYER_CONFIG,defaultProtectedVisibility,emptyProtectedData,expandProtectedPlace,type ProtectedLayerKey,type ProtectedMapLayer,type ProtectedPlace,type ProtectedPlacesPayload} from "@/lib/protected-layers";\n',
        'import protected-layers',
    )

if '[protectedData,setProtectedData]' not in page:
    page=replace_once(
        page,
        ' const [query,setQuery]=useState("")',
        ' const [protectedData,setProtectedData]=useState<Record<ProtectedLayerKey,ProtectedPlace[]>>(emptyProtectedData()),[protectedVisible,setProtectedVisible]=useState<Record<ProtectedLayerKey,boolean>>(defaultProtectedVisibility());\n const [query,setQuery]=useState("")',
        'estado capas protegidas',
    )

page=page.replace('[showSchools,setShowSchools]=useState(false)','[showSchools,setShowSchools]=useState(true)',1)
page=page.replace('[showHealth,setShowHealth]=useState(false)','[showHealth,setShowHealth]=useState(true)',1)
page=page.replace('[showPolice,setShowPolice]=useState(false)','[showPolice,setShowPolice]=useState(true)',1)

if 'const protectedRequest=Promise.all(PROTECTED_LAYER_CONFIG.map' not in page:
    new_effect=''' useEffect(()=>{const json=<T,>(url:string)=>fetch(url,{cache:"force-cache"}).then(async r=>{if(!r.ok)throw new Error(`${url}: ${r.status}`);return await r.json() as T});const protectedRequest=Promise.all(PROTECTED_LAYER_CONFIG.map(x=>json<ProtectedPlacesPayload>(`/data/${x.key}.json`)));Promise.all([json<BancasPayload>("/data/bancas.json"),json<EscuelasPayload>("/data/escuelas.json"),json<SaludPayload>("/data/salud.json"),json<DestacamentosPayload>("/data/destacamentos.json"),protectedRequest]).then(([b,e,s,d,extra])=>{const repaired=repairBancaLocations(b.records.map(expandirBanca));setBancas(repaired.records);setLocationStats({corrected:repaired.corrected,pending:repaired.pending});setEscuelas(e.records.map(expandirEscuela));setSalud(s.records.map(expandirSalud));setDestacamentos(d.records.map(expandirDestacamento));const extraData=emptyProtectedData();PROTECTED_LAYER_CONFIG.forEach((cfg,i)=>{const payload=extra[i];extraData[cfg.key]=payload.records.map(r=>expandProtectedPlace(r,payload.meta)).filter(x=>Number.isFinite(x.lat)&&Number.isFinite(x.lng))});setProtectedData(extraData);setMeta(b.meta);setSchoolMeta(e.meta);setHealthMeta(s.meta);setPoliceMeta(d.meta);setLoading(false)}).catch(err=>{console.error("[GeoBancas/data]",err);setError("No fue posible cargar las capas geográficas");setLoading(false)})},[]);'''
    page=regex_once(
        page,
        r' useEffect\(\(\)=>\{const json=<T,>\(url:string\)=>fetch\(url,\{cache:"force-cache"\}\).*?\},\[\]\);',
        new_effect,
        'carga de datos',
    )

if 'const protectedMapLayers=useMemo<ProtectedMapLayer[]>' not in page:
    old=' const schools=useMemo(()=>province===ALL?escuelas:escuelas.filter(x=>x.provincia===province),[escuelas,province]), health=useMemo(()=>province===ALL?salud:salud.filter(x=>x.provincia===province),[salud,province]), police=destacamentos;'
    new=old+'\n const protectedMapLayers=useMemo<ProtectedMapLayer[]>(()=>PROTECTED_LAYER_CONFIG.map(cfg=>({id:cfg.key,label:cfg.title,color:cfg.color,items:protectedData[cfg.key],visible:protectedVisible[cfg.key]})),[protectedData,protectedVisible]);\n const toggleProtected=(key:ProtectedLayerKey)=>setProtectedVisible(prev=>({...prev,[key]:!prev[key]}));'
    page=replace_once(page,old,new,'mapas protegidos memo')

if 'protectedLayers={protectedMapLayers}' not in page:
    page=replace_once(page,'destacamentos={police} showBancas=','destacamentos={police} protectedLayers={protectedMapLayers} showBancas=','props GeoMap')

if 'PROTECTED_LAYER_CONFIG.map(cfg=><Layer key={cfg.key}' not in page:
    old='<Layer title="Destacamentos policiales" count={police.length} active={showPolice} color="police" onClick={()=>setShowPolice(v=>!v)}/>'
    new=old+'{PROTECTED_LAYER_CONFIG.map(cfg=><Layer key={cfg.key} title={cfg.title} count={protectedData[cfg.key].length} active={protectedVisible[cfg.key]} color={cfg.color} onClick={()=>toggleProtected(cfg.key)}/>)}'
    page=replace_once(page,old,new,'controles panel')

if 'PROTECTED_LAYER_CONFIG.map(cfg=><ViewToggle key={cfg.key}' not in page:
    old='<ViewToggle label="Destacamentos policiales" active={showPolice} onClick={()=>setShowPolice(v=>!v)}/>'
    new=old+'{PROTECTED_LAYER_CONFIG.map(cfg=><ViewToggle key={cfg.key} label={cfg.title} active={protectedVisible[cfg.key]} onClick={()=>toggleProtected(cfg.key)}/>)}'
    page=replace_once(page,old,new,'controles visualización')

old_layer='function Layer({title,count,active,color,onClick}:{title:string;count:number;active:boolean;color:string;onClick:()=>void}){return <div className="layer-switch"><div><i className={`layer-dot ${color}`}/><strong>{title}</strong><small>{count.toLocaleString("es-DO")} ubicaciones</small></div><button className={active?"active":""} onClick={onClick}><span/></button></div>}'
if old_layer in page:
    new_layer='function Layer({title,count,active,color,onClick}:{title:string;count:number;active:boolean;color:string;onClick:()=>void}){const custom=color.startsWith("#");return <div className="layer-switch"><div><i className={`layer-dot ${custom?"":color}`} style={custom?{background:color}:undefined}/><strong>{title}</strong><small>{count.toLocaleString("es-DO")} ubicaciones</small></div><button className={active?"active":""} onClick={onClick}><span/></button></div>}'
    page=replace_once(page,old_layer,new_layer,'Layer color dinámico')

page=page.replace('"Preparando bancas, escuelas y centros de salud…"','"Preparando bancas y todas las capas territoriales…"',1)

if '@/lib/protected-layers' not in geomap:
    geomap=replace_once(
        geomap,
        'import type {Banca,Escuela,Salud,Destacamento} from "@/lib/sample-data";\n',
        'import type {Banca,Escuela,Salud,Destacamento} from "@/lib/sample-data";\nimport type {ProtectedMapLayer,ProtectedPlace} from "@/lib/protected-layers";\n',
        'import mapa protegido',
    )

if 'protectedLayers:ProtectedMapLayer[];' not in geomap:
    geomap=replace_once(geomap,'destacamentos:Destacamento[];showBancas:','destacamentos:Destacamento[];protectedLayers:ProtectedMapLayer[];showBancas:','prop capas protegidas')

if 'function protectedGeoJSON' not in geomap:
    marker='function destacamentosGeoJSON(items:Destacamento[]):GeoJSON.FeatureCollection<GeoJSON.Point>{return{type:"FeatureCollection",features:items.map(d=>({type:"Feature",id:d.id,geometry:{type:"Point",coordinates:[d.lng,d.lat]},properties:{id:d.id,color:"#f59e0b"}}))}}\n'
    insert=marker+'function protectedGeoJSON(items:ProtectedPlace[]):GeoJSON.FeatureCollection<GeoJSON.Point>{return{type:"FeatureCollection",features:items.map(x=>({type:"Feature",id:x.id,geometry:{type:"Point",coordinates:[x.lng,x.lat]},properties:{id:x.id,nombre:x.nombre,categoria:x.categoria}}))}}\n'
    geomap=replace_once(geomap,marker,insert,'geojson protegido')

if 'const addProtectedLayerSet=(layer:ProtectedMapLayer)' not in geomap:
    marker='   addLayerSet("bancas",refs.current.data,"banca","#0c56b3",refs.current.showBancas);addLayerSet("escuelas",refs.current.escuelas,"escuela","#8b5cf6",refs.current.showEscuelas);addLayerSet("salud",refs.current.salud,"salud","#22c9f4",refs.current.showSalud);addLayerSet("destacamentos",refs.current.destacamentos,"destacamento","#f59e0b",refs.current.showDestacamentos);\n'
    extra='''   const addProtectedLayerSet=(layer:ProtectedMapLayer)=>{const id=`protected-${layer.id}`,visibility=layer.visible?"visible":"none";map.addSource(id,{type:"geojson",data:protectedGeoJSON(layer.items),cluster:true,clusterMaxZoom:11,clusterRadius:30});map.addLayer({id:`${id}-clusters`,type:"circle",source:id,minzoom:6.6,filter:["has","point_count"],layout:{visibility},paint:{"circle-color":layer.color,"circle-radius":["step",["get","point_count"],9,20,11,75,14],"circle-stroke-width":1.2,"circle-stroke-color":"rgba(255,255,255,.94)","circle-opacity":.9}});map.addLayer({id:`${id}-count`,type:"symbol",source:id,minzoom:6.6,filter:["has","point_count"],layout:{visibility,"text-field":["get","point_count_abbreviated"],"text-size":8,"text-font":["Open Sans Bold"],"text-allow-overlap":true},paint:{"text-color":"#f8fbff","text-halo-color":"rgba(8,17,29,.42)","text-halo-width":.6}});map.addLayer({id:`${id}-blip`,type:"circle",source:id,minzoom:6.6,filter:["!",["has","point_count"]],layout:{visibility},paint:{"circle-color":layer.color,"circle-radius":["interpolate",["linear"],["zoom"],6.6,2.6,11,4.2,16,6],"circle-stroke-width":["interpolate",["linear"],["zoom"],6.6,.7,14,1.25],"circle-stroke-color":"rgba(255,255,255,.95)","circle-opacity":.96}})};\n   refs.current.protectedLayers.forEach(addProtectedLayerSet);\n'''
    geomap=replace_once(geomap,marker,marker+extra,'crear capas protegidas')

if 'protectedLayers.forEach(layer=>{const id=`protected-${layer.id}`;map.on("click"' not in geomap:
    marker='   (["bancas","escuelas","salud","destacamentos"] as const).forEach(id=>map.on("click",`${id}-clusters`,e=>expand(id,`${id}-clusters`,e)));\n'
    extra='   refs.current.protectedLayers.forEach(layer=>{const id=`protected-${layer.id}`;map.on("click",`${id}-clusters`,e=>expand(id,`${id}-clusters`,e))});\n'
    geomap=replace_once(geomap,marker,marker+extra,'cluster protegidos')

if 'protectedLayers.forEach(layer=>{const id=`protected-${layer.id}`;[`${id}-clusters`,`${id}-blip`]' not in geomap:
    marker='   ["bancas-clusters","escuelas-clusters","salud-clusters","destacamentos-clusters","bancas-blip","bancas-point","search-results","escuelas-blip","escuelas-point","salud-blip","salud-point","destacamentos-blip","destacamentos-point"].forEach(id=>{map.on("mouseenter",id,()=>map.getCanvas().style.cursor="pointer");map.on("mouseleave",id,()=>map.getCanvas().style.cursor="")});\n'
    extra='   refs.current.protectedLayers.forEach(layer=>{const id=`protected-${layer.id}`;[`${id}-clusters`,`${id}-blip`].forEach(layerId=>{map.on("mouseenter",layerId,()=>map.getCanvas().style.cursor="pointer");map.on("mouseleave",layerId,()=>map.getCanvas().style.cursor="")})});\n'
    geomap=replace_once(geomap,marker,marker+extra,'cursor protegidos')

if 'useEffect(()=>{const m=mapRef.current;if(!m)return;const apply=()=>{for(const layer of p.protectedLayers)' not in geomap:
    marker=' useEffect(()=>update("bancas",p.data,"banca"),[p.data]);useEffect(()=>update("escuelas",p.escuelas,"escuela"),[p.escuelas]);useEffect(()=>update("salud",p.salud,"salud"),[p.salud]);useEffect(()=>update("destacamentos",p.destacamentos,"destacamento"),[p.destacamentos]);\n'
    extra=' useEffect(()=>{const m=mapRef.current;if(!m)return;const apply=()=>{for(const layer of p.protectedLayers){const id=`protected-${layer.id}`;(m.getSource(id)as maplibregl.GeoJSONSource|undefined)?.setData(protectedGeoJSON(layer.items));[`${id}-clusters`,`${id}-count`,`${id}-blip`].forEach(layerId=>{if(m.getLayer(layerId))m.setLayoutProperty(layerId,"visibility",layer.visible?"visible":"none")})}};if(m.isStyleLoaded())apply();else m.once("load",apply)},[p.protectedLayers]);\n'
    geomap=replace_once(geomap,marker,marker+extra,'actualizar capas protegidas')

PAGE.write_text(page,encoding='utf-8')
MAP.write_text(geomap,encoding='utf-8')
print('Integración aplicada correctamente')
