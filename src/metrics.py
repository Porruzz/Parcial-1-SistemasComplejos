"""
Modulo de Observacion y Metricas de Rendimiento (src/metrics.py)
================================================================
Implementa el Patron de Diseno de Comportamiento Observer (GoF) para desacoplar
la recoleccion de telemetria del ciclo de simulacion central del modelo.

Monitorea y calcula paso a paso los 7 indicadores cuantitativos requeridos:
1. PDR (Packet Delivery Ratio): Porcentaje acumulado de paquetes entregados con exito.
2. Throughput: Paquetes efectivamente entregados por unidad de tiempo (tick).
3. Latencia Media: Tiempo de transito promedio entre generacion y entrega.
4. Ocupacion Media de Colas: Longitud promedio de los buferes en toda la red.
5. PCR (Percentage of Congested Routers): Proporcion de nodos en estado CONGESTED.
6. Paquetes Descartados: Perdidas acumuladas por desbordamiento de bufer.
7. Balance de Carga: Distribucion espacial de la ocupacion entre nodos.
"""

from __future__ import annotations
from typing import Dict, List, Any, TYPE_CHECKING
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from src.model import NetworkCongestionModel


class MetricsObserver:
    """
    Recolector desacoplado de telemetria en series temporales.
    Captura una instantanea (snapshot) del estado de todos los nodos al final de cada tick.
    """

    def __init__(self):
        """Inicializa la lista de registros de series temporales."""
        self.step_records: List[Dict[str, Any]] = []

    def record_step(self, model: NetworkCongestionModel) -> None:
        """
        Calcula y registra las metricas del sistema correspondientes al paso actual.

        Parametros:
        -----------
        model : NetworkCongestionModel
            Instancia del modelo de simulacion del cual se extrae la telemetria.
        """
        from src.model import NodeState

        # 1. Metricas de Bufer y Ocupacion
        total_queued = sum(len(a.queue) for a in model.agents)
        mean_queue = total_queued / model.num_nodes
        max_queue = max((len(a.queue) for a in model.agents), default=0)

        # 2. Metricas de Estados de Saturacion (PCR)
        congested_nodes = sum(1 for a in model.agents if a.state == NodeState.CONGESTED)
        alert_nodes = sum(1 for a in model.agents if a.state == NodeState.ALERT)
        pcr = (congested_nodes / model.num_nodes) * 100.0  # Expresado en porcentaje

        # 3. Flujo instantaneo en el tick
        step_delivered = model.step_delivered_count
        step_generated = model.step_generated_count
        step_dropped = model.step_dropped_count

        # 4. Latencia promedio acumulada
        avg_latency = float(np.mean(model.latencies_history)) if model.latencies_history else 0.0

        # 5. Tasa acumulada de entrega (PDR)
        total_gen = model.total_generated
        total_deliv = model.total_delivered
        current_pdr = (total_deliv / total_gen * 100.0) if total_gen > 0 else 100.0

        # Almacenar registro estructurado
        self.step_records.append({
            "step": model.current_step,
            "condition": model.condition_name,
            "load_label": model.load_label,
            "injection_rate": model.injection_rate,
            "seed": model.seed,
            "mean_queue": mean_queue,
            "max_queue": max_queue,
            "congested_nodes": congested_nodes,
            "alert_nodes": alert_nodes,
            "pcr": pcr,
            "step_generated": step_generated,
            "step_delivered": step_delivered,
            "step_dropped": step_dropped,
            "total_generated": total_gen,
            "total_delivered": total_deliv,
            "total_dropped": model.total_dropped,
            "cumulative_pdr": current_pdr,
            "mean_latency": avg_latency,
            "throughput_step": step_delivered
        })

    def get_dataframe(self) -> pd.DataFrame:
        """
        Convierte los registros temporales capturados en un DataFrame de pandas.

        Retorna:
        --------
        pd.DataFrame
            Tabla con la serie temporal completa de la simulacion.
        """
        return pd.DataFrame(self.step_records)
