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
  generated_at?:string;
  [key:string]:unknown;
 };
 records:ProtectedPlaceRecord[];
};

export type ProtectedDetail={label:string;value:string};

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
 osmUrl:string;
 generatedAt:string;
 validated:boolean;
 validationLabel:string;
 validationValue:string;
 details:ProtectedDetail[];
};

export const PROTECTED_LAYER_CONFIG=[
 {key:"colegios_privados",title:"Colegios privados",color:"#a855f7",validationLabel:"Validación MINERD"},
 {key:"universidades",title:"Universidades",color:"#6366f1",validationLabel:"Reconocimiento MESCyT"},
 {key:"estancias_infantiles",title:"Estancias infantiles",color:"#ec4899",validationLabel:"Validación INAIPI"},
 {key:"centros_discapacidad",title:"CAID / discapacidad",color:"#14b8a6",validationLabel:"Validación institucional"},
 {key:"clinicas_centros_salud",title:"Clínicas / centros de salud",color:"#06b6d4",validationLabel:"Habilitación sanitaria"},
 {key:"iglesias_incorporadas_candidatas",title:"Iglesias incorporadas · validar",color:"#f97316",validationLabel:"Incorporación / registro"},
 {key:"cuarteles_recintos_militares",title:"Cuarteles / recintos militares",color:"#64748b",validationLabel:"Validación MIDE"},
 {key:"sedes_poderes_estado",title:"Sedes de poderes del Estado",color:"#eab308",validationLabel:"Validación institucional"},
 {key:"organos_extrapoder",title:"Órganos extrapoder",color:"#ef4444",validationLabel:"Validación institucional"},
] as const;

export type ProtectedLayerKey=(typeof PROTECTED_LAYER_CONFIG)[number]["key"];

export type ProtectedMapLayer={
 id:ProtectedLayerKey;
 label:string;
 color:string;
 items:ProtectedPlace[];
 visible:boolean;
};

export const emptyProtectedData=()=>{
 const data={} as Record<ProtectedLayerKey,ProtectedPlace[]>;
 for(const x of PROTECTED_LAYER_CONFIG)data[x.key]=[];
 return data;
};

export const defaultProtectedVisibility=()=>{
 const data={} as Record<ProtectedLayerKey,boolean>;
 for(const x of PROTECTED_LAYER_CONFIG)data[x.key]=true;
 return data;
};

const asText=(value:unknown)=>{
 if(value===true)return "Sí";
 if(value===false)return "No";
 if(value===null||value===undefined||value==="")return "";
 return String(value).replaceAll("_"," ");
};

const validationFields:[string,string][]=[
 ["validacion_minerd","Validación MINERD"],
 ["reconocida_mescyt","Reconocimiento MESCyT"],
 ["validacion_inaipi","Validación INAIPI"],
 ["validacion_institucional","Validación institucional"],
 ["habilitacion_sanitaria","Habilitación sanitaria"],
 ["validacion_pgr_dgii","Incorporación / registro"],
 ["validacion_mide","Validación MIDE"],
];

const detailFields:[string,string][]=[
 ["privado_confirmado_osm","Privado según etiqueta OSM"],
 ["criterio_privado","Criterio de clasificación"],
 ["red_institucional","Red institucional"],
 ["caid_candidato","Candidato CAID"],
 ["incorporacion_verificada","Incorporación verificada"],
 ["recinto_militar_validado","Recinto militar validado"],
 ["sede_principal_validada","Sede principal validada"],
 ["clasificacion_juridica","Clasificación jurídica"],
 ["religion","Religión"],
 ["denominacion","Denominación"],
];

export const expandProtectedPlace=(record:ProtectedPlaceRecord,meta?:ProtectedPlacesPayload["meta"]):ProtectedPlace=>{
 const validation=validationFields.find(([key])=>record[key]!==undefined);
 const details:ProtectedDetail[]=detailFields.flatMap(([key,label])=>{
  const value=asText(record[key]);
  return value?[{label,value}]:[];
 });
 const validated=record.validada===true||record.incorporacion_verificada===true||record.recinto_militar_validado===true||record.sede_principal_validada===true;
 return {
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
  osmUrl:String(record.osm_url||""),
  generatedAt:String(meta?.generated_at||""),
  validated,
  validationLabel:validation?.[1]||"Validación",
  validationValue:validation?asText(record[validation[0]])||(validated?"Validada":"Pendiente"):validated?"Validada":"Pendiente",
  details,
 };
};
