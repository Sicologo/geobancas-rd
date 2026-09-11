# Actualización GeoBancas RD

## Cambios
- Se eliminó la dependencia visual de CARTO que mostraba `API KEY REQUIRED`.
- El mapa base usa OpenStreetMap directamente mediante MapLibre, sin API key.
- El selector de provincia ahora muestra la cantidad de bancas por provincia.
- `Todos` muestra el total nacional.
- Se agregó el indicador `Empleos estimados` al dashboard.
- Fórmula: bancas del filtro actual × 1.5 empleados, redondeado a persona completa.
- El cálculo cambia automáticamente por provincia, búsqueda, estatus y riesgo.
- El pie del panel también muestra bancas y empleo estimado del filtro actual.
