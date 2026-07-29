# GeoBancas RD

Base profesional compatible con Vercel para el Sistema de Geolocalización y Supervisión de Bancas.

## Ejecutar localmente

```bash
npm install
npm run dev
```

Abre `http://localhost:3000`.

## Desplegar en Vercel

1. Sube este contenido al repositorio `Sicologo/geobancas-rd`.
2. Importa el repositorio desde Vercel.
3. Vercel detectará Next.js automáticamente.
4. Presiona **Deploy**.

## Estado actual

- Dashboard responsive.
- Mapa con MapLibre y OpenStreetMap.
- Búsqueda y filtros.
- API de salud en `/api/health`.
- Datos demostrativos.

## Próxima integración

- PostgreSQL + PostGIS.
- Importación real del Excel.
- Autenticación y roles.
- Auditoría e inspecciones.
- Capas de escuelas, iglesias y otros lugares.
