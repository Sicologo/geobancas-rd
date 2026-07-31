"use client";
import {useEffect,useRef} from "react";
import maplibregl,{Map,MapMouseEvent,MapLayerMouseEvent} from "maplibre-gl";
import type {Banca,Escuela,Salud,Destacamento} from "@/lib/sample-data";

type Point={lat:number;lng:number};
type AnalysisTarget={id:string;type:"escuela"|"salud"|"destacamento"|"banca";name:string;lat:number;lng:number;color:string};
type MeasureSelection={a:Banca|null;b:Banca|null};
type Props={data:Banca[];revealFiltered:boolean;escuelas:Escuela[];salud:Salud[];destacamentos:Destacamento[];showBancas:boolean;showEscuelas:boolean;showSalud:boolean;showDestacamentos:boolean;showAnalysisLines:boolean;selectedId?:string;selectedEscuelaCodigo?:string;selectedSaludId?:string;selectedDestacamentoId?:string;simulationPoint?:Point|null;analysisOrigin?:Point|null;analysisTargets:AnalysisTarget[];measureSelection:MeasureSelection;onSelect:(b:Banca)=>void;onSelectEscuela:(e:Escuela)=>void;onSelectSalud:(s:Salud)=>void;onSelectDestacamento:(d:Destacamento)=>void;onSimulationPoint:(p:Point)=>void;simulationMode:boolean;measureMode:boolean};
const statusColor:Record<Banca["estatus"],string>={Legal:"#2ecc71",Ilegal:"#ff5c73",Pendiente:"#f5b942",Suspendida:"#87a4bf"};
const emptyLine:GeoJSON.FeatureCollection<GeoJSON.LineString>={type:"FeatureCollection",features:[]};
const emptyPoint:GeoJSON.FeatureCollection<GeoJSON.Point>={type:"FeatureCollection",features:[]};
function bancasGeoJSON(items:Banca[]):GeoJSON.FeatureCollection<GeoJSON.Point>{return{type:"FeatureCollection",features:items.map(b=>({type:"Feature",geometry:{type:"Point",coordinates:[b.lng,b.lat]},properties:{...b,color:statusColor[b.estatus]}}))}}
function escuelasGeoJSON(items:Escuela[]):GeoJSON.FeatureCollection<GeoJSON.Point>{return{type:"FeatureCollection",features:items.map(e=>({type:"Feature",geometry:{type:"Point",coordinates:[e.lng,e.lat]},properties:{...e,color:"#8b5cf6"}}))}}
function saludGeoJSON(items:Salud[]):GeoJSON.FeatureCollection<GeoJSON.Point>{return{type:"FeatureCollection",features:items.map(s=>({type:"Feature",geometry:{type:"Point",coordinates:[s.lng,s.lat]},properties:{...s,color:"#22c9f4"}}))}}
function destacamentosGeoJSON(items:Destacamento[]):GeoJSON.FeatureCollection<GeoJSON.Point>{return{type:"FeatureCollection",features:items.map(d=>({type:"Feature",geometry:{type:"Point",coordinates:[d.lng,d.lat]},properties:{...d,color:"#f59e0b"}}))}}
function fc(items:Banca[]|Escuela[]|Salud[]|Destacamento[],kind:"banca"|"escuela"|"salud"|"destacamento"){if(kind==="banca")return bancasGeoJSON(items as Banca[]);if(kind==="escuela")return escuelasGeoJSON(items as Escuela[]);if(kind==="salud")return saludGeoJSON(items as Salud[]);return destacamentosGeoJSON(items as Destacamento[])}
function makeMapIcon(kind:"school"|"health"|"police"|"banca-legal"|"banca-ilegal"|"banca-pendiente"|"banca-suspendida"):ImageData{
 const size=48,canvas=document.createElement("canvas");canvas.width=size;canvas.height=size;const c=canvas.getContext("2d");if(!c)throw new Error("Canvas no disponible");
 c.clearRect(0,0,size,size);c.lineJoin="round";c.lineCap="round";
 if(kind==="school"){
  c.fillStyle="#7c3aed";c.beginPath();c.moveTo(24,4);c.lineTo(41,14);c.lineTo(41,34);c.lineTo(24,44);c.lineTo(7,34);c.lineTo(7,14);c.closePath();c.fill();
  c.strokeStyle="#fff";c.lineWidth=3;c.beginPath();c.moveTo(13,18);c.quadraticCurveTo(19,16,23,20);c.lineTo(23,34);c.quadraticCurveTo(18,30,13,32);c.closePath();c.stroke();c.beginPath();c.moveTo(35,18);c.quadraticCurveTo(29,16,25,20);c.lineTo(25,34);c.quadraticCurveTo(30,30,35,32);c.closePath();c.stroke();
 }else if(kind==="health"){
  c.fillStyle="#06b6d4";c.fillRect(17,4,14,40);c.fillRect(4,17,40,14);
  c.strokeStyle="rgba(255,255,255,.92)";c.lineWidth=2;c.stroke();
 }else if(kind==="police"){
  c.fillStyle="#f59e0b";c.beginPath();c.moveTo(24,4);c.lineTo(40,10);c.lineTo(38,28);c.quadraticCurveTo(36,39,24,45);c.quadraticCurveTo(12,39,10,28);c.lineTo(8,10);c.closePath();c.fill();
  c.strokeStyle="#fff";c.lineWidth=3;c.beginPath();c.moveTo(24,13);c.lineTo(24,34);c.moveTo(16,22);c.lineTo(32,22);c.stroke();
 }else{
  const colors={"banca-legal":"#22c55e","banca-ilegal":"#ef4444","banca-pendiente":"#facc15","banca-suspendida":"#94a3b8"} as const;
  c.fillStyle=colors[kind];
  c.beginPath();c.moveTo(24,5);c.lineTo(41,16);c.lineTo(36,39);c.lineTo(12,39);c.lineTo(7,16);c.closePath();c.fill();
  c.strokeStyle="rgba(255,255,255,.95)";c.lineWidth=2;c.stroke();
  c.fillStyle="#fff";c.beginPath();c.arc(24,22,5,0,Math.PI*2);c.fill();
  c.strokeStyle="rgba(8,17,29,.35)";c.lineWidth=2;c.beginPath();c.moveTo(18,33);c.lineTo(30,33);c.stroke();
 }
 return c.getImageData(0,0,size,size);
}
function registerMapIcons(map:Map){
 if(!map.hasImage("geo-school"))map.addImage("geo-school",makeMapIcon("school"),{pixelRatio:2});
 if(!map.hasImage("geo-health"))map.addImage("geo-health",makeMapIcon("health"),{pixelRatio:2});
 if(!map.hasImage("geo-police"))map.addImage("geo-police",makeMapIcon("police"),{pixelRatio:2});
 if(!map.hasImage("geo-banca-legal"))map.addImage("geo-banca-legal",makeMapIcon("banca-legal"),{pixelRatio:2});
 if(!map.hasImage("geo-banca-ilegal"))map.addImage("geo-banca-ilegal",makeMapIcon("banca-ilegal"),{pixelRatio:2});
 if(!map.hasImage("geo-banca-pendiente"))map.addImage("geo-banca-pendiente",makeMapIcon("banca-pendiente"),{pixelRatio:2});
 if(!map.hasImage("geo-banca-suspendida"))map.addImage("geo-banca-suspendida",makeMapIcon("banca-suspendida"),{pixelRatio:2});
}

export default function GeoMap(p:Props){
 const el=useRef<HTMLDivElement|null>(null),mapRef=useRef<Map|null>(null),refs=useRef(p);useEffect(()=>{refs.current=p},[p]);
 useEffect(()=>{if(!el.current||mapRef.current)return;
  const map=new maplibregl.Map({container:el.current,center:[-70.1627,18.7357],zoom:7.15,minZoom:6.6,maxZoom:19,maxBounds:[[-72.15,17.3],[-68.05,20.15]],renderWorldCopies:false,style:{version:8,glyphs:"https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",sources:{carto:{type:"raster",tiles:["https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png","https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"],tileSize:512,attribution:"© OpenStreetMap © CARTO"}},layers:[{id:"carto",type:"raster",source:"carto",paint:{"raster-saturation":-.35,"raster-contrast":.04,"raster-brightness-min":.1,"raster-brightness-max":.96}}]}});
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),"top-right");
  map.on("load",()=>{
   registerMapIcons(map);
   map.addSource("bancas-heat",{type:"geojson",data:bancasGeoJSON(refs.current.data)});
   map.addLayer({id:"bancas-heat",type:"heatmap",source:"bancas-heat",maxzoom:9.6,layout:{visibility:refs.current.showBancas?"visible":"none"},paint:{"heatmap-weight":.7,"heatmap-intensity":["interpolate",["linear"],["zoom"],6.6,.45,9,1],"heatmap-radius":["interpolate",["linear"],["zoom"],6.6,9,9.5,20],"heatmap-opacity":["interpolate",["linear"],["zoom"],6.6,.42,9,.22,9.6,0],"heatmap-color":["interpolate",["linear"],["heatmap-density"],0,"rgba(12,86,179,0)",.3,"rgba(21,147,229,.28)",.6,"rgba(34,201,244,.46)",1,"rgba(12,86,179,.72)"]}});
   map.addSource("search-results",{type:"geojson",data:refs.current.revealFiltered?bancasGeoJSON(refs.current.data):emptyPoint});map.addLayer({id:"search-results",type:"symbol",source:"search-results",layout:{visibility:refs.current.revealFiltered?"visible":"none","icon-image":["match",["get","estatus"],"Legal","geo-banca-legal","Ilegal","geo-banca-ilegal","Pendiente","geo-banca-pendiente","Suspendida","geo-banca-suspendida","geo-banca-pendiente"],"icon-size":["interpolate",["linear"],["zoom"],6,.48,12,.66,18,.84],"icon-allow-overlap":true,"icon-ignore-placement":true},paint:{"icon-opacity":.98}});
   const addLayerSet=(id:string,data:Banca[]|Escuela[]|Salud[]|Destacamento[],kind:"banca"|"escuela"|"salud"|"destacamento",color:string,visible:boolean)=>{
    const isBanca=id==="bancas";
    map.addSource(id,{type:"geojson",data:fc(data,kind),cluster:true,clusterMaxZoom:isBanca?13:11,clusterRadius:isBanca?42:30});
    const visibility=visible?"visible":"none";
    const clusterMinZoom=isBanca?9:11.2;
    map.addLayer({id:`${id}-clusters`,type:"circle",source:id,minzoom:clusterMinZoom,filter:["has","point_count"],layout:{visibility},paint:{"circle-color":isBanca?"rgba(8,17,29,.88)":color,"circle-radius":isBanca?["step",["get","point_count"],10,25,13,100,16,500,20]:["step",["get","point_count"],9,20,11,75,14],"circle-stroke-width":1,"circle-stroke-color":isBanca?"rgba(34,201,244,.55)":"rgba(255,255,255,.88)","circle-opacity":.9}});
    map.addLayer({id:`${id}-count`,type:"symbol",source:id,minzoom:clusterMinZoom,filter:["has","point_count"],layout:{visibility,"text-field":["get","point_count_abbreviated"],"text-size":isBanca?9:8,"text-font":["Open Sans Bold"],"text-allow-overlap":true},paint:{"text-color":"#f8fbff"}});
    if(isBanca){
     map.addLayer({id:`${id}-point`,type:"symbol",source:id,minzoom:13.1,filter:["!",["has","point_count"]],layout:{visibility,"icon-image":["match",["get","estatus"],"Legal","geo-banca-legal","Ilegal","geo-banca-ilegal","Pendiente","geo-banca-pendiente","Suspendida","geo-banca-suspendida","geo-banca-pendiente"],"icon-size":["interpolate",["linear"],["zoom"],13.1,.42,15,.56,18,.72],"icon-allow-overlap":false,"icon-ignore-placement":false,"symbol-sort-key":2},paint:{"icon-opacity":.94}});
    }else{
     const icon=kind==="escuela"?"geo-school":kind==="salud"?"geo-health":"geo-police";
     map.addLayer({id:`${id}-point`,type:"symbol",source:id,minzoom:12.4,filter:["!",["has","point_count"]],layout:{visibility,"icon-image":icon,"icon-size":["interpolate",["linear"],["zoom"],12.4,.62,15,.78,18,.92],"icon-allow-overlap":false,"icon-ignore-placement":false,"symbol-sort-key":1}});
    }
   };
   addLayerSet("bancas",refs.current.data,"banca","#0c56b3",refs.current.showBancas);addLayerSet("escuelas",refs.current.escuelas,"escuela","#8b5cf6",refs.current.showEscuelas);addLayerSet("salud",refs.current.salud,"salud","#22c9f4",refs.current.showSalud);addLayerSet("destacamentos",refs.current.destacamentos,"destacamento","#f59e0b",refs.current.showDestacamentos);
   map.addSource("analysis-lines",{type:"geojson",data:emptyLine});map.addLayer({id:"analysis-lines",type:"line",source:"analysis-lines",paint:{"line-color":["get","color"],"line-width":2.5,"line-dasharray":[2,2]}});
   map.addSource("simulation",{type:"geojson",data:emptyPoint});map.addLayer({id:"simulation-ring",type:"circle",source:"simulation",paint:{"circle-radius":13,"circle-color":"rgba(12,86,179,.14)","circle-stroke-color":"#22c9f4","circle-stroke-width":3}});
   map.addSource("measure-line",{type:"geojson",data:emptyLine});map.addLayer({id:"measure-line",type:"line",source:"measure-line",paint:{"line-color":"#f5b942","line-width":3,"line-dasharray":[1.2,1.2]}});
   map.addSource("measure-points",{type:"geojson",data:emptyPoint});map.addLayer({id:"measure-points",type:"circle",source:"measure-points",paint:{"circle-radius":9,"circle-color":["get","color"],"circle-stroke-width":2,"circle-stroke-color":"#f8fbff"}});
   const expand=async(source:string,layer:string,e:MapMouseEvent)=>{const f=map.queryRenderedFeatures(e.point,{layers:[layer]})[0];if(!f)return;const z=await(map.getSource(source)as maplibregl.GeoJSONSource).getClusterExpansionZoom(f.properties?.cluster_id);map.easeTo({center:(f.geometry as GeoJSON.Point).coordinates as[number,number],zoom:z})};
   (["bancas","escuelas","salud","destacamentos"] as const).forEach(id=>map.on("click",`${id}-clusters`,e=>expand(id,`${id}-clusters`,e)));
   ["bancas-clusters","escuelas-clusters","salud-clusters","destacamentos-clusters","bancas-point","search-results","escuelas-point","salud-point","destacamentos-point"].forEach(id=>{map.on("mouseenter",id,()=>map.getCanvas().style.cursor="pointer");map.on("mouseleave",id,()=>map.getCanvas().style.cursor="")});
   const selectBanca=(e:MapLayerMouseEvent)=>{const id=e.features?.[0]?.properties?.id;const x=refs.current.data.find(v=>v.id===id);if(x)refs.current.onSelect(x)};map.on("click","bancas-point",selectBanca);map.on("click","search-results",selectBanca);map.on("click","escuelas-point",e=>{const id=e.features?.[0]?.properties?.codigo;const x=refs.current.escuelas.find(v=>v.codigo===id);if(x)refs.current.onSelectEscuela(x)});map.on("click","salud-point",e=>{const id=e.features?.[0]?.properties?.id;const x=refs.current.salud.find(v=>v.id===id);if(x)refs.current.onSelectSalud(x)});map.on("click","destacamentos-point",e=>{const id=e.features?.[0]?.properties?.id;const x=refs.current.destacamentos.find(v=>v.id===id);if(x)refs.current.onSelectDestacamento(x)});
   map.on("click",e=>{if(refs.current.simulationMode)refs.current.onSimulationPoint({lng:e.lngLat.lng,lat:e.lngLat.lat})});
  });mapRef.current=map;return()=>{map.remove();mapRef.current=null}},[]);
 const update=(id:string,data:Banca[]|Escuela[]|Salud[]|Destacamento[],kind:"banca"|"escuela"|"salud"|"destacamento")=>{const m=mapRef.current;if(!m)return;const apply=()=>{(m.getSource(id)as maplibregl.GeoJSONSource|undefined)?.setData(fc(data,kind));if(id==="bancas")(m.getSource("bancas-heat")as maplibregl.GeoJSONSource|undefined)?.setData(bancasGeoJSON(data as Banca[]))};if(m.isStyleLoaded())apply();else m.once("load",apply)};
 useEffect(()=>update("bancas",p.data,"banca"),[p.data]);useEffect(()=>update("escuelas",p.escuelas,"escuela"),[p.escuelas]);useEffect(()=>update("salud",p.salud,"salud"),[p.salud]);useEffect(()=>update("destacamentos",p.destacamentos,"destacamento"),[p.destacamentos]);
 useEffect(()=>{const m=mapRef.current;if(!m)return;const apply=()=>{const source=m.getSource("search-results")as maplibregl.GeoJSONSource|undefined;source?.setData(p.revealFiltered?bancasGeoJSON(p.data):emptyPoint);if(m.getLayer("search-results"))m.setLayoutProperty("search-results","visibility",p.revealFiltered?"visible":"none");if(p.revealFiltered&&p.data.length){const bounds=new maplibregl.LngLatBounds();p.data.forEach(x=>bounds.extend([x.lng,x.lat]));if(p.data.length===1)m.flyTo({center:[p.data[0].lng,p.data[0].lat],zoom:16});else m.fitBounds(bounds,{padding:100,maxZoom:15,duration:700})}};if(m.isStyleLoaded())apply();else m.once("load",apply)},[p.revealFiltered,p.data]);
 useEffect(()=>{const m=mapRef.current;if(!m)return;const apply=()=>{if(m.getLayer("bancas-heat"))m.setLayoutProperty("bancas-heat","visibility",p.showBancas?"visible":"none");([ ["bancas",p.showBancas],["escuelas",p.showEscuelas],["salud",p.showSalud],["destacamentos",p.showDestacamentos] ]as const).forEach(([id,v])=>[`${id}-clusters`,`${id}-count`,`${id}-point`].forEach(l=>{if(m.getLayer(l))m.setLayoutProperty(l,"visibility",v?"visible":"none")}))};if(m.isStyleLoaded())apply();else m.once("load",apply)},[p.showBancas,p.showEscuelas,p.showSalud,p.showDestacamentos]);
 useEffect(()=>{const m=mapRef.current;if(!m)return;const apply=()=>{if(m.getLayer("analysis-lines"))m.setLayoutProperty("analysis-lines","visibility",p.showAnalysisLines?"visible":"none");const features:GeoJSON.Feature<GeoJSON.LineString>[]=[];if(p.analysisOrigin){for(const t of p.analysisTargets)features.push({type:"Feature",properties:{color:t.color},geometry:{type:"LineString",coordinates:[[p.analysisOrigin.lng,p.analysisOrigin.lat],[t.lng,t.lat]]}});if(p.selectedId)m.flyTo({center:[p.analysisOrigin.lng,p.analysisOrigin.lat],zoom:Math.max(m.getZoom(),14)})}(m.getSource("analysis-lines")as maplibregl.GeoJSONSource)?.setData({type:"FeatureCollection",features})};if(m.isStyleLoaded())apply();else m.once("load",apply)},[p.analysisOrigin,p.analysisTargets,p.selectedId,p.showAnalysisLines]);
 useEffect(()=>{const m=mapRef.current;if(!m)return;const apply=()=>{(m.getSource("simulation")as maplibregl.GeoJSONSource)?.setData(p.simulationPoint?{type:"FeatureCollection",features:[{type:"Feature",properties:{},geometry:{type:"Point",coordinates:[p.simulationPoint.lng,p.simulationPoint.lat]}}]}:emptyPoint);if(p.simulationPoint)m.flyTo({center:[p.simulationPoint.lng,p.simulationPoint.lat],zoom:15})};if(m.isStyleLoaded())apply();else m.once("load",apply)},[p.simulationPoint]);
 useEffect(()=>{const m=mapRef.current;if(!m)return;const apply=()=>{const{a,b}=p.measureSelection;const points:GeoJSON.Feature<GeoJSON.Point>[]=[];if(a)points.push({type:"Feature",properties:{color:"#1593e5"},geometry:{type:"Point",coordinates:[a.lng,a.lat]}});if(b)points.push({type:"Feature",properties:{color:"#ff5c73"},geometry:{type:"Point",coordinates:[b.lng,b.lat]}});(m.getSource("measure-points")as maplibregl.GeoJSONSource)?.setData({type:"FeatureCollection",features:points});(m.getSource("measure-line")as maplibregl.GeoJSONSource)?.setData({type:"FeatureCollection",features:a&&b?[{type:"Feature",properties:{},geometry:{type:"LineString",coordinates:[[a.lng,a.lat],[b.lng,b.lat]]}}]:[]});if(a&&b){const bounds=new maplibregl.LngLatBounds().extend([a.lng,a.lat]).extend([b.lng,b.lat]);m.fitBounds(bounds,{padding:120,maxZoom:16,duration:700})}};if(m.isStyleLoaded())apply();else m.once("load",apply)},[p.measureSelection]);
 return <div ref={el} className={`map ${p.simulationMode||p.measureMode?"simulation-cursor":""}`} aria-label="Mapa territorial de República Dominicana"/>;
}
