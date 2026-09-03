"""
Modulo de Generacion de Figuras Cientificas (src/plotting.py)
=============================================================
Genera las visualizaciones cuantitativas en alta resolucion (300 DPI) para el informe
y la presentacion de resultados.

Figuras Generadas:
------------------
1. fig1_comparative_indicators.png:
   Grafica de barras 2x2 que contrasta PDR (%), Throughput, Latencia y Longitud Media de Cola
   a traves de los tres escenarios de carga (Baja, Media, Alta) con barras de error al IC 95%.
2. fig2_temporal_congestion_dynamics.png:
   Serie temporal continua (300 ticks) de la longitud media de cola y la proporcion de
   nodos congestionados (PCR %) bajo regimen de carga alta (lambda = 0.28).
3. fig3_network_topology_snapshots.png:
   Instantanea espacial comparativa del grafo Watts-Strogatz en el tick 150, coloreando
   los nodos segun su estado de saturacion FSM y escalando su diametro segun la cola.
"""

import os
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import seaborn as sns

from src.config import CONDITION_COLORS, STATE_COLORS
from src.model import NetworkCongestionModel, NodeState
from src.strategies import BaselineShortestPathStrategy, DistributedBackpressureStrategy

# Configuracion estetica global para graficas cientificas
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "figure.dpi": 300
})


def plot_comparative_indicators(df_raw: pd.DataFrame, output_dir: str = "figures") -> None:
    """
    Construye la Figura 1: Comparacion de indicadores de rendimiento con barras de error (IC 95%).

    Parametros:
    -----------
    df_raw : pd.DataFrame
        Dataset con los resultados individuales de las 60 corridas.
    output_dir : str
        Directorio destino para guardar la imagen PNG en 300 DPI.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    order_loads = ["Baja", "Media", "Alta"]
    palette = [CONDITION_COLORS["Sin Control"], CONDITION_COLORS["Con Control"]]

    # Panel (A): Tasa de Entrega de Paquetes (PDR %)
    sns.barplot(
        data=df_raw, x="load", y="pdr_percent", hue="condition",
        order=order_loads, palette=palette, errorbar=("ci", 95), capsize=0.1, ax=axes[0, 0]
    )
    axes[0, 0].set_title("(A) Tasa de Entrega de Paquetes (PDR %)", fontweight="bold")
    axes[0, 0].set_ylabel("PDR (%)")
    axes[0, 0].set_xlabel("Escenario de Carga")
    axes[0, 0].set_ylim(0, 105)

    # Panel (B): Throughput Global Promedio
    sns.barplot(
        data=df_raw, x="load", y="throughput_packets_per_tick", hue="condition",
        order=order_loads, palette=palette, errorbar=("ci", 95), capsize=0.1, ax=axes[0, 1]
    )
    axes[0, 1].set_title("(B) Throughput Global Promedio", fontweight="bold")
    axes[0, 1].set_ylabel("Throughput (paquetes / tick)")
    axes[0, 1].set_xlabel("Escenario de Carga")

    # Panel (C): Latencia Media de Entrega
    sns.barplot(
        data=df_raw, x="load", y="mean_latency_ticks", hue="condition",
        order=order_loads, palette=palette, errorbar=("ci", 95), capsize=0.1, ax=axes[1, 0]
    )
    axes[1, 0].set_title("(C) Latencia Media de Entrega", fontweight="bold")
    axes[1, 0].set_ylabel("Latencia (ticks / saltos)")
    axes[1, 0].set_xlabel("Escenario de Carga")

    # Panel (D): Ocupacion Media de Colas
    sns.barplot(
        data=df_raw, x="load", y="mean_queue_length", hue="condition",
        order=order_loads, palette=palette, errorbar=("ci", 95), capsize=0.1, ax=axes[1, 1]
    )
    axes[1, 1].set_title("(D) Ocupacion Media de Colas de Bufer", fontweight="bold")
    axes[1, 1].set_ylabel("Longitud de Cola (paquetes)")
    axes[1, 1].set_xlabel("Escenario de Carga")

    plt.suptitle("Comparacion de Indicadores de Rendimiento: Sin Control vs Con Control (IC 95%)", fontweight="bold", y=0.99)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig1_comparative_indicators.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f">> Figura 1 generada exitosamente: {out_path}")


def plot_temporal_dynamics(df_timeseries: pd.DataFrame, output_dir: str = "figures") -> None:
    """
    Construye la Figura 2: Dinamica temporal de colas y PCR bajo carga alta (lambda = 0.28).

    Parametros:
    -----------
    df_timeseries : pd.DataFrame
        Dataset de series temporales con registros tick a tick.
    output_dir : str
        Directorio de exportacion.
    """
    os.makedirs(output_dir, exist_ok=True)
    df_high = df_timeseries[df_timeseries["load_label"] == "Alta"].copy()
    df_high["pcr_percent"] = df_high["pcr"] * 100.0 if df_high["pcr"].max() <= 1.0 else df_high["pcr"]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Panel Superior: Longitud Media de Cola
    sns.lineplot(
        data=df_high, x="step", y="mean_queue", hue="condition",
        palette=[CONDITION_COLORS["Sin Control"], CONDITION_COLORS["Con Control"]],
        errorbar=("ci", 95), ax=axes[0]
    )
    axes[0].set_title("Evolucion Temporal de la Longitud Media de Cola (Escenario Carga Alta)", fontweight="bold")
    axes[0].set_ylabel("Longitud Media de Cola")
    axes[0].axhline(y=10, color="orange", linestyle="--", alpha=0.7, label="Umbral Alerta (50%)")
    axes[0].axhline(y=16, color="red", linestyle="--", alpha=0.7, label="Umbral Congestion (80%)")
    axes[0].legend(loc="upper left")

    # Panel Inferior: Proporcion de Nodos Congestionados (PCR %)
    sns.lineplot(
        data=df_high, x="step", y="pcr_percent", hue="condition",
        palette=[CONDITION_COLORS["Sin Control"], CONDITION_COLORS["Con Control"]],
        errorbar=("ci", 95), ax=axes[1]
    )
    axes[1].set_title("Proporcion de Nodos Congestionados (PCR %) en el Tiempo", fontweight="bold")
    axes[1].set_ylabel("% Nodos Congestionados")
    axes[1].set_xlabel("Paso de Simulacion (Ticks)")
    axes[1].legend(loc="upper left")

    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig2_temporal_congestion_dynamics.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f">> Figura 2 generada exitosamente: {out_path}")


def plot_topology_snapshots(seed: int = 42, output_dir: str = "figures") -> None:
    """
    Construye la Figura 3: Instantaneas topologicas espaciales comparativas en el tick 150.

    Parametros:
    -----------
    seed : int
        Semilla determinista para la topologia y el layout de red.
    output_dir : str
        Directorio de exportacion.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Instanciacion y ejecucion simultanea hasta el paso 150
    model_no = NetworkCongestionModel(
        num_nodes=50, k_neighbors=4, rewire_prob=0.10, injection_rate=0.28,
        strategy=BaselineShortestPathStrategy(), condition_name="Sin Control", seed=seed
    )
    model_ctrl = NetworkCongestionModel(
        num_nodes=50, k_neighbors=4, rewire_prob=0.10, injection_rate=0.28,
        strategy=DistributedBackpressureStrategy(), condition_name="Con Control", seed=seed
    )

    for _ in range(150):
        model_no.step()
        model_ctrl.step()

    grafo = model_no.graph
    posiciones = nx.spring_layout(grafo, seed=seed, k=0.35)
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    state_colors = {
        NodeState.NORMAL: STATE_COLORS["NORMAL"],
        NodeState.ALERT: STATE_COLORS["ALERT"],
        NodeState.CONGESTED: STATE_COLORS["CONGESTED"]
    }

    # Subfigura Izquierda: Sin Control (Dijkstra)
    colors_no = [state_colors[agent.state] for agent in model_no.agents]
    sizes_no = [180 + (len(agent.queue) * 20) for agent in model_no.agents]
    nx.draw_networkx_nodes(grafo, posiciones, node_color=colors_no, node_size=sizes_no, edgecolors="black", linewidths=1.2, ax=axes[0])
    nx.draw_networkx_edges(grafo, posiciones, alpha=0.35, edge_color="gray", ax=axes[0])
    congested_no = sum(1 for a in model_no.agents if a.state == NodeState.CONGESTED)
    axes[0].set_title(f"Sin Control (Dijkstra Estatico) - Tick 150\nNodos Congestionados: {congested_no}/50", fontweight="bold")
    axes[0].axis("off")

    # Subfigura Derecha: Con Control (Backpressure)
    colors_ctrl = [state_colors[agent.state] for agent in model_ctrl.agents]
    sizes_ctrl = [180 + (len(agent.queue) * 20) for agent in model_ctrl.agents]
    nx.draw_networkx_nodes(grafo, posiciones, node_color=colors_ctrl, node_size=sizes_ctrl, edgecolors="black", linewidths=1.2, ax=axes[1])
    nx.draw_networkx_edges(grafo, posiciones, alpha=0.35, edge_color="gray", ax=axes[1])
    congested_ctrl = sum(1 for a in model_ctrl.agents if a.state == NodeState.CONGESTED)
    axes[1].set_title(f"Con Control Distribuido (Backpressure) - Tick 150\nNodos Congestionados: {congested_ctrl}/50", fontweight="bold")
    axes[1].axis("off")

    # Leyenda unificada
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label='Normal (< 50% cola)', markerfacecolor=STATE_COLORS["NORMAL"], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='Alerta (50% - 80% cola)', markerfacecolor=STATE_COLORS["ALERT"], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='Congestionado (>= 80% cola)', markerfacecolor=STATE_COLORS["CONGESTED"], markersize=12),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=12, frameon=True)
    plt.suptitle("Topologia de Red Watts-Strogatz (N=50): Estados de Congestion Espaciales Emergentes", fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.06, 1, 0.95])

    out_path = os.path.join(output_dir, "fig3_network_topology_snapshots.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f">> Figura 3 generada exitosamente: {out_path}")


def generate_all_plots(data_dir: str = "data", output_dir: str = "figures") -> None:
    """
    Ejecuta la generacion secuencial de las tres figuras cientificas del proyecto.
    """
    raw_path = os.path.join(data_dir, "results_raw_runs.csv")
    timeseries_path = os.path.join(data_dir, "results_timeseries.csv")
    
    if not os.path.exists(raw_path) or not os.path.exists(timeseries_path):
        print(">> No se encontraron archivos de datos en data/. Ejecute experimentos primero.")
        return
        
    df_raw = pd.read_csv(raw_path)
    df_timeseries = pd.read_csv(timeseries_path)
    
    plot_comparative_indicators(df_raw, output_dir)
    plot_temporal_dynamics(df_timeseries, output_dir)
    plot_topology_snapshots(seed=42, output_dir=output_dir)
