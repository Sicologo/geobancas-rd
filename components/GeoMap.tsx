"use client";
import {useEffect,useRef} from "react";
import maplibregl,{Map,MapMouseEvent} from "maplibre-gl";
import type {Banca,Escuela,Salud} from "@/lib/sample-data";

type Point={lat:number;lng:number};
type AnalysisTarget={id:string;type:"escuela"|"salud";name:string;lat:number;lng:number;color:string};
type Props={data:Banca[];escuelas:Escuela[];salud:Salud[];showBancas:boolean;showEscuelas:boolean;showSalud:boolean;showAnalysisLines:boolean;selectedId?:string;selectedEscuelaCodigo?:string;selectedSaludId?:string;simulationPoint?:Point|null;analysisOrigin?:Point|null;analysisTargets:AnalysisTarget[];onSelect:(b:Banca)=>void;onSelectEscuela:(e:Escuela)=>void;onSelectSalud:(s:Salud)=>void;onSimulationPoint:(p:Point)=>void;simulationMode:boolean};
const statusColor:Record<Banca["estatus"],string>={Legal:"#2ecc71",Ilegal:"#ff5c73",Pendiente:"#f5b942",Suspendida:"#87a4bf"};
function bancasGeoJSON(items: Banca[]): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return {
    type: "FeatureCollection",
    features: items.map((b): GeoJSON.Feature<GeoJSON.Point> => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [b.lng, b.lat] },
      properties: { ...b, color: statusColor[b.estatus] },
    })),
  };
}

function escuelasGeoJSON(items: Escuela[]): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return {
    type: "FeatureCollection",
    features: items.map((e): GeoJSON.Feature<GeoJSON.Point> => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [e.lng, e.lat] },
      properties: { ...e, color: "#8b5cf6" },
    })),
  };
}

function saludGeoJSON(items: Salud[]): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return {
    type: "FeatureCollection",
    features: items.map((s): GeoJSON.Feature<GeoJSON.Point> => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [s.lng, s.lat] },
      properties: { ...s, color: "#22c9f4" },
    })),
  };
}

function fc(
  items: Banca[] | Escuela[] | Salud[],
  kind: "banca" | "escuela" | "salud",
): GeoJSON.FeatureCollection<GeoJSON.Point> {
  if (kind === "banca") return bancasGeoJSON(items as Banca[]);
  if (kind === "escuela") return escuelasGeoJSON(items as Escuela[]);
  return saludGeoJSON(items as Salud[]);
}
const emptyLine:GeoJSON.FeatureCollection<GeoJSON.LineString>={type:"FeatureCollection",features:[]};
const emptyPoint:GeoJSON.FeatureCollection<GeoJSON.Point>={type:"FeatureCollection",features:[]};
export default function GeoMap(p:Props){
 const el=useRef<HTMLDivElement|null>(null), mapRef=useRef<Map|null>(null), refs=useRef(p); useEffect(()=>{refs.current=p},[p]);
 useEffect(()=>{if(!el.current||mapRef.current)return; const map=new maplibregl.Map({container:el.current,center:[-70.1627,18.7357],zoom:7.15,minZoom:6.6,maxZoom:19,maxBounds:[[-72.15,17.3],[-68.05,20.15]],renderWorldCopies:false,style:{version:8,glyphs:"https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",sources:{osm:{type:"raster",tiles:["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],tileSize:256,attribution:"© OpenStreetMap contributors"}},layers:[{id:"osm",type:"raster",source:"osm"}]}}); map.addControl(new maplibregl.NavigationControl({showCompass:false}),"top-right");
 map.on("load",()=>{
  const addCluster=(id:string,data:Banca[]|Escuela[]|Salud[],kind:"banca"|"escuela"|"salud",color:string,visible:boolean)=>{
   map.addSource(id,{type:"geojson",data:fc(data,kind),cluster:true,clusterMaxZoom:14,clusterRadius:id==="bancas"?46:38});
   const visibility=visible?"visible":"none";
   map.addLayer({id:`${id}-clusters`,type:"circle",source:id,filter:["has","point_count"],layout:{visibility},paint:{"circle-color":color,"circle-radius":["step",["get","point_count"],id==="bancas"?17:19,20,id==="bancas"?22:24,100,id==="bancas"?28:31],"circle-stroke-width":id==="bancas"?3:4,"circle-stroke-color":"#f8fbff","circle-opacity":.96}});
   map.addLayer({id:`${id}-count`,type:"symbol",source:id,filter:["has","point_count"],layout:{visibility,"text-field":["get","point_count_abbreviated"],"text-size":id==="bancas"?11:12,"text-font":["Open Sans Bold"],"text-allow-overlap":true},paint:{"text-color":"#fff","text-halo-color":"rgba(0,0,0,.35)","text-halo-width":1}});
   map.addLayer({id:`${id}-point`,type:"circle",source:id,filter:["!",["has","point_count"]],layout:{visibility},paint:{"circle-color":["get","color"],"circle-radius":id==="bancas"?7:9,"circle-stroke-width":id==="bancas"?3:4,"circle-stroke-color":"#fff","circle-opacity":1}});
  };
  addCluster("bancas",refs.current.data,"banca","#0c56b3",refs.current.showBancas);addCluster("escuelas",refs.current.escuelas,"escuela","#8b5cf6",refs.current.showEscuelas);addCluster("salud",refs.current.salud,"salud","#22c9f4",refs.current.showSalud);
  map.addSource("analysis-lines",{type:"geojson",data:emptyLine});map.addLayer({id:"analysis-lines",type:"line",source:"analysis-lines",paint:{"line-color":["get","color"],"line-width":3,"line-dasharray":[2,2]}});
  map.addSource("simulation",{type:"geojson",data:emptyPoint});map.addLayer({id:"simulation-ring",type:"circle",source:"simulation",paint:{"circle-radius":15,"circle-color":"rgba(12,86,179,.2)","circle-stroke-color":"#22c9f4","circle-stroke-width":4}});
  const expand=async(source:string,layer:string,e:MapMouseEvent)=>{const f=map.queryRenderedFeatures(e.point,{layers:[layer]})[0];if(!f)return;const z=await (map.getSource(source) as maplibregl.GeoJSONSource).getClusterExpansionZoom(f.properties?.cluster_id);map.easeTo({center:(f.geometry as GeoJSON.Point).coordinates as [number,number],zoom:z})};
  ["bancas","escuelas","salud"].forEach(id=>{map.on("click",`${id}-clusters`,e=>expand(id,`${id}-clusters`,e));map.on("mouseenter",`${id}-clusters`,()=>map.getCanvas().style.cursor="pointer");map.on("mouseleave",`${id}-clusters`,()=>map.getCanvas().style.cursor="")});
  map.on("click","bancas-point",e=>{const id=e.features?.[0]?.properties?.id;const x=refs.current.data.find(v=>v.id===id);if(x)refs.current.onSelect(x)});map.on("click","escuelas-point",e=>{const id=e.features?.[0]?.properties?.codigo;const x=refs.current.escuelas.find(v=>v.codigo===id);if(x)refs.current.onSelectEscuela(x)});map.on("click","salud-point",e=>{const id=e.features?.[0]?.properties?.id;const x=refs.current.salud.find(v=>v.id===id);if(x)refs.current.onSelectSalud(x)});
  map.on("click",e=>{if(refs.current.simulationMode && !(e.originalEvent.target as HTMLElement).closest(".maplibregl-marker")) refs.current.onSimulationPoint({lng:e.lngLat.lng,lat:e.lngLat.lat})});
  // Sincronización final: evita que una capa quede vacía si los datos llegaron durante la carga del estilo.
  (map.getSource("bancas") as maplibregl.GeoJSONSource).setData(bancasGeoJSON(refs.current.data));
  (map.getSource("escuelas") as maplibregl.GeoJSONSource).setData(escuelasGeoJSON(refs.current.escuelas));
  (map.getSource("salud") as maplibregl.GeoJSONSource).setData(saludGeoJSON(refs.current.salud));
 }); mapRef.current=map;return()=>{map.remove();mapRef.current=null}},[]);
 const update=(id:string,data:Banca[]|Escuela[]|Salud[],kind:"banca"|"escuela"|"salud")=>{
  const m=mapRef.current;if(!m)return;
  const apply=()=>{const source=m.getSource(id) as maplibregl.GeoJSONSource|undefined;if(source)source.setData(fc(data,kind))};
  if(m.isStyleLoaded())apply();else m.once("load",apply);
 };
 useEffect(()=>update("bancas",p.data,"banca"),[p.data]);
 useEffect(()=>update("escuelas",p.escuelas,"escuela"),[p.escuelas]);
 useEffect(()=>update("salud",p.salud,"salud"),[p.salud]);
 useEffect(()=>{
  const m=mapRef.current;if(!m)return;
  const apply=()=>{([ ["bancas",p.showBancas],["escuelas",p.showEscuelas],["salud",p.showSalud] ] as const).forEach(([id,v])=>[`${id}-clusters`,`${id}-count`,`${id}-point`].forEach(l=>{if(m.getLayer(l))m.setLayoutProperty(l,"visibility",v?"visible":"none")}))};
  if(m.isStyleLoaded())apply();else m.once("load",apply);
 },[p.showBancas,p.showEscuelas,p.showSalud]);
 useEffect(()=>{const m=mapRef.current;if(!m)return;const apply=()=>{if(m.getLayer("analysis-lines"))m.setLayoutProperty("analysis-lines","visibility",p.showAnalysisLines?"visible":"none");const origin=p.analysisOrigin;const features:GeoJSON.Feature<GeoJSON.LineString>[]=[];if(origin){for(const target of p.analysisTargets){features.push({type:"Feature",properties:{color:target.color,type:target.type,name:target.name},geometry:{type:"LineString",coordinates:[[origin.lng,origin.lat],[target.lng,target.lat]]}})}if(p.selectedId)m.flyTo({center:[origin.lng,origin.lat],zoom:Math.max(m.getZoom(),14)})}(m.getSource("analysis-lines") as maplibregl.GeoJSONSource)?.setData({type:"FeatureCollection",features})};if(m.isStyleLoaded())apply();else m.once("load",apply)},[p.analysisOrigin,p.analysisTargets,p.selectedId,p.showAnalysisLines]);
 useEffect(()=>{const m=mapRef.current;if(!m?.isStyleLoaded())return;(m.getSource("simulation") as maplibregl.GeoJSONSource)?.setData(p.simulationPoint?{type:"FeatureCollection",features:[{type:"Feature",properties:{},geometry:{type:"Point",coordinates:[p.simulationPoint.lng,p.simulationPoint.lat]}}]}:emptyPoint);if(p.simulationPoint)m.flyTo({center:[p.simulationPoint.lng,p.simulationPoint.lat],zoom:15})},[p.simulationPoint]);
 return <div ref={el} className={`map ${p.simulationMode?"simulation-cursor":""}`} aria-label="Mapa territorial de República Dominicana"/>;
}
