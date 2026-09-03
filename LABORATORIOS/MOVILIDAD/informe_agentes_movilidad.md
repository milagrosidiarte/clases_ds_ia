## Respuestas

**1. ¿En qué situaciones ambos agentes producen la misma acción?

Coinciden en dos casos: cuando la presión es baja y no hay racha previa (ambos dan NO_REFORZAR), y cuando ya hay dos o más horas consecutivas de presión alta (ambos dan RECOMENDAR_REFUERZO, como se ve en las horas 7 y 8). También coinciden si la percepción es inválida, ambos se abstienen.

**2. ¿Cuándo reaccionan de forma diferente?

Difieren en la primera hora de presión alta después de una racha baja o al inicio: el agente simple ya recomienda refuerzo apenas ve presion >= 0.85, mientras que el basado en modelo espera confirmación de una segunda hora consecutiva antes de recomendar. Se ve en la hora 6: accion_simple = RECOMENDAR_REFUERZO pero accion_modelo = NO_REFORZAR.

**3. ¿Por qué el segundo agente está basado en modelo aunque no planifique?

Porque mantiene un estado interno (racha_presion_alta, presion_anterior, percepcion_valida) que resume información de percepciones pasadas y lo usa para decidir sobre el estado actual, no solo sobre la percepción de la hora. Eso define a un agente basado en modelo: tener una representación interna del mundo (aunque sea mínima) que persiste entre pasos. Sigue siendo reactivo porque aplica reglas condición-acción sobre ese estado, sin generar sucesores ni buscar caminos ni planificar acciones futuras.

**4. ¿Qué representa tasa_otras_simulada y qué no permite afirmar?

Representa una proporción sintética y aleatoria, acotada e inversamente relacionada con la flota de X, que el entorno usa para repartir la demanda total entre X y "otras empresas" ficticias. No permite afirmar nada sobre la participación de mercado real de ninguna empresa de taxis: es una hipótesis didáctica, no una medición, y no está estimada con datos reales.

**5. ¿Por qué resultado_h_mas_1.csv no puede formar parte de la percepción?

Porque contiene información generada después del momento de decisión (la demanda real de la hora h+1). El agente estaría decidiendo con datos del futuro, lo cual invalida la evaluación y no representa una situación realista, donde a la hora h todavía no se sabe qué va a pasar en h+1.


## PEAS

| Elemento | Contenido |
|---|---|
| **Performance** | Recomendaciones coherentes con las reglas de la consigna, ausencia de fuga temporal (nunca se usa información de h+1), abstención ante datos inválidos o incompletos, y trazabilidad (cada acción viene acompañada de un motivo explícito que justifica la regla aplicada). |
| **Environment** | Secuencia horaria simulada para una zona TLC fija (en este caso, zona 161 - Midtown Center), demanda de Yellow Taxi transformada en `demanda_total`, flota fija y conocida de la empresa X, participación sintética de otras empresas, y un responsable humano que revisa la recomendación antes de actuar. |
| **Actuators** | Emisión de uno de los tres mensajes posibles: `NO_REFORZAR`, `RECOMENDAR_REFUERZO`, `ABSTENERSE`. El agente no ejecuta traslados ni asigna vehículos reales; solo comunica una recomendación. |
| **Sensors** | Lectura secuencial y en orden temporal de las filas de `percepciones.csv` (una fila por hora, hasta la hora h inclusive). No es un sensor conectado en tiempo real: es una lectura lógica de un archivo generado previamente por el simulador. |


## Limitaciones

- Los pickups de TLC son viajes Yellow Taxi **realizados y reportados**, no
  demanda total de movilidad ni solicitudes no atendidas.
- X y "otras empresas" son entidades **ficticias**, creadas solo para el
  ejercicio.
- La relación inversa entre el tamaño de la flota de X y la participación de
  otras empresas es una **hipótesis didáctica**, no fue estimada con datos
  reales.
- Se asume una unidad de capacidad por taxi-hora, una **simplificación**
  fuerte de la operación real de una flota.
- La distancia entre centroides de zonas no determina duración de viaje ni
  disponibilidad real de vehículos.
- `RECOMENDAR_REFUERZO` es un mensaje para **revisión humana**, no una orden
  automática ni un traslado ejecutado.

  