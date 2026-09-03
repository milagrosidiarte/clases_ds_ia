import pandas as pd
from agentes_movilidad import procesar_secuencia

percepciones = pd.read_csv("escenario_agente/percepciones.csv")
bitacora = procesar_secuencia(percepciones)
bitacora.to_csv("bitacora_agentes.csv", index=False)
print(bitacora.to_string(index=False))