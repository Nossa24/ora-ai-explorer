# Apartamento 102 · Torre 1 · Propuesta de redistribución

**Rediseño conceptual y propuesta comercial. No es planta verificada.**

El apartamento 102 se transforma de «2 alcobas + estudio» a **2 habitaciones amplias**:
- una principal con baño privado y vestier;
- una habitación 2 de 8,88 m²;
- un baño social;
- cocina abierta en U con barra-península de 2 puestos, sin comedor tradicional;
- zona de ropas en una columna integrada a la cocina, junto al acceso (redes pendientes de viabilidad);
- depósito en el antiguo cuarto de ropas;
- balcón propuesto frente a la sala, con la puerta corrediza al este.

La estética por defecto es «Monocromática elegante».

La explicación, las áreas y lo que hay que validar están en [PROPUESTA.md](PROPUESTA.md).

## Abrir

- Abre `index.html` con doble clic, o en un Mac usa `mac/Abrir Apartamento 102 propuesta.command`.
- Desde un servidor local la ruta es `/apartamento-102/`.

El visor y los modos son los mismos del apartamento 104:
- maqueta;
- recorrido de 12 capítulos con pausa y «Explorar aquí»;
- caminata con colisiones;
- puntos de información;
- acabados en vivo;
- capas.

Tiene dos capas propias:
- **Planta original del DWG:** dibuja en rojo, sobre el piso, los muros originales.
- **Solo envolvente del DWG:** oculta toda la propuesta.

## Archivos

| Archivo | Contenido |
| --- | --- |
| `data/original-102-dwg.json` | Líneas del 102 tomadas del DWG (muros, ventanas, aparatos y rótulos) en coordenadas locales |
| `tools/disenar_102.py` | Define la propuesta, calcula áreas y dibuja `capturas/00-original-vs-propuesta.png` y `capturas/01-planta-propuesta.png` |
| `data/propuesta-102.json` | Muros (con su origen: `dwg` o `propuesta`), vanos, puertas, aparatos, mobiliario, espacios y balcón |
| `tools/generar_glb.py` | Modelo 3D `modelo/apto-102-propuesta.glb`. `ARQ_Muros` es la envolvente del DWG; `PRO_Muros_interiores` son los tabiques propuestos |
| `src/app.mjs` | Visor, derivado del del 104. Usa las texturas, los acabados y el entorno de `../apartamento-104/src/` |

## Regenerar

```bash
python3 tools/disenar_102.py data/original-102-dwg.json data/propuesta-102.json capturas/01-planta-propuesta.png capturas/00-original-vs-propuesta.png
python3 tools/generar_glb.py data/propuesta-102.json modelo/apto-102-propuesta.glb
node tools/build.mjs        # requiere three 0.180.0 y esbuild, igual que el 104
```
