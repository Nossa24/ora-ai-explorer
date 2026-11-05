# Propuesta de redistribución – apto 102 · Torre 1 · Pinares Ártica Home

> **Rediseño conceptual / propuesta comercial. No es planta verificada ni aprobada del proyecto.**
> Parte del apartamento 102 del DWG (`PLANTA PISO 1 AL PISO 20 · TORRE 1`, rotulado 60,42 m²), pero la
> distribución interior es nueva.

![Original frente a propuesta](capturas/00-original-vs-propuesta.png)

## Qué se conserva del DWG y qué cambia

| Se conserva (DWG) | Cambia (propuesta) |
| --- | --- |
| Envolvente de 8,074 × 7,60 m: medianeros, muro del corredor y fachada | Todos los tabiques interiores |
| Vanos de fachada: ventana de 2,449 m de la sala y dos ventanas de 1,00 m | Cocina, baños, zona de ropas y puertas interiores |
| Puerta de acceso P2 de 1,00 m, en la misma esquina | Se elimina el estudio |
| Los dos ductos verticales del núcleo húmedo | Balcón de 4,04 m² frente a la sala (propuesta, como en el 104) |

## Nueva distribución

| Espacio | Área neta | Qué tiene |
| --- | --- | --- |
| Sala · comedor · cocina | 19,10 m² | Espacio abierto de 7,30 m de fondo. La sala da al balcón; comedor para cuatro; cocina en L con mesón oeste (lavaplatos) y mesón norte (estufa y horno), más nevera de columna |
| Habitación principal | 11,39 m² | Cama de 1,60 m, mesas de noche, butaca junto a la ventana |
| Baño principal (privado) | 4,70 m² | Ducha de 1,78 m con mampara, doble lavamanos y sanitario suspendido. Se entra desde la habitación |
| Vestier | 3,06 m² | Clósets en L y espejo de cuerpo entero. Se entra desde la habitación |
| Habitación 2 | 8,88 m² | Cama doble, armario de 1,40 m y escritorio bajo la ventana |
| Baño social | 2,73 m² | Ducha, sanitario suspendido y lavamanos. Sirve a la habitación 2 y a la zona social |
| Ropas | 1,11 m² | Lavadora y secadora apiladas y lavadero, tras una puerta corrediza desde el hall |
| Hall de alcobas | 2,12 m² | Reparte las dos habitaciones, el baño social y ropas |
| **Interior neto** | **53,97 m²** | Muros dentro de la envolvente: 7,36 m². Envolvente bruta: 61,36 m² |
| Balcón propuesto | 4,04 m² | 2,449 × 1,65 m, exterior a la envolvente |

Las áreas se calculan sobre una malla de 1 cm (`tools/disenar_102.py`). El rótulo comercial del plano
(60,42 m²) no se modifica: como en el 104, el DWG no dice cómo se midió.

## Por qué es mejor

1. **Dos habitaciones de verdad en lugar de «2 + estudio».**
   - La alcoba pequeña del plano original (2,50 × 2,52 m, 6,30 m²) pasa a ser una habitación de
     8,88 m² con cama doble, armario y escritorio.
   - El estudio sin ventana desaparece. Su área se usa para la suite principal y para los servicios.
2. **Suite principal.**
   - La habitación principal tiene ahora baño privado (4,70 m²) y vestier (3,06 m²), con acceso solo
     desde la habitación.
   - En total son 19,15 m² de uso privado. Es el argumento comercial más fuerte de un apartamento de
     60 m².
3. **Circulación corta.**
   - Un solo hall de 2,12 m² reparte cuatro puertas: las dos habitaciones, el baño social y ropas.
   - No hay pasillos largos, y el área se va a los recintos.
4. **Zona social continua.**
   - Sala, comedor y cocina forman un solo espacio de 19,10 m² con luz de la ventana de 2,45 m.
   - El balcón propuesto actúa como extensión de la sala: el recorrido lo presenta como parte de la
     zona social.
5. **Cocina moderna y funcional.**
   - Cocina en L con 3,10 m de mesón y nevera de columna.
   - Abierta al comedor, pero fuera del paso entre el hall y la sala.
6. **Ropas resuelta sin estorbar.**
   - Queda detrás de una puerta corrediza, con acceso desde el hall.
   - No invade la cocina ni la circulación.
7. **Núcleo húmedo agrupado.**
   - Los dos baños y ropas quedan juntos, alrededor de los dos ductos del DWG.
   - Así se simplifican las redes hidrosanitarias y de ventilación.
8. **Luz natural donde se necesita.**
   - Cada habitación conserva su ventana de fachada.
   - Los recintos sin ventana son el hall, los baños, ropas y el vestier: servicios que se ventilan
     por ducto.

## Lo que hay que validar antes de ofrecerla

1. **Sistema estructural.**
   - Si los muros interiores de la torre son estructurales (por ejemplo, muros de concreto de sistema
     industrializado), no se pueden mover. Toda la propuesta depende de esto.
   - Lo debe confirmar el ingeniero estructural del proyecto.
2. **Redes hidrosanitarias y de gas:**
   - nuevas posiciones de baños, cocina y ropas;
   - pendientes de desagüe;
   - ventilación de baños y ropas por los ductos existentes;
   - salida de la campana.
3. **Norma urbanística y licencia.**
   - La redistribución y, sobre todo, el balcón requieren revisar la licencia de construcción y su
     modificación.
4. **Coherencia entre unidades.**
   - El 102 comparte medianero con el 101 y el 103, y su distribución se repite en los pisos
     superiores.
   - Las bajantes deben coincidir piso a piso.
5. **Aprobación del arquitecto del proyecto.**

## En el visor

- **Rótulo permanente:** «Propuesta de redistribución – apto 102 · rediseño conceptual, no planta
  verificada».
- **Planta original del DWG:** una capa dibuja en rojo, sobre el piso, los muros originales, para
  comparar en la maqueta.
- **Solo envolvente del DWG:** oculta tabiques, aparatos, muebles, acabados y balcón de la propuesta,
  y deja la envolvente y la planta original.
- **Leyenda de cuatro categorías:**
  - envolvente, vanos y ductos del DWG;
  - medidas provisionales (alturas);
  - mobiliario y acabados ilustrativos;
  - redistribución y balcón propuestos.
- **Lo mismo que en el 104:** maqueta, recorrido de 12 capítulos, caminata con colisiones, puntos de
  información, acabados en vivo y entorno exterior conceptual.

Supuestos de visualización (no del DWG): altura libre 2,40 m, puertas de 2,10 m, antepecho de 0,90 m
y tabiques de 0,12 m.
