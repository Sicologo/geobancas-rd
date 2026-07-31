# GeoBancas RD

Versión con líneas múltiples de proximidad.

Al seleccionar una banca, el sistema calcula y muestra simultáneamente:
- escuela más cercana (morado)
- centro de salud más cercano (cian)

La estructura `analysisTargets` permite agregar en el futuro iglesias, CAID, destacamentos y otras capas sin reescribir el motor de líneas.


## Corrección de interfaz modular

- Controles flotantes centrados para evitar solapamientos con el panel geográfico.
- Modo mapa limpio reversible: al pulsarlo nuevamente restaura paneles, líneas, estadísticas y ficha sin perder la selección.
- Líneas de proximidad de escuelas y salud conservadas.
- Visibilidad individual para bancas, escuelas, salud, líneas, estadísticas, ficha de detalle, estado inferior y panel de control.
- El botón X del panel conserva su animación y puede reabrirse desde la barra central.

## Interfaz cartográfica V2
- Buscador con botón de limpieza rápida.
- Enter oculta el panel y deja disponible el control de reapertura.
- Escuelas y salud desactivadas inicialmente.
- Escuelas y salud aparecen solo con acercamiento suficiente.
- Bancas en vista nacional mediante mapa de densidad; clusters compactos en zoom medio y puntos mínimos en zoom cercano.
- Mapa base CARTO Light para una apariencia ejecutiva.
- Indicadores superiores y panel lateral más compactos.

## Motor normativo geoespacial
Esta versión aplica referencias configuradas para el Artículo 26: 500 m respecto de las capas protegidas disponibles (centros educativos, salud y destacamentos) y 200 m entre bancas de lotería. El resultado es una alerta territorial preliminar, no una determinación jurídica definitiva. Para aplicar excepciones por preexistencia (Art. 178) se requiere incorporar fecha y resolución de autorización.
