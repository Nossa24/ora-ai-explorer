# Propuesta de redistribución – apto 102 · Torre 1 · Pinares Ártica Home

> **Rediseño conceptual / propuesta comercial. No es planta verificada ni aprobada del proyecto.**
> Parte del apartamento 102 del DWG (`PLANTA PISO 1 AL PISO 20 · TORRE 1`, rotulado 60,42 m²), pero la
> distribución interior es nueva.

![Original frente a propuesta](capturas/00-original-vs-propuesta.png)

**Versión vigente (barra y ropas junto al acceso).** Sobre la primera propuesta se aprobaron dos ajustes:
- el comedor tradicional se reemplaza por una barra-península de 2 puestos integrada a la cocina en U;
- la zona de ropas pasa a una columna integrada a la cocina, en la esquina izquierda inmediata al
  ingresar (opción B). El antiguo cuarto de ropas queda como depósito.

La estética por defecto del visor es «Monocromática elegante»: blanco, grises y negro mate.

## Qué se conserva del DWG y qué cambia

| Se conserva (DWG) | Cambia (propuesta) |
| --- | --- |
| Envolvente de 8,074 × 7,60 m: medianeros, muro del corredor y fachada | Todos los tabiques interiores |
| Vanos de fachada: ventana de 2,449 m de la sala y dos ventanas de 1,00 m | Cocina, baños, zona de ropas, depósito y puertas interiores |
| Puerta de acceso P2 de 1,00 m, en la misma esquina | Se elimina el estudio |
| Los dos ductos verticales del núcleo húmedo | Balcón de 4,04 m² frente a la sala (propuesta, como en el 104) |

## Nueva distribución

| Espacio | Área neta | Qué tiene |
| --- | --- | --- |
| Sala · cocina · barra | 19,10 m² | Espacio abierto de 7,30 m de fondo. Sala de 3,90 m de fondo frente al balcón; cocina en U con mesón norte (estufa y horno), nevera de columna y barra-península de 1,45 × 0,90 m con lavaplatos y 2 banquetas; columna de ropas de 0,65 × 1,05 m junto al acceso. Sin comedor tradicional |
| Habitación principal | 11,39 m² | Cama de 1,60 m, mesas de noche, butaca junto a la ventana |
| Baño principal (privado) | 4,70 m² | Ducha de 1,78 m con mampara, doble lavamanos y sanitario suspendido. Se entra desde la habitación |
| Vestier | 3,06 m² | Clósets en L y espejo de cuerpo entero. Se entra desde la habitación |
| Habitación 2 | 8,88 m² | Cama doble, armario de 1,40 m y escritorio bajo la ventana |
| Baño social | 2,73 m² | Ducha, sanitario suspendido y lavamanos. Sirve a la habitación 2 y a la zona social |
| Depósito | 1,11 m² | Antiguo cuarto de ropas: depósito o despensa con estantería, tras una puerta corrediza desde el hall |
| Hall de alcobas | 2,12 m² | Reparte las dos habitaciones, el baño social y el depósito |
| **Interior neto** | **53,97 m²** | Muros dentro de la envolvente: 7,36 m². Envolvente bruta: 61,36 m² |
| Balcón propuesto | 4,04 m² | 2,449 × 1,65 m, exterior a la envolvente. Hoja corrediza que abre al este (paso libre de 1,20 m en el eje de la sala) |

Las áreas se calculan sobre una malla de 1 cm (`tools/disenar_102.py`). El rótulo comercial del plano
(60,42 m²) no se modifica: como en el 104, el DWG no dice cómo se midió.

## Barra y ropas: medidas

| Medida | Valor |
| --- | --- |
| Barra-península | 1,45 × 0,90 m, altura 0,90 m, voladizo de 0,30 m hacia la sala, 2 puestos |
| Paso entre la barra y el tabique del depósito | 0,90 m |
| Eje libre cocina – sala – balcón | ≥ 0,85 m, recto, entre la mesa de centro y el televisor |
| Paso libre de la puerta del balcón | 1,20 m (hoja corrediza recogida al oeste) |
| Columna de ropas | 0,65 × 1,05 m, contra el medianero oeste, de 5,40 a 6,45 m desde la fachada |
| Frente libre ante la columna de ropas | 1,70 m |
| Paso al entrar, entre la columna de ropas y el mesón norte | 0,70 m (el mesón norte arranca a 1,55 m del medianero) |

El paso de 0,70 m al entrar es suficiente para una persona pero es el punto más estrecho del acceso:
se consiguió acortando el mesón norte 0,30 m frente al dibujo aprobado; la estufa se corrió 0,20 m al
este.

### Ropas: pendiente de viabilidad técnica

La columna de ropas se aleja del núcleo húmedo. Antes de ofrecerla hay que confirmar:
1. **Desagüe.** Hay ≈3,0–3,5 m horizontales hasta el ducto D1. Con pendiente ≥2 % se necesitan unos
   6–7 cm de afinado de piso o paso por la placa. Alternativa: bomba de desagüe.
2. **Ventilación.** No hay ventana: secadora de condensación o bomba de calor y extracción mecánica
   hacia el ducto.
3. **Instalaciones.** Circuito eléctrico dedicado, punto de agua fría y caliente, bandeja antiderrame e
   impermeabilización bajo la columna.
4. **Coincidencia piso a piso** de bajantes y puntos de agua.

Si alguno de estos puntos no es viable, la alternativa es volver la zona de ropas al antiguo cuarto
(hoy depósito), que está junto a los ductos.

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
   - Un solo hall de 2,12 m² reparte cuatro puertas: las dos habitaciones, el baño social y el depósito.
   - No hay pasillos largos, y el área se va a los recintos.
4. **Zona social continua.**
   - Sala, cocina y barra forman un solo espacio de 19,10 m² con luz de la ventana de 2,45 m.
   - Sin comedor tradicional, la sala gana fondo (3,90 m) y queda un eje recto hasta el balcón.
   - El balcón propuesto actúa como extensión de la sala: el recorrido lo presenta como parte de la
     zona social.
5. **Cocina moderna y funcional.**
   - Cocina en U: mesón norte de 1,40 m con estufa y horno, nevera de columna y barra-península con
     lavaplatos, que sirve también para comer.
   - Abierta a la sala, pero fuera del paso entre el hall y la sala.
6. **Ropas resuelta sin estorbar.**
   - Columna integrada a la carpintería de la cocina, tras puertas corredizas, junto al acceso.
   - Deja libre el antiguo cuarto de ropas como depósito.
7. **Núcleo húmedo agrupado.**
   - Los dos baños quedan juntos, alrededor de los dos ductos del DWG. La zona de ropas se aleja de
     ellos (ver «pendiente de viabilidad técnica»).
   - Así se simplifican las redes hidrosanitarias y de ventilación.
8. **Luz natural donde se necesita.**
   - Cada habitación conserva su ventana de fachada.
   - Los recintos sin ventana son el hall, los baños, el depósito y el vestier: servicios que se
     ventilan por ducto.

## Lo que hay que validar antes de ofrecerla

1. **Sistema estructural.**
   - Si los muros interiores de la torre son estructurales (por ejemplo, muros de concreto de sistema
     industrializado), no se pueden mover. Toda la propuesta depende de esto.
   - Lo debe confirmar el ingeniero estructural del proyecto.
2. **Redes hidrosanitarias y de gas:**
   - nuevas posiciones de baños, cocina, lavaplatos en la península y columna de ropas;
   - pendientes de desagüe;
   - ventilación de baños por los ductos existentes y extracción mecánica de la zona de ropas;
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
- **Estética por defecto «Monocromática elegante»:** microcemento gris perla, muros blancos, cocina en
  negro mate con mármol gris, baños en piedra gris y negro mate. Las otras tres propuestas de acabados
  siguen disponibles.
- **Lo mismo que en el 104:** maqueta, recorrido de 12 capítulos, caminata con colisiones, puntos de
  información, acabados en vivo y entorno exterior conceptual.

Supuestos de visualización (no del DWG): altura libre 2,40 m, puertas de 2,10 m, antepecho de 0,90 m
y tabiques de 0,12 m.
