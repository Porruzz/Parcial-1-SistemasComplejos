"""
visualizer.py
=============
Visualización interactiva y animación en tiempo real con Matplotlib y NetworkX.
"""

import sys
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx

from src.config import STATE_COLORS
from src.model import NetworkCongestionModel, NodeState
from src.strategies import BaselineShortestPathStrategy, DistributedBackpressureStrategy


def run_live_visualizer(condition: str = "Con Control", load: str = "Alta", seed: int = 42, steps: int = 300):
    injection_rate = {"Baja": 0.04, "Media": 0.12, "Alta": 0.28}.get(load, 0.28)
    strategy = DistributedBackpressureStrategy() if condition == "Con Control" else BaselineShortestPathStrategy()

    model = NetworkCongestionModel(
        num_nodes=50,
        k_neighbors=4,
        rewire_prob=0.10,
        injection_rate=injection_rate,
        queue_capacity=20,
        link_capacity=2,
        strategy=strategy,
        condition_name=condition,
        load_label=load,
        seed=seed,
        max_steps=steps
    )

    G = model.graph
    pos = nx.spring_layout(G, seed=seed, k=0.35)

    fig, (ax_net, ax_metric) = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={'width_ratios': [1.3, 1]})
    steps_data, pdr_data, mean_q_data = [], [], []

    def update(frame):
        model.step()
        ax_net.clear()

        colors = [STATE_COLORS[a.state.value] for a in model.agents]
        sizes = [150 + (len(a.queue) * 25) for a in model.agents]

        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, edgecolors="black", linewidths=1.0, ax=ax_net)
        nx.draw_networkx_edges(G, pos, alpha=0.3, edge_color="gray", ax=ax_net)

        congested = sum(1 for a in model.agents if a.state == NodeState.CONGESTED)
        alerts = sum(1 for a in model.agents if a.state == NodeState.ALERT)

        ax_net.set_title(
            f"Red de 50 Nodos ({condition} - Carga {load})\n"
            f"Tick: {model.current_step} | Congestionados: {congested}/50 | Alerta: {alerts}/50",
            fontweight="bold"
        )
        ax_net.axis("off")

        steps_data.append(model.current_step)
        pdr = (model.total_delivered / model.total_generated * 100.0) if model.total_generated > 0 else 100.0
        pdr_data.append(pdr)
        mean_q = sum(len(a.queue) for a in model.agents) / 50.0
        mean_q_data.append(mean_q)

        ax_metric.clear()
        ax_metric.plot(steps_data, mean_q_data, color="#e03131", lw=2, label="Longitud Media de Cola")
        ax_metric.axhline(y=10, color="orange", linestyle="--", alpha=0.6, label="Umbral Alerta (50%)")
        ax_metric.axhline(y=16, color="red", linestyle="--", alpha=0.6, label="Umbral Congestión (80%)")
        ax_metric.set_ylim(0, 21)
        ax_metric.set_xlabel("Paso Temporal (Ticks)")
        ax_metric.set_ylabel("Ocupación de Cola")
        ax_metric.set_title(
            f"Telemetría en Vivo | PDR: {pdr:.1f}% | Entregados: {model.total_delivered} | Caídos: {model.total_dropped}",
            fontweight="bold"
        )
        ax_metric.legend(loc="upper left")

    anim = FuncAnimation(fig, update, frames=steps, interval=60, repeat=False)
    plt.tight_layout()
    plt.show()
