#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'app'/'page.tsx'
MAP=ROOT/'components'/'GeoMap.tsx'


def replace_once(text:str,old:str,new:str,label:str)->str:
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f'{label}: esperado 1 reemplazo, encontrados {count}')
    return text.replace(old,new,1)

page=PAGE.read_text(encoding='utf-8')
geomap=MAP.read_text(encoding='utf-8')

# 1) No montar MapLibre con arrays vacíos. Esperar a que todos los datasets estén cargados.
state_marker='[cleanMode,setCleanMode]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState("");'
if '[mapReady,setMapReady]' not in page:
    page=replace_once(page,state_marker,state_marker+'\n const [mapReady,setMapReady]=useState(false);','estado mapReady')

old_map='   <GeoMap revealFiltered={searchSubmitted&&hasActiveFilters} measureMode={measureMode} measureSelection={{a:measureA,b:measureB}} data={filtered} escuelas={schools} salud={health} destacamentos={police} protectedLayers={protectedMapLayers} showBancas={showBancas} showEscuelas={showSchools} showSalud={showHealth} showDestacamentos={showPolice} showAnalysisLines={showLines&&!cleanMode} selectedId={selected?.id} selectedEscuelaCodigo={selectedSchool?.codigo} selectedSaludId={selectedHealth?.id} selectedDestacamentoId={selectedPolice?.id} simulationMode={simMode} simulationPoint={sim?.point} analysisOrigin={analysisOrigin} analysisTargets={analysisTargets} onSimulationPoint={simulate} onSelect={chooseBanca} onSelectEscuela={openSchool} onSelectSalud={openHealth} onSelectDestacamento={openPolice} onSelectProtected={openProtected}/>'
new_map='   {!loading&&!error&&<GeoMap revealFiltered={searchSubmitted&&hasActiveFilters} measureMode={measureMode} measureSelection={{a:measureA,b:measureB}} data={filtered} escuelas={schools} salud={health} destacamentos={police} protectedLayers={protectedMapLayers} showBancas={showBancas} showEscuelas={showSchools} showSalud={showHealth} showDestacamentos={showPolice} showAnalysisLines={showLines&&!cleanMode} selectedId={selected?.id} selectedEscuelaCodigo={selectedSchool?.codigo} selectedSaludId={selectedHealth?.id} selectedDestacamentoId={selectedPolice?.id} simulationMode={simMode} simulationPoint={sim?.point} analysisOrigin={analysisOrigin} analysisTargets={analysisTargets} onSimulationPoint={simulate} onSelect={chooseBanca} onSelectEscuela={openSchool} onSelectSalud={openHealth} onSelectDestacamento={openPolice} onSelectProtected={openProtected} onReady={()=>setMapReady(true)}/>}'
if old_map in page:
    page=replace_once(page,old_map,new_map,'montaje diferido GeoMap')

old_loading='   {(loading||error)&&<div className={`data-state ${error?"error":""}`}><span className="loader"/><div><strong>{error||"Cargando plataforma territorial"}</strong><small>{error?"Revisa los archivos públicos.":"Preparando bancas y todas las capas territoriales…"}</small></div></div>}'
new_loading='   {(loading||(!loading&&!error&&!mapReady)||error)&&<div className={`data-state ${error?"error":""}`}><span className="loader"/><div><strong>{error||(!loading?"Preparando mapa territorial":"Cargando plataforma territorial")}</strong><small>{error?"Revisa los archivos públicos.":!loading?"Renderizando bancas y todos los blips…":"Preparando bancas y todas las capas territoriales…"}</small></div></div>}'
if old_loading in page:
    page=replace_once(page,old_loading,new_loading,'overlay hasta mapa listo')

# 2) GeoMap notifica cuando el primer frame completo está realmente renderizado.
old_props='onSelectDestacamento:(d:Destacamento)=>void;onSelectProtected:(layer:ProtectedLayerKey,p:ProtectedPlace)=>void;onSimulationPoint:(p:Point)=>void;simulationMode:boolean;measureMode:boolean};'
new_props='onSelectDestacamento:(d:Destacamento)=>void;onSelectProtected:(layer:ProtectedLayerKey,p:ProtectedPlace)=>void;onSimulationPoint:(p:Point)=>void;onReady?:()=>void;simulationMode:boolean;measureMode:boolean};'
if old_props in geomap:
    geomap=replace_once(geomap,old_props,new_props,'prop onReady')

# 3) Bancas siempre por encima de las nuevas capas para que nunca queden visualmente tapadas.
marker='   refs.current.protectedLayers.forEach(addProtectedLayerSet);\n'
if 'const bankTopLayers=' not in geomap:
    extra='''   const bankTopLayers=["bancas-clusters","bancas-count","bancas-blip","bancas-point","search-results"];
   for(const layerId of bankTopLayers){if(map.getLayer(layerId))map.moveLayer(layerId)}
'''
    geomap=replace_once(geomap,marker,marker+extra,'prioridad visual bancas')

# 4) No declarar el mapa listo hasta que MapLibre esté idle tras crear fuentes/capas.
ready_marker='   map.on("click",e=>{if(refs.current.simulationMode)refs.current.onSimulationPoint({lng:e.lngLat.lng,lat:e.lngLat.lat})});\n'
if 'refs.current.onReady?.()' not in geomap:
    geomap=replace_once(geomap,ready_marker,ready_marker+'   map.once("idle",()=>refs.current.onReady?.());\n','evento ready')

PAGE.write_text(page,encoding='utf-8')
MAP.write_text(geomap,encoding='utf-8')
print('Carga inicial determinista aplicada')
