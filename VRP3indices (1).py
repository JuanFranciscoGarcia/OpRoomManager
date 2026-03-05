#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pulp
import pandas as pd

# Carga de datos
datos_demanda = pd.read_excel('demanda_gasolineras.xlsx')
datos_distancias = pd.read_excel('matriz_distancias_gasolineras.xlsx', index_col=0)

demandas = datos_demanda['Demanda'].tolist()
distancias = datos_distancias.values

demandas.insert(0, 0)

# Parámetros y variables
capacidad_max = 25
nodos = 12
camiones = nodos - 1
x = pulp.LpVariable.dicts("x", [(i, j, k) for i in range(nodos) for j in range(nodos) for k in range(camiones)], cat="Binary")
y = pulp.LpVariable.dicts("y", [(i, k) for i in range(nodos) for k in range(camiones)], lowBound=0, cat="Continuous")


problema = pulp.LpProblem("VRP_3_Indices", pulp.LpMinimize)


# F.O.
problema += pulp.lpSum(distancias[i][j] * x[(i, j, k)] for i in range(nodos) for j in range(nodos) for k in range(camiones))

# Restricciones
for j in range(1, nodos):  
    problema += pulp.lpSum(x[(i, j, k)] for i in range(nodos) for k in range(camiones) if i != j) == 1


for i in range(1, nodos):
    problema += pulp.lpSum(x[(i, j, k)] for j in range(nodos) for k in range(camiones) if i != j) == 1


for k in range(camiones):
    for i in range(1, nodos):
        problema += pulp.lpSum(x[(j, i, k)] for j in range(nodos) if j != i) == pulp.lpSum(x[(i, j, k)] for j in range(nodos) if j != i)


for k in range(camiones):
    for i in range(1, nodos):
        problema += y[(i, k)] >= demandas[i]
        problema += y[(i, k)] <= capacidad_max


for k in range(camiones):
    for i in range(1, nodos):
        for j in range(1, nodos):
            if i != j:
                problema += y[(i, k)] - y[(j, k)] + capacidad_max * x[(i, j, k)] <= capacidad_max - demandas[j]


for k in range(camiones):
    for i in range(nodos):
        problema += x[(i, i, k)] == 0


for k in range(camiones):
    problema += pulp.lpSum(x[(0, j, k)] for j in range(1, nodos)) <= 1
    problema += pulp.lpSum(x[(j, 0, k)] for j in range(1, nodos)) <= 1




problema.solve()


print("Estado del modelo:", pulp.LpStatus[problema.status])
print("Distancia total mínima:", pulp.value(problema.objective))


# Rutas asignadas
routes = []
for k in range(camiones):
    for i in range(nodos):
        for j in range(nodos):
            if pulp.value(x[(i, j, k)]) == 1:
                routes.append((i, j, k))

print("Rutas:", routes)




