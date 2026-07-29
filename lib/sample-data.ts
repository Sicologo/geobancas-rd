export type Escuela = {
  codigo: string;
  nombre: string;
  sector: string;
  nivel: string;
  provincia: string;
  municipio: string;
  lat: number;
  lng: number;
  matricula: number;
  regional: string;
  distrito: string;
};

export type EscuelaCompacta = [
  codigo: string,
  nombre: string,
  sector: string,
  nivel: string,
  provincia: string,
  municipio: string,
  lat: number,
  lng: number,
  matricula: number,
  regional: string,
  distrito: string,
];

export type EscuelasPayload = {
  meta: { total: number; mapped: number; invalid: number; source: string };
  records: EscuelaCompacta[];
};

export function expandirEscuela(item: EscuelaCompacta): Escuela {
  return {
    codigo: item[0], nombre: item[1], sector: item[2], nivel: item[3],
    provincia: item[4], municipio: item[5], lat: item[6], lng: item[7],
    matricula: item[8], regional: item[9], distrito: item[10],
  };
}

export type Banca = {
  id: string;
  nombre: string;
  propietario: string;
  provincia: string;
  municipio: string;
  sector: string;
  direccion: string;
  estatus: "Legal" | "Ilegal" | "Pendiente" | "Suspendida";
  riesgo: "Bajo" | "Moderado" | "Alto";
  lat: number;
  lng: number;
  escuelaCercanaCodigo: string;
  escuelaCercanaNombre: string;
  escuelaDistanciaM: number;
  escuelaLat: number;
  escuelaLng: number;
};

export type BancaCompacta = [
  id: string,
  nombre: string,
  propietario: string,
  provincia: string,
  municipio: string,
  sector: string,
  direccion: string,
  estatus: Banca["estatus"],
  riesgo: Banca["riesgo"],
  lat: number,
  lng: number,
  escuelaCercanaCodigo: string,
  escuelaCercanaNombre: string,
  escuelaDistanciaM: number,
  escuelaLat: number,
  escuelaLng: number,
];

export type BancasPayload = {
  meta: { total: number; mapped: number; pending: number };
  records: BancaCompacta[];
};

export function expandirBanca(item: BancaCompacta): Banca {
  return {
    id: item[0], nombre: item[1], propietario: item[2], provincia: item[3],
    municipio: item[4], sector: item[5], direccion: item[6], estatus: item[7],
    riesgo: item[8], lat: item[9], lng: item[10], escuelaCercanaCodigo: item[11],
    escuelaCercanaNombre: item[12], escuelaDistanciaM: item[13], escuelaLat: item[14],
    escuelaLng: item[15],
  };
}
