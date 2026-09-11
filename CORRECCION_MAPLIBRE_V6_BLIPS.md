# Corrección MapLibre v6 / blips

- Se configuró el **worker obligatorio de MapLibre GL JS v6 para Next.js**.
- `predev`, `prebuild` y `prestart` copian `maplibre-gl-worker.mjs` y `maplibre-gl-shared.mjs` a `public/maplibre`.
- `GeoMap.tsx` apunta el worker a `/maplibre/maplibre-gl-worker.mjs` antes de crear el mapa.
- Se redujo el GeoJSON enviado al worker para las 68k+ bancas, dejando solo las propiedades necesarias para pintar y seleccionar marcadores.
- Se mantiene MapLibre 6.9.0 y la capa circular de respaldo para las bancas.
- La métrica usa la terminología **Personas estimadas** (1.5 personas por banca).

Esta corrección ataca el fallo de MapLibre v6 en Next.js donde el mapa base raster puede aparecer pero las fuentes GeoJSON/clusters/blips no se procesan cuando el worker no carga.
