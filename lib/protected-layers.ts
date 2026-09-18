export type ProtectedPlaceRecord={
 id:string;
 nombre:string;
 categoria?:string;
 direccion?:string;
 ciudad?:string;
 municipio?:string;
 provincia?:string;
 telefono?:string;
 website?:string;
 lat:number;
 lon:number;
 fuente?:string;
 [key:string]:unknown;
};

export type ProtectedPlacesPayload={
 meta:{
  total:number;
  source?:string;
  categoria?:string;
  legal_notice?:string;
  [key:string]:unknown;
 };
 records:ProtectedPlaceRecord[];
};

export type ProtectedPlace={
 id:string;
 nombre:string;
 categoria:string;
 direccion:string;
 ciudad:string;
 municipio:string;
 provincia:string;
 telefono:string;
 website:string;
 lat:number;
 lng:number;
 fuente:string;
 legalNotice:string;
};

export const PROTECTED_LAYER_CONFIG=[
 {key:"colegios_privados",title:"Colegios privados",color:"#a855f7"},
 {key:"universidades",title:"Universidades",color:"#6366f1"},
 {key:"estancias_infantiles",title:"Estancias infantiles",color:"#ec4899"},
 {key:"centros_discapacidad",title:"CAID / discapacidad",color:"#14b8a6"},
 {key:"clinicas_centros_salud",title:"Clínicas / centros de salud",color:"#06b6d4"},
 {key:"iglesias_incorporadas_candidatas",title:"Iglesias incorporadas · validar",color:"#f97316"},
 {key:"cuarteles_recintos_militares",title:"Cuarteles / recintos militares",color:"#64748b"},
 {key:"sedes_poderes_estado",title:"Sedes de poderes del Estado",color:"#eab308"},
 {key:"organos_extrapoder",title:"Órganos extrapoder",color:"#ef4444"},
] as const;

export type ProtectedLayerKey=(typeof PROTECTED_LAYER_CONFIG)[number]["key"];

export type ProtectedMapLayer={
 id:ProtectedLayerKey;
 label:string;
 color:string;
 items:ProtectedPlace[];
 visible:boolean;
};

export const emptyProtectedData=()=>Object.fromEntries(PROTECTED_LAYER_CONFIG.map(x=>[x.key,[]])) as Record<ProtectedLayerKey,ProtectedPlace[]>;
export const defaultProtectedVisibility=()=>Object.fromEntries(PROTECTED_LAYER_CONFIG.map(x=>[x.key,true])) as Record<ProtectedLayerKey,boolean>;

export const expandProtectedPlace=(record:ProtectedPlaceRecord,meta?:ProtectedPlacesPayload["meta"]):ProtectedPlace=>({
 id:String(record.id||""),
 nombre:String(record.nombre||record.categoria||"Ubicación protegida"),
 categoria:String(record.categoria||meta?.categoria||"Lugar protegido"),
 direccion:String(record.direccion||""),
 ciudad:String(record.ciudad||""),
 municipio:String(record.municipio||""),
 provincia:String(record.provincia||""),
 telefono:String(record.telefono||""),
 website:String(record.website||""),
 lat:Number(record.lat),
 lng:Number(record.lon),
 fuente:String(record.fuente||meta?.source||"OpenStreetMap"),
 legalNotice:String(meta?.legal_notice||""),
});
