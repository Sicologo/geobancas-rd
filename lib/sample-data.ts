export type Escuela={codigo:string;nombre:string;sector:string;nivel:string;provincia:string;municipio:string;lat:number;lng:number;matricula:number;regional:string;distrito:string};
export type EscuelaCompacta=[string,string,string,string,string,string,number,number,number,string,string];
export type EscuelasPayload={meta:{total:number;mapped:number;invalid:number;source:string};records:EscuelaCompacta[]};
export const expandirEscuela=(i:EscuelaCompacta):Escuela=>({codigo:i[0],nombre:i[1],sector:i[2],nivel:i[3],provincia:i[4],municipio:i[5],lat:i[6],lng:i[7],matricula:i[8],regional:i[9],distrito:i[10]});

export type Salud={id:string;nombre:string;tipo:string;direccion:string;estado:string;nivel:string;regional:string;provincia:string;municipio:string;barrio:string;lat:number;lng:number};
export type SaludCompacta=[string,string,string,string,string,string,string,string,string,string,number,number];
export type SaludPayload={meta:{total:number;mapped:number;invalid:number;source:string};records:SaludCompacta[]};
export const expandirSalud=(i:SaludCompacta):Salud=>({id:i[0],nombre:i[1],tipo:i[2],direccion:i[3],estado:i[4],nivel:i[5],regional:i[6],provincia:i[7],municipio:i[8],barrio:i[9],lat:i[10],lng:i[11]});

export type Banca={id:string;nombre:string;propietario:string;provincia:string;municipio:string;sector:string;direccion:string;estatus:"Legal"|"Ilegal"|"Pendiente"|"Suspendida";riesgo:"Bajo"|"Moderado"|"Alto";lat:number;lng:number;escuelaCercanaCodigo:string;escuelaCercanaNombre:string;escuelaDistanciaM:number;escuelaLat:number;escuelaLng:number};
export type BancaCompacta=[string,string,string,string,string,string,string,Banca["estatus"],Banca["riesgo"],number,number,string,string,number,number,number];
export type BancasPayload={meta:{total:number;mapped:number;pending:number};records:BancaCompacta[]};
export const expandirBanca=(i:BancaCompacta):Banca=>({id:i[0],nombre:i[1],propietario:i[2],provincia:i[3],municipio:i[4],sector:i[5],direccion:i[6],estatus:i[7],riesgo:i[8],lat:i[9],lng:i[10],escuelaCercanaCodigo:i[11],escuelaCercanaNombre:i[12],escuelaDistanciaM:i[13],escuelaLat:i[14],escuelaLng:i[15]});
