"""
metrics.py
==========
Implementación del Patrón Observer para la recolección y agregación estadística de telemetría.
"""

from __future__ import annotations
from typing import Dict, List, Any, TYPE_CHECKING
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from src.model import NetworkCongestionModel


class MetricsObserver:
    """
    Patrón Observer: Observa el estado del modelo en cada tick y almacena series temporales.
    """
    def __init__(self):
        self.step_records: List[Dict[str, Any]] = []

    def record_step(self, model: NetworkCongestionModel) -> None:
        from src.model import NodeState

        total_queued = sum(len(a.queue) for a in model.agents)
        mean_queue = total_queued / model.num_nodes
        max_queue = max((len(a.queue) for a in model.agents), default=0)

        congested_nodes = sum(1 for a in model.agents if a.state == NodeState.CONGESTED)
        alert_nodes = sum(1 for a in model.agents if a.state == NodeState.ALERT)
        pcr = congested_nodes / model.num_nodes

        step_delivered = model.step_delivered_count
        step_generated = model.step_generated_count
        step_dropped = model.step_dropped_count

        avg_latency = float(np.mean(model.latencies_history)) if model.latencies_history else 0.0

        total_gen = model.total_generated
        total_deliv = model.total_delivered
        current_pdr = (total_deliv / total_gen * 100.0) if total_gen > 0 else 100.0

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
        return pd.DataFrame(self.step_records)
