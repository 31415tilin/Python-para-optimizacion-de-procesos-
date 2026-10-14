import random
import pandas as pd

sectores = ["Agricultura", "COMERCIO", "Manufactura Pesada", "tecnología", "MINERÍA", "Nulo", "agroindustria"]
calificaciones = ["A", "B", "C", "Nulo"]

datos = []
# Generar 1050 filas
for _ in range(1050):
    sector = random.choice(sectores)
    calificacion = random.choice(calificaciones)
    datos.append([sector, calificacion])

# Crear DataFrame y exportar
df = pd.DataFrame(datos, columns=["Sector", "Calificación"])
df.to_csv("datos_sectores.csv", index=False, encoding="utf-8")

print("Archivo 'datos_sectores.csv' generado con éxito con 1050 registros.")