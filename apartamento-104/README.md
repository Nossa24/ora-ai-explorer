# Apartamento 104 · Torre 1 en 3D

Representación navegable del apartamento 104 de Pinares Ártica Home (60,01 m² rotulados).
La planta se construye a partir del DWG arquitectónico entregado.

- **Abrir:** `index.html` (funciona con doble clic y desde un servidor local), o en un Mac con
  `mac/Abrir Apartamento 104 en 3D.command`.
- **Modos:**
  - **Maqueta:** vista orbital con zoom.
  - **Recorrido:** trayectoria cinematográfica que entra por la puerta principal y cruza los vanos reales.
  - **Caminar:** primera persona a 1,60 m, con colisiones contra muros, ventanas y aparatos. Se mueve con WASD o flechas, o tocando el piso.
- **Espacios:** un punto interactivo por espacio, y la misma lista con sus áreas netas.
- **Acabados en vivo:** piso (roble, porcelanato, microcemento) y color de muros.
- **Capas:** mobiliario, cotas del plano y «solo arquitectura verificada».
- **Propuesta:** balcón de 4,01 m² en la fachada de la sala. No figura en los DWG. Se puede activar
  o desactivar, y está documentado en [MEDIDAS.md](MEDIDAS.md#propuesta-de-diseño-balcón-de-401-m²-no-figura-en-los-planos).

## Verificado frente a ilustrativo

Proviene del DWG: muros, vanos, espacios, cotas, y posición y huella de los aparatos fijos
(nodos `ARQ_*` con `extras.verificado: true`, y `APA_*`).

Es ilustrativo: alturas, losa, hojas de puerta, ventanería, acabados y todo el mobiliario
(`MOB_*` e `ILU_*`).

La relación completa de medidas está en [MEDIDAS.md](MEDIDAS.md).

## Regenerar

```bash
dwg2dxf -y -o planos.dxf PLANO_ARQUITECTONICOS_TORRES_PINARES_ARTICA_HOME.dwg   # LibreDWG
python3 tools/extraer_geometria.py planos.dxf "" data/geometria-104.json          # requiere ezdxf
python3 tools/plano_validacion.py data/geometria-104.json plano-validacion-104.png
python3 tools/generar_glb.py data/geometria-104.json modelo/apto-104.glb data/propuesta-balcon.json
npm i --no-save three@0.180.0 && node tools/build.mjs                            # requiere esbuild
```

Los DWG no se incluyen en el repositorio porque el repositorio es público.

`modelo/apto-104.glb` se escribe directamente desde Python (glTF 2.0) porque Blender no estaba
disponible en el entorno de trabajo. Se puede abrir y refinar en Blender: los nombres de nodos y
materiales son estables.
