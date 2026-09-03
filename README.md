# Modelo Basado en Agentes para el Control Descentralizado de Congestión en Redes Complejas

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Framework Mesa / NetworkX](https://img.shields.io/badge/framework-NetworkX%20%7C%20Mesa-green.svg)]()
[![Patrones de Diseño GoF](https://img.shields.io/badge/arquitectura-SOLID%20%26%20GoF-orange.svg)]()
[![Universidad Sergio Arboleda](https://img.shields.io/badge/institución-Universidad%20Sergio%20Arboleda-red.svg)]()

Simulación computacional multiagente diseñada para estudiar la **aparición de congestión como una propiedad macroscópica emergente** en redes de comunicación de datos de 50 nodos y evaluar la efectividad de un **mecanismo de control descentralizado y auto-organizado** basado en el cálculo de ***Net Interaction* (Yves Lafont, 1990)** y heurísticas locales de contrapresión (*Carlos Gershenson, 2007*).

---

## 🏛️ Arquitectura de Software y Patrones de Diseño (GoF)

El código fuente está modularizado siguiendo las mejores prácticas de programación orientada a objetos (POO) y principios SOLID:

* **Patrón Strategy (`src/strategies.py`):** Permite intercambiar en tiempo de ejecución la política de enrutamiento entre `BaselineShortestPathStrategy` (Dijkstra estático por camino más corto) y `DistributedBackpressureStrategy` (desvío adaptativo por gradiente de carga y contrapresión en origen).
* **Patrón State (`src/model.py`):** Máquina de estados finitos que modela el nivel de saturación de los enrutadores (`NORMAL` $<50\%$ cola $\to$ `ALERT` $50\%-80\%$ $\to$ `CONGESTED` $\ge 80\%$).
* **Patrón Observer (`src/metrics.py`):** Recolector desacoplado de telemetría que captura series temporales paso a paso y computa métricas estadísticas con intervalos de confianza al 95%.
* **Patrón Factory (`src/topology.py`):** Constructor determinista y conexo de redes complejas de Mundo Pequeño (*Watts-Strogatz*, $N=50, k=4, p=0.10$).

```
Parcial-1-SistemasComplejos/
│
├── main.py                  # CLI unificado (experimentos, gráficas, demo interactiva)
├── requirements.txt         # Dependencias del proyecto
├── .gitignore               # Exclusiones de Git
├── README.md                # Documentación del repositorio
│
├── src/                     # Código Fuente Modular
│   ├── config.py            # Hiperparámetros, umbrales y semillas deterministas
│   ├── model.py             # Agente RouterAgent, entidad Packet y NetworkCongestionModel
│   ├── strategies.py        # Patrón Strategy con las políticas de enrutamiento
│   ├── topology.py          # Patrón Factory para generar la red Watts-Strogatz
│   ├── metrics.py           # Patrón Observer para telemetría y análisis estadístico
│   ├── experiments.py       # Batch Runner (Matriz factorial de 60 corridas con IC 95%)
│   ├── plotting.py          # Generador de figuras científicas en alta resolución (300 DPI)
│   └── visualizer.py        # Animación interactiva en tiempo real (Matplotlib/NetworkX)
│
├── data/                    # Datasets Empíricos Generados
│   ├── results_raw_runs.csv       # 60 simulaciones individuales paso a paso
│   ├── results_summary_table.csv  # Tabla consolidada con medias y 95% CI
│   └── results_timeseries.csv     # 90.000 pasos temporales de red
│
└── figures/                 # Figuras Científicas del Parcial
    ├── fig1_comparative_indicators.png        # Gráfica de barras de PDR, Throughput, Latencia y Colas
    ├── fig2_temporal_congestion_dynamics.png  # Series de tiempo (Colapso vs Estabilización)
    └── fig3_network_topology_snapshots.png    # Snapshot espacial de la red con estados (Verde/Naranja/Rojo)
```

---

## 🚀 Instalación y Uso Rápido (CLI)

### 1. Instalación de dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la Suite de 60 Experimentos Factoriales
```bash
python main.py --experiment
```

### 3. Generar las Figuras Científicas (300 DPI)
```bash
python main.py --plot
```

### 4. Lanzar la Demostración Interactiva en Vivo (Para la Sustentación)
```bash
# Simulación con Control Distribuido en Alta Carga:
python main.py --demo --condition "Con Control" --load "Alta"

# Simulación Línea Base (Sin Control) en Alta Carga:
python main.py --demo --condition "Sin Control" --load "Alta"
```

---

## 📊 Tabla de Resultados Experimentales ($M=10$ Réplicas, IC 95%)

Resultados consolidados tras evaluar la matriz completa ($2\text{ Condiciones} \times 3\text{ Cargas} \times 10\text{ Semillas deterministas}$):

| Condición | Escenario de Carga ($\lambda$) | Paquetes Generados | Paquetes Entregados | **Paquetes Descartados (Pérdida)** | **Tasa de Entrega (PDR %)** | Throughput (paq/tick) | Latencia Media (ticks) | Nodos Congestionados (PCR %) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Sin Control** | **Baja (0.04)** | $595.5 \pm 16.5$ | $587.4 \pm 16.2$ | $0.0 \pm 0.0$ | **$98.64\% \pm 0.38\%$** | $1.96 \pm 0.05$ | $3.93 \pm 0.20$ | $0.00\%$ |
| **Sin Control** | **Media (0.12)** | $1796.0 \pm 35.6$ | $1770.2 \pm 34.2$ | $1.5 \pm 3.4$ | **$98.57\% \pm 0.20\%$** | $5.90 \pm 0.11$ | $4.51 \pm 0.38$ | $0.02\%$ |
| **Sin Control** | **Alta (0.28)** | $4194.2 \pm 41.5$ | $3248.5 \pm 189.8$ | $\mathbf{790.2 \pm 188.4}$ | **$77.47\% \pm 4.60\%$** | $10.83 \pm 0.63$ | $11.89 \pm 1.11$ | $6.15\% \pm 1.22\%$ |
| **Con Control** | **Baja (0.04)** | $609.3 \pm 20.0$ | $601.9 \pm 18.7$ | $0.0 \pm 0.0$ | **$98.80\% \pm 0.43\%$** | $2.01 \pm 0.06$ | $3.93 \pm 0.17$ | $0.00\%$ |
| **Con Control** | **Media (0.12)** | $1804.1 \pm 16.1$ | $1777.2 \pm 17.8$ | $0.0 \pm 0.0$ | **$98.51\% \pm 0.29\%$** | $5.92 \pm 0.06$ | $4.38 \pm 0.26$ | $0.00\%$ |
| **Con Control** | **Alta (0.28)** | $3767.1 \pm 156.2$ | $3358.8 \pm 277.1$ | $\mathbf{38.9 \pm 27.0}$ | **$88.90\% \pm 3.68\%$** | $11.20 \pm 0.92$ | $21.31 \pm 5.93$ | $1.86\% \pm 0.96\%$ |

---

## 💡 Conclusiones y Hallazgos Principales

1. **Reducción del 95.1% en descarte de paquetes:** En el régimen saturado (alta carga), el control distribuido reduce los paquetes perdidos por desbordamiento de cola de **$790.2$** a solo **$38.9$ paquetes**.
2. **Mejora del PDR (+11.43 pp):** La tasa de entrega de paquetes asciende del **$77.47\%$** al **$88.90\%$**.
3. **Trade-off de Latencia (*"When slow is faster"*, Gershenson 2007):** El incremento leve en la latencia media ($11.89 \to 21.31$ ticks) representa el coste temporal óptimo que asumen los paquetes al ser desviados por rutas secundarias más largas pero libres de colas, evitando la destrucción de información por descarte masivo.
