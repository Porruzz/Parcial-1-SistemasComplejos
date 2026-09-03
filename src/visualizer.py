"""
Modulo de Visualizacion Dinamica en Tiempo Real (src/visualizer.py)
===================================================================
Implementa una animacion interactiva en tiempo real utilizando Matplotlib y NetworkX
para observar paso a paso la transicion de fase y la formacion de cuellos de botella.

Componentes del Panel:
----------------------
1. Panel Izquierdo: Grafo interactivo de 50 nodos Watts-Strogatz. Los colores de los nodos
   cambian dinamicamente segun su estado FSM (Verde = NORMAL, Amarillo = ALERT, Rojo = CONGESTED)
   y su diametro se escala en funcion del tamano instantaneo de su cola.
2. Panel Derecho: Telemetria continua en vivo con la curva temporal de longitud media de cola
   y los contadores acumulados de entrega, descarte y tasa de entrega (PDR %).
"""

import sys
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx

from src.config import STATE_COLORS
from src.model import NetworkCongestionModel, NodeState
from src.strategies import BaselineShortestPathStrategy, DistributedBackpressureStrategy


def run_live_visualizer(
    condition: str = "Con Control",
    load: str = "Alta",
    seed: int = 42,
    steps: int = 300
) -> None:
    """
    Despliega una ventana interactiva de animacion paso a paso.

    Parametros:
    -----------
    condition : str
        Estrategia a simular ("Sin Control" o "Con Control").
    load : str
        Escenario de inyeccion ("Baja", "Media" o "Alta").
    seed : int
        Semilla determinista para la generacion del grafo y las trayectorias.
    steps : int
        Numero total de pasos temporales a animar (por defecto 300).
    """
    injection_rate = {"Baja": 0.04, "Media": 0.12, "Alta": 0.28}.get(load, 0.28)
    strategy = DistributedBackpressureStrategy() if condition == "Con Control" else BaselineShortestPathStrategy()

    # Inicializacion del modelo para la sesion visual
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

    grafo = model.graph
    posiciones = nx.spring_layout(grafo, seed=seed, k=0.35)

    fig, (ax_net, ax_metric) = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={'width_ratios': [1.3, 1]})
    steps_data, pdr_data, mean_q_data = [], [], []

    def update(frame):
        """Funcion de actualizacion invocada en cada cuadro de la animacion."""
        model.step()
        ax_net.clear()

        # 1. Renderizado del Grafo Espacial
        colors = [STATE_COLORS[a.state.value] for a in model.agents]
        sizes = [150 + (len(a.queue) * 25) for a in model.agents]

        nx.draw_networkx_nodes(grafo, posiciones, node_color=colors, node_size=sizes, edgecolors="black", linewidths=1.0, ax=ax_net)
        nx.draw_networkx_edges(grafo, posiciones, alpha=0.30, edge_color="gray", ax=ax_net)

        congested = sum(1 for a in model.agents if a.state == NodeState.CONGESTED)
        alerts = sum(1 for a in model.agents if a.state == NodeState.ALERT)

        ax_net.set_title(
            f"Red de 50 Nodos ({condition} - Carga {load})\n"
            f"Tick: {model.current_step} | Congestionados: {congested}/50 | Alerta: {alerts}/50",
            fontweight="bold"
        )
        ax_net.axis("off")

        # 2. Renderizado de Telemetria en Serie Temporal
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
        ax_metric.set_ylabel("Ocupacion de Cola (Paquetes)")
        ax_metric.set_title(
            f"Telemetria en Vivo | PDR: {pdr:.1f}% | Entregados: {model.total_delivered} | Descartes: {model.total_dropped}",
            fontweight="bold"
        )
        ax_metric.legend(loc="upper left")

    anim = FuncAnimation(fig, update, frames=steps, interval=60, repeat=False)
    plt.tight_layout()
    plt.show()
