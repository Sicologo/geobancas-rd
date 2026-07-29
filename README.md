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
