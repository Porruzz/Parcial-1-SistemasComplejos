"""
experiments.py
==============
Ejecutor de experimentos masivos (Batch Runner) con inferencia estadística (IC 95%).
"""

import os
import time
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from src.config import EXPERIMENT_SEEDS, LOAD_SCENARIOS, DEFAULT_SIMULATION_STEPS
from src.model import NetworkCongestionModel
from src.strategies import (
    BaselineShortestPathStrategy,
    DistributedBackpressureStrategy
)

CONDITIONS = {
    "Sin Control": BaselineShortestPathStrategy,
    "Con Control": DistributedBackpressureStrategy
}


def calculate_recovery_time(df_steps: pd.DataFrame, threshold_congested: float = 0.30, recovery_level: float = 0.05) -> float:
    pcr_series = df_steps["pcr"].values
    in_congestion = False
    congestion_start = 0
    recovery_times = []

    for t, pcr in enumerate(pcr_series):
        if not in_congestion and pcr >= threshold_congested:
            in_congestion = True
            congestion_start = t
        elif in_congestion and pcr <= recovery_level:
            in_congestion = False
            recovery_times.append(t - congestion_start)

    return float(np.mean(recovery_times)) if recovery_times else 0.0


def run_experiments(output_dir: str = "data", max_steps: int = DEFAULT_SIMULATION_STEPS) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    os.makedirs(output_dir, exist_ok=True)
    raw_runs_records: List[Dict[str, Any]] = []
    all_timeseries_dfs: List[pd.DataFrame] = []

    total_experiments = len(CONDITIONS) * len(LOAD_SCENARIOS) * len(EXPERIMENT_SEEDS)
    current_exp = 0

    print("=" * 80)
    print(f"INICIANDO SUITE EXPERIMENTAL: {total_experiments} SIMULACIONES EN TOTAL")
    print("=" * 80)
    start_time = time.time()

    for cond_name, strategy_cls in CONDITIONS.items():
        for load_label, rate in LOAD_SCENARIOS.items():
            print(f"\n>> Condición: '{cond_name}' | Carga: '{load_label}' (lambda={rate})")
            for seed in EXPERIMENT_SEEDS:
                current_exp += 1
                strategy_instance = strategy_cls()

                model = NetworkCongestionModel(
                    num_nodes=50,
                    k_neighbors=4,
                    rewire_prob=0.10,
                    injection_rate=rate,
                    queue_capacity=20,
                    link_capacity=2,
                    strategy=strategy_instance,
                    condition_name=cond_name,
                    load_label=load_label,
                    seed=seed,
                    max_steps=max_steps
                )

                df_steps = model.run()
                all_timeseries_dfs.append(df_steps)

                total_gen = model.total_generated
                total_deliv = model.total_delivered
                total_drop = model.total_dropped
                pdr = (total_deliv / total_gen * 100.0) if total_gen > 0 else 100.0
                throughput = total_deliv / max_steps
                mean_latency = float(np.mean(model.latencies_history)) if model.latencies_history else 0.0
                mean_queue = df_steps["mean_queue"].mean()
                max_queue_peak = df_steps["max_queue"].max()
                mean_pcr = df_steps["pcr"].mean() * 100.0
                peak_pcr = df_steps["pcr"].max() * 100.0
                rec_time = calculate_recovery_time(df_steps)

                raw_runs_records.append({
                    "run_id": current_exp,
                    "condition": cond_name,
                    "load": load_label,
                    "injection_rate": rate,
                    "seed": seed,
                    "packets_generated": total_gen,
                    "packets_delivered": total_deliv,
                    "packets_dropped": total_drop,
                    "pdr_percent": pdr,
                    "throughput_packets_per_tick": throughput,
                    "mean_latency_ticks": mean_latency,
                    "mean_queue_length": mean_queue,
                    "peak_queue_length": max_queue_peak,
                    "mean_congested_nodes_percent": mean_pcr,
                    "peak_congested_nodes_percent": peak_pcr,
                    "recovery_time_ticks": rec_time
                })
                print(f"  [{current_exp:02d}/{total_experiments}] Seed={seed:3d} | PDR={pdr:5.1f}% | Deliv={total_deliv:4d} | Drop={total_drop:4d} | Latency={mean_latency:4.1f} | MeanQueue={mean_queue:4.1f}")

    elapsed = time.time() - start_time
    print(f"\n>> Experimentos completados en {elapsed:.2f} s.")

    df_raw = pd.DataFrame(raw_runs_records)
    df_timeseries = pd.concat(all_timeseries_dfs, ignore_index=True)

    metrics_to_aggregate = [
        "packets_generated", "packets_delivered", "packets_dropped",
        "pdr_percent", "throughput_packets_per_tick", "mean_latency_ticks",
        "mean_queue_length", "peak_queue_length", "mean_congested_nodes_percent", "recovery_time_ticks"
    ]

    summary_records = []
    for (cond, load), group in df_raw.groupby(["condition", "load"], sort=False):
        n = len(group)
        rec = {"Condición": cond, "Escenario de Carga": load, "N_Replicas": n}
        for metric in metrics_to_aggregate:
            vals = group[metric].values
            mean_val = np.mean(vals)
            std_val = np.std(vals, ddof=1) if n > 1 else 0.0
            sem = std_val / np.sqrt(n) if n > 1 else 0.0
            ci95 = stats.t.ppf(0.975, df=n-1) * sem if n > 1 and sem > 0 else 0.0

            rec[f"{metric}_mean"] = mean_val
            rec[f"{metric}_std"] = std_val
            rec[f"{metric}_ci95"] = ci95
            rec[f"{metric}_formatted"] = f"{mean_val:.2f} ± {ci95:.2f}"
        summary_records.append(rec)

    df_summary = pd.DataFrame(summary_records)

    df_raw.to_csv(os.path.join(output_dir, "results_raw_runs.csv"), index=False)
    df_summary.to_csv(os.path.join(output_dir, "results_summary_table.csv"), index=False)
    df_timeseries.to_csv(os.path.join(output_dir, "results_timeseries.csv"), index=False)

    return df_raw, df_summary, df_timeseries
