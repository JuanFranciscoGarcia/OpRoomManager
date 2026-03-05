# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 16:26:08 2025

@author: juanf
"""

import pandas as pd
import pulp as lp
import time
import matplotlib.pyplot as plt

# Cargar datos
matriz_distancias = pd.read_excel('matriz_distancias_gasolineras.xlsx', index_col=0)
demanda = pd.read_excel('demanda_gasolineras.xlsx')


matriz_distancias = matriz_distancias.iloc[0:17, 0:17]
demanda = demanda.iloc[0:16, ]

# Por unificar bucles introduciré el depósito en la tabla de demandas
DEPOSITO = "Depósito"
demanda = pd.concat([pd.DataFrame({"Unnamed: 0": [DEPOSITO], "Demanda": [0]}), demanda]).reset_index(drop=True)

#debo adjuntar el auxiliar a demandas y distancias
demanda = pd.concat([pd.DataFrame({"Unnamed: 0": 'DepósitoAUX', "Demanda": [0]}), demanda]).reset_index(drop=True)
matriz_distancias['DepósitoAUX'] = matriz_distancias['Depósito'] 
nueva_fila = matriz_distancias.loc[DEPOSITO].copy()  # Copiar la fila
matriz_distancias = pd.concat([matriz_distancias, nueva_fila.to_frame().T], ignore_index=True)
matriz_distancias.index = matriz_distancias.columns.tolist()
clientes = [cliente for cliente in demanda["Unnamed: 0"].values]

# Parámetros, debo identificar la capacidad del camión
CAPACIDAD_CAMION = 25

#%%

# Función para generar rutas iniciales, algoritmo visto en CyR, utilizada una variante en problema quirófanos
# Generar rutas iniciales: una ruta para cada gasolinera
def generar_rutas_individuales(demanda, deposito, deposito_aux):
    rutas = []
    for _, row in demanda.iterrows():
        cliente = row["Unnamed: 0"]
        # Generar rutas solo si el cliente no es el depósito ni el depósito auxiliar
        if cliente != deposito and cliente != deposito_aux:
            rutas.append([deposito, cliente, deposito_aux])
    return rutas

#%%

# Formulación del modelo maestro relajado
def resolver_modelo_maestro_relajado(rutas, matriz_distancias, demanda, clientes):
    
    #genero objeto problema
    problema = lp.LpProblem("SetCovering_VRP", lp.LpMinimize)


    #parámetro de existencia de cliente en ciudad
    air = pd.DataFrame(0, index=clientes, columns=range(len(rutas)))
    for k, ruta in enumerate(rutas):
        for cliente in ruta:
            if cliente in clientes:
                air.loc[cliente, k] = 1
                
    #inicializo variables 'selectores de ruta'
    lambdas = lp.LpVariable.dicts("Ruta", range(len(rutas)),lowBound=0, upBound=1, cat="Continuous")
    costes_rutas = [sum(matriz_distancias.loc[ruta[i], ruta[i + 1]] for i in range(len(ruta) - 1)) for ruta in rutas]

    #función objetivo
    problema += lp.lpSum(costes_rutas[k] * lambdas[k] for k in range(len(rutas)))

    #restricciones --> se cubren todas las ciudades en la selección de rutas
    clientes2 = [cliente for cliente in clientes if cliente != DEPOSITO and cliente != 'DepósitoAUX']
    for cliente2 in clientes2:
        problema += lp.lpSum(air.loc[cliente2, k] * lambdas[k] for k in range(len(rutas))) == 1, f"Cliente_{cliente2}"

    problema.solve()
    return problema, lambdas

#%%

# Formulación del modelo maestro relajado
def resolver_modelo_maestro_sinrelajado(rutas, matriz_distancias, demanda, clientes):
    
    #genero objeto problema
    problema = lp.LpProblem("SetCovering_VRP", lp.LpMinimize)


    #parámetro de existencia de cliente en ciudad
    air = pd.DataFrame(0, index=clientes, columns=range(len(rutas)))
    for k, ruta in enumerate(rutas):
        for cliente in ruta:
            if cliente in clientes:
                air.loc[cliente, k] = 1
                
    #inicializo variables 'selectores de ruta'
    lambdas = lp.LpVariable.dicts("Ruta", range(len(rutas)), cat="Binary")
    costes_rutas = [sum(matriz_distancias.loc[ruta[i], ruta[i + 1]] for i in range(len(ruta) - 1)) for ruta in rutas]

    #función objetivo
    problema += lp.lpSum(costes_rutas[k] * lambdas[k] for k in range(len(rutas)))

    #restricciones --> se cubren todas las ciudades en la selección de rutas
    clientes2 = [cliente for cliente in clientes if cliente != DEPOSITO and cliente != 'DepósitoAUX']
    for cliente2 in clientes2:
        problema += lp.lpSum(air.loc[cliente2, k] * lambdas[k] for k in range(len(rutas))) == 1, f"Cliente_{cliente2}"

    problema.solve()
    return problema, lambdas

#%%

# Generar nueva ruta
def construir_ruta(x, clientes, deposito, deposito_aux):
    ruta = [deposito]  # Inicia en el depósito
    while True:
        actual = ruta[-1]
        siguiente = None
        for cliente in clientes:
            if cliente != actual and (actual, cliente) in x and x[(actual, cliente)] > 0.5:
                siguiente = cliente
                break
        if siguiente is None or siguiente == deposito_aux:
            break
        ruta.append(siguiente)
    ruta.append(deposito_aux)  # Termina en el depósito auxiliar
    return ruta



#%%
# Formulación del subproblema

def resolver_subproblema(precios_sombra, matriz_distancias, demanda, rutas_existentes, clientes):
    # Generar objeto del problema
    subproblema = lp.LpProblem("Subproblema_Generacion_Rutas", lp.LpMinimize)

    # Variables binarias para selección de arcos y nodos
    x = lp.LpVariable.dicts("x", [(i, j) for i in clientes for j in clientes if i != j], cat="Binary")
    y = lp.LpVariable.dicts("y", clientes, cat="Binary")

    # Función objetivo: minimizar el costo reducido
    subproblema += (
        lp.lpSum(matriz_distancias.loc[i, j] * x[(i, j)] for i in clientes for j in clientes if i != j)
        - lp.lpSum(precios_sombra[i] * y[i] for i in clientes if i != "DepósitoAUX")
    )

    # Restricciones de conectividad para nodos regulares
    clientes_regulares = [cliente for cliente in clientes if cliente not in ["Depósito", "DepósitoAUX"]]
    for i in clientes_regulares:
        subproblema += lp.lpSum(x[(i, j)] for j in clientes if i != j) == y[i], f"Conectividad_salida_{i}"
        subproblema += lp.lpSum(x[(j, i)] for j in clientes if i != j) == y[i], f"Conectividad_entrada_{i}"

    # Restricciones de conectividad para el depósito y depósito auxiliar
    subproblema += lp.lpSum(x[("Depósito", j)] for j in clientes if j != "Depósito") == 1, "Salida_deposito"
    subproblema += lp.lpSum(x[(j, "DepósitoAUX")] for j in clientes if j != "DepósitoAUX") == 1, "Entrada_deposito_aux"

    # Restricción de capacidad del camión
    subproblema += (
        lp.lpSum(demanda.loc[demanda["Unnamed: 0"] == cliente, "Demanda"].values[0] * y[cliente]
                 for cliente in clientes if cliente not in ["Depósito", "DepósitoAUX"]) <= CAPACIDAD_CAMION,
        "Capacidad"
    )

    # Restricción de evitar subciclos (MTZ - Miller-Tucker-Zemlin)
    u = lp.LpVariable.dicts("Orden", clientes, lowBound=0, upBound=len(clientes) - 1, cat="Continuous")
    for i in clientes:
        for j in clientes:
            if i != j:
                subproblema += (
                    u[i] - u[j] + len(clientes) * x[(i, j)] <= len(clientes) - 1,
                    f"Subciclo_{i}_{j}"
                )

    # Forzar uso de depósito y depósito auxiliar
    subproblema += y["Depósito"] == 1, "Usar_deposito"
    subproblema += y["DepósitoAUX"] == 1, "Usar_deposito_aux"

    # Evitar repetir rutas existentes
    for ruta in rutas_existentes:
        arcos_ruta = [(ruta[i], ruta[i + 1]) for i in range(len(ruta) - 1)]
        subproblema += (
            lp.lpSum(x[arco] for arco in arcos_ruta if arco in x) <= len(arcos_ruta) - 1,
            f"No_repetir_ruta_{'_'.join(ruta)}"
        )

    # Resolver el subproblema
    subproblema.solve()

    # Construir la nueva ruta a partir de las variables x
    valores_x = {
        (i, j): lp.value(x[(i, j)]) for i in clientes for j in clientes if i != j
    }
    nueva_ruta = construir_ruta(valores_x, clientes, "Depósito", "DepósitoAUX")

    # Validar si la nueva ruta es trivial o ya existe
    if not nueva_ruta or nueva_ruta in rutas_existentes:
        return None, None

    # Retornar la nueva ruta y el costo reducido
    return nueva_ruta, lp.value(subproblema.objective)



#%%
# Integración iterativa
rutas = generar_rutas_individuales(demanda, DEPOSITO, 'DepósitoAUX')
rutas_existentes = rutas

# Variables para evolución
objetivo_evolucion = []
tiempos_evolucion = []


while True:
    inicio = time.time()
    modelo, lambdas = resolver_modelo_maestro_relajado(rutas, matriz_distancias, demanda, clientes)
    print("Coste actual:", lp.value(modelo.objective))
    precios_sombra = {
        cliente: modelo.constraints[f"Cliente_{cliente}"].pi
        for cliente in demanda["Unnamed: 0"].values if cliente != DEPOSITO and cliente != 'DepósitoAUX'
    }
    precios_sombra[DEPOSITO] = 0
    precios_sombra['DepósitoAUX'] = 0

    nueva_ruta, coste_reducido = resolver_subproblema(precios_sombra, matriz_distancias, demanda, rutas, clientes)
    print("Nueva ruta generada:", nueva_ruta)
    objetivo_evolucion.append(lp.value(modelo.objective))
    tiempos_evolucion.append(time.time() - inicio)

    if nueva_ruta is None or coste_reducido is None or coste_reducido >= 0:
        break

    rutas.append(nueva_ruta)

modelo_final, lambdas_final = resolver_modelo_maestro_sinrelajado(rutas, matriz_distancias, demanda,clientes)

print(f"Estado final del modelo: {lp.LpStatus[modelo_final.status]}")
print(f"Coste total mínimo: {lp.value(modelo_final.objective)}")
print("Rutas seleccionadas:")
for r, var in lambdas_final.items():
    if var.varValue > 0:
        print(f"Ruta {r}: {var.varValue}")
        
for r, var in lambdas.items():
    if var.varValue > 0:
        print(f"Ruta {r}: {var.varValue}")

# Graficar evolución
fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:blue'
ax1.set_xlabel('Número de columnas añadidas')
ax1.set_ylabel('Valor de la función objetivo', color=color)
ax1.plot(range(len(objetivo_evolucion)), objetivo_evolucion, marker='o', color=color, label='Valor función objetivo')
ax1.tick_params(axis='y', labelcolor=color)
ax1.legend(loc='upper left')

ax2 = ax1.twinx()
color = 'tab:green'
ax2.set_ylabel('Tiempo (segundos)', color=color)
ax2.plot(range(len(tiempos_evolucion)), tiempos_evolucion, marker='x', color=color, label='Tiempo por columna')
ax2.tick_params(axis='y', labelcolor=color)
ax2.legend(loc='upper right')

plt.title('Evolución del valor de la función objetivo y tiempo de cálculo por columna')
plt.grid(True)
plt.show()
