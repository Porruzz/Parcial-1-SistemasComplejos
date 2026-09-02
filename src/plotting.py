"""
plotting.py
===========
Generación de figuras científicas de publicación (300 DPI).
"""

import os
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import seaborn as sns

from src.config import CONDITION_COLORS, STATE_COLORS
from src.model import NetworkCongestionModel, NodeState
from src.strategies import BaselineShortestPathStrategy, DistributedBackpressureStrategy

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "figure.dpi": 300
})


def plot_comparative_indicators(df_raw: pd.DataFrame, output_dir: str = "figures"):
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    order_loads = ["Baja", "Media", "Alta"]
    palette = [CONDITION_COLORS["Sin Control"], CONDITION_COLORS["Con Control"]]

    # (A) PDR
    sns.barplot(
        data=df_raw, x="load", y="pdr_percent", hue="condition",
        order=order_loads, palette=palette, errorbar=("ci", 95), capsize=0.1, ax=axes[0, 0]
    )
    axes[0, 0].set_title("(A) Tasa de Entrega de Paquetes (PDR %)", fontweight="bold")
    axes[0, 0].set_ylabel("PDR (%)")
    axes[0, 0].set_xlabel("Escenario de Carga")
    axes[0, 0].set_ylim(0, 105)

    # (B) Throughput
    sns.barplot(
        data=df_raw, x="load", y="throughput_packets_per_tick", hue="condition",
        order=order_loads, palette=palette, errorbar=("ci", 95), capsize=0.1, ax=axes[0, 1]
    )
    axes[0, 1].set_title("(B) Throughput Global Promedio", fontweight="bold")
    axes[0, 1].set_ylabel("Throughput (paquetes / tick)")
    axes[0, 1].set_xlabel("Escenario de Carga")

    # (C) Latencia
    sns.barplot(
        data=df_raw, x="load", y="mean_latency_ticks", hue="condition",
        order=order_loads, palette=palette, errorbar=("ci", 95), capsize=0.1, ax=axes[1, 0]
    )
    axes[1, 0].set_title("(C) Latencia Media de Entrega", fontweight="bold")
    axes[1, 0].set_ylabel("Latencia (ticks / saltos)")
    axes[1, 0].set_xlabel("Escenario de Carga")

    # (D) Colas
    sns.barplot(
        data=df_raw, x="load", y="mean_queue_length", hue="condition",
        order=order_loads, palette=palette, errorbar=("ci", 95), capsize=0.1, ax=axes[1, 1]
    )
    axes[1, 1].set_title("(D) Ocupación Media de Colas de Búfer", fontweight="bold")
    axes[1, 1].set_ylabel("Longitud de Cola (paquetes)")
    axes[1, 1].set_xlabel("Escenario de Carga")

    plt.suptitle("Comparación de Indicadores de Rendimiento (IC 95%)", fontweight="bold", y=0.99)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig1_comparative_indicators.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f">> Gráfica guardada: {out_path}")


def plot_temporal_dynamics(df_timeseries: pd.DataFrame, output_dir: str = "figures"):
    os.makedirs(output_dir, exist_ok=True)
    df_high = df_timeseries[df_timeseries["load_label"] == "Alta"].copy()
    df_high["pcr_percent"] = df_high["pcr"] * 100.0

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    sns.lineplot(
        data=df_high, x="step", y="mean_queue", hue="condition",
        palette=[CONDITION_COLORS["Sin Control"], CONDITION_COLORS["Con Control"]],
        errorbar=("ci", 95), ax=axes[0]
    )
    axes[0].set_title("Evolución Temporal de la Longitud Media de Cola (Alta Carga)", fontweight="bold")
    axes[0].set_ylabel("Longitud Media de Cola")
    axes[0].axhline(y=10, color="orange", linestyle="--", alpha=0.7, label="Umbral Alerta (50%)")
    axes[0].axhline(y=16, color="red", linestyle="--", alpha=0.7, label="Umbral Congestión (80%)")
    axes[0].legend(loc="upper left")

    sns.lineplot(
        data=df_high, x="step", y="pcr_percent", hue="condition",
        palette=[CONDITION_COLORS["Sin Control"], CONDITION_COLORS["Con Control"]],
        errorbar=("ci", 95), ax=axes[1]
    )
    axes[1].set_title("Proporción de Nodos Congestionados (PCR %) en el Tiempo", fontweight="bold")
    axes[1].set_ylabel("% Nodos Congestionados")
    axes[1].set_xlabel("Paso de Simulación (Ticks)")
    axes[1].legend(loc="upper left")

    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig2_temporal_congestion_dynamics.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f">> Gráfica guardada: {out_path}")


def plot_topology_snapshots(seed: int = 42, output_dir: str = "figures"):
    os.makedirs(output_dir, exist_ok=True)
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

    G = model_no.graph
    pos = nx.spring_layout(G, seed=seed, k=0.35)
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    state_colors = {
        NodeState.NORMAL: STATE_COLORS["NORMAL"],
        NodeState.ALERT: STATE_COLORS["ALERT"],
        NodeState.CONGESTED: STATE_COLORS["CONGESTED"]
    }

    # Sin Control
    colors_no = [state_colors[agent.state] for agent in model_no.agents]
    sizes_no = [180 + (len(agent.queue) * 20) for agent in model_no.agents]
    nx.draw_networkx_nodes(G, pos, node_color=colors_no, node_size=sizes_no, edgecolors="black", linewidths=1.2, ax=axes[0])
    nx.draw_networkx_edges(G, pos, alpha=0.35, edge_color="gray", ax=axes[0])
    axes[0].set_title(f"Sin Control (Dijkstra Estático) - Tick 150\nNodos Congestionados: {sum(1 for a in model_no.agents if a.state == NodeState.CONGESTED)}/50", fontweight="bold")
    axes[0].axis("off")

    # Con Control
    colors_ctrl = [state_colors[agent.state] for agent in model_ctrl.agents]
    sizes_ctrl = [180 + (len(agent.queue) * 20) for agent in model_ctrl.agents]
    nx.draw_networkx_nodes(G, pos, node_color=colors_ctrl, node_size=sizes_ctrl, edgecolors="black", linewidths=1.2, ax=axes[1])
    nx.draw_networkx_edges(G, pos, alpha=0.35, edge_color="gray", ax=axes[1])
    axes[1].set_title(f"Con Control Distribuido (Backpressure) - Tick 150\nNodos Congestionados: {sum(1 for a in model_ctrl.agents if a.state == NodeState.CONGESTED)}/50", fontweight="bold")
    axes[1].axis("off")

    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label='Normal (< 50% cola)', markerfacecolor=STATE_COLORS["NORMAL"], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='Alerta (50% - 80% cola)', markerfacecolor=STATE_COLORS["ALERT"], markersize=12),
        plt.Line2D([0], [0], marker='o', color='w', label='Congestionado (≥ 80% cola)', markerfacecolor=STATE_COLORS["CONGESTED"], markersize=12),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=12, frameon=True)
    plt.suptitle("Topología de Red Watts-Strogatz (N=50): Estados de Congestión Espaciales Emergentes", fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.06, 1, 0.95])

    out_path = os.path.join(output_dir, "fig3_network_topology_snapshots.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f">> Gráfica guardada: {out_path}")


def generate_all_plots(data_dir: str = "data", output_dir: str = "figures"):
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
