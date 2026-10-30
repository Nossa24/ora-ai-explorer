# Ora AI — Explorador de torres

Demo interactivo (réplica del reel de referencia): pasas el cursor por un piso, aparece la tarjeta con el número de piso y la unidad, haces clic y la fachada se abre en esa losa para entrar a la residencia (maqueta 3D → sala → habitación → baño). Los Penthouses (los 2 últimos pisos de cada torre) llevan a su propio recorrido.

## Cómo verlo

```bash
cd ora-ai-explorer
node server.mjs          # → http://localhost:8768
```

Usa el servidor (`server.mjs` atiende peticiones Range, que el video necesita para saltar entre habitaciones). Abrir `index.html` con doble clic no lo he probado.

Parámetros útiles en la URL: `?tod=night` (empieza de noche), `?scan=0` (sin el recorrido automático de pisos), `?debug=1` (dibuja los polígonos de cada piso).

## Estructura

| Ruta | Qué es |
|---|---|
| `img/day.webp`, `img/night.webp` | Tus dos imágenes del edificio, ampliadas 2× (3344×1882) |
| `media/interior-residencia.mp4` | Interior de la residencia (maqueta → sala y cocina → habitación → baño) |
| `media/interior-penthouse.mp4` | Interior del penthouse (maqueta → gran sala → cocina → baño spa) |
| `js/config.js` | **Todo lo editable**: marca, textos, planos de fachada, tiempos del video, link del CTA |
| `js/app.js`, `css/style.css`, `index.html` | Lógica, estilos y estructura |
| `js/vendor/gsap.min.js` | GSAP 3.12.5 (línea de tiempo de la transición), local |

## Cosas que se cambian en `js/config.js`

- **Marca y CTA**: `brand.name`, `brand.tag`, `brand.cta.href` (pon el link de Calendly/WhatsApp; hoy es `#`).
- **Cantidad de pisos y numeración**: `towers.T1/T2` → `floors`, `base`, `pent`.
- **Calibración de pisos**: cada plano de fachada es un cuadrilátero `[arriba-izq, arriba-der, abajo-der, abajo-izq]` en píxeles de la imagen original (1672×941). Abre `?debug=1` para verlos.
- **Datos de la unidad**: `units.res` y `units.pent` (nombre, m², habitaciones, descripción).
- **Tiempos del video**: `plan.hold` (fotograma donde se detiene la maqueta y aparece el panel), `plan.resume`, y `rooms[].hold` (fotograma de cada habitación).

## Reel para redes

`video/ora-ai-reel.mp4`: 1080×1920 (9:16), 37 s, H.264 + AAC, con el mismo formato del reel de referencia (texto arriba y la pantalla de la demo al centro). Se grabó la propia demo cuadro a cuadro a 30 fps.

Música: «Gimme that Groove!» de Michael Ramir C., de Mixkit (Mixkit Stock Music Free License: uso comercial en video y redes, sin atribución obligatoria). La pista está recortada para que su entrada coincida con la primera tarjeta de piso y su golpe fuerte con el clic; está normalizada a -14 LUFS. El archivo de audio suelto no se incluye en el repo.

## Cómo se hizo el video interior

Los dos clips salen del reel de referencia, que estaba grabado con el celular frente a una laptop. Se les corrigió la perspectiva de la pantalla (cámara fija), se recortó el encabezado y la botonera de la web original, se tapó el panel de texto en inglés que venía incrustado en la maqueta (el panel que ves en la demo es HTML en español) y se re-codificó con GOP corto para que los saltos entre habitaciones sean exactos. Son 1600×874, sin audio.

Para reemplazarlos por renders propios del edificio: exporta el mismo recorrido (maqueta → 3 habitaciones), pon los nuevos MP4 en `media/` y ajusta los `hold` de `js/config.js`.
