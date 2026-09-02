# Agent-Based Modeling for Decentralized Congestion Control in Complex Networks

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Framework Mesa / NetworkX](https://img.shields.io/badge/framework-NetworkX%20%7C%20Mesa-green.svg)]()
[![Design Patterns GoF](https://img.shields.io/badge/architecture-SOLID%20%26%20GoF-orange.svg)]()

Autonomous multi-agent simulation model designed to study the emergence of congestion in complex data communication networks and evaluate a decentralized, self-organizing congestion control mechanism based on the **Net Interaction** framework (Lafont, 1990) and local backpressure heuristics (Gershenson, 2007).

---

## 🏛️ Software Architecture & Design Patterns

The codebase is structured following professional Object-Oriented Programming (OOP) and Gang of Four (GoF) design patterns:

* **Strategy Pattern (`src/strategies.py`):** Enables hot-swapping between `BaselineShortestPathStrategy` (static Dijkstra) and `DistributedBackpressureStrategy` (dynamic load-gradient deflection & backpressure throttling).
* **State Pattern (`src/model.py`):** Finite state machine modeling router saturation levels (`NORMAL` $\to$ `ALERT` $\to$ `CONGESTED`).
* **Observer Pattern (`src/metrics.py`):** Decoupled telemetry collector capturing tick-by-tick time-series data and computing 95% confidence intervals across replications.
* **Factory Pattern (`src/topology.py`):** Deterministic builder for connected Watts-Strogatz Small-World networks ($N=50, k=4, p=0.10$).

```
Parcial-1-Sistemas-Complejos/
│
├── main.py                  # Unified CLI Entrypoint (run experiments, plots, demo)
├── generate_report.py       # Automated PDF Academic Report Builder (ReportLab)
├── requirements.txt         # Project dependencies
├── .gitignore               # Optimized Git rules
│
├── src/                     # Core Source Code
│   ├── config.py            # Centralized hyperparameter & configuration manager
│   ├── model.py             # RouterAgent, Packet entity, and ABM Simulation Model
│   ├── strategies.py        # Strategy Pattern routing policies
│   ├── topology.py          # Network topology factory (Watts-Strogatz / Barabási-Albert)
│   ├── metrics.py           # Observer Pattern telemetry and statistical engine
│   ├── experiments.py       # 60-Run factorial matrix executor (2 cond x 3 loads x 10 seeds)
│   ├── plotting.py          # High-resolution (300 DPI) scientific figure generator
│   └── visualizer.py        # Real-time Matplotlib/NetworkX animated demo
│
├── data/                    # Generated Empirical Datasets
│   ├── results_raw_runs.csv
│   ├── results_summary_table.csv
│   └── results_timeseries.csv
│
└── figures/                 # Scientific Visualizations & Snapshots
    ├── fig1_comparative_indicators.png
    ├── fig2_temporal_congestion_dynamics.png
    └── fig3_network_topology_snapshots.png
```

---

## 🚀 Quickstart & Usage

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run the Full Experimental Suite (60 Factorial Runs)
```bash
python main.py --experiment
```

### 3. Generate Scientific Figures (300 DPI)
```bash
python main.py --plot
```

### 4. Launch Live Interactive Demo (For Presentation / Oral Defense)
```bash
# Distributed Control under High Load:
python main.py --demo --condition "Con Control" --load "Alta"

# Baseline (No Control) under High Load:
python main.py --demo --condition "Sin Control" --load "Alta"
```

### 5. Build Academic PDF Report
```bash
python generate_report.py
```

---

## 📊 Summary of Experimental Results ($M=10$ Replications, 95% CI)

| Condition | Traffic Load ($\lambda$) | Packets Generated | Packets Delivered | **Packets Dropped (Loss)** | **Delivery Ratio (PDR %)** | Throughput (pkt/tick) | Mean Latency (ticks) | Congested Nodes (PCR %) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **No Control** | **Low (0.04)** | $595.5 \pm 16.5$ | $587.4 \pm 16.2$ | $0.0 \pm 0.0$ | **$98.64\% \pm 0.38\%$** | $1.96 \pm 0.05$ | $3.93 \pm 0.20$ | $0.00\%$ |
| **No Control** | **Medium (0.12)** | $1796.0 \pm 35.6$ | $1770.2 \pm 34.2$ | $1.5 \pm 3.4$ | **$98.57\% \pm 0.20\%$** | $5.90 \pm 0.11$ | $4.51 \pm 0.38$ | $0.02\%$ |
| **No Control** | **High (0.28)** | $4194.2 \pm 41.5$ | $3248.5 \pm 189.8$ | $\mathbf{790.2 \pm 188.4}$ | **$77.47\% \pm 4.60\%$** | $10.83 \pm 0.63$ | $11.89 \pm 1.11$ | $6.15\% \pm 1.22\%$ |
| **With Control** | **Low (0.04)** | $609.3 \pm 20.0$ | $601.9 \pm 18.7$ | $0.0 \pm 0.0$ | **$98.80\% \pm 0.43\%$** | $2.01 \pm 0.06$ | $3.93 \pm 0.17$ | $0.00\%$ |
| **With Control** | **Medium (0.12)** | $1804.1 \pm 16.1$ | $1777.2 \pm 17.8$ | $0.0 \pm 0.0$ | **$98.51\% \pm 0.29\%$** | $5.92 \pm 0.06$ | $4.38 \pm 0.26$ | $0.00\%$ |
| **With Control** | **High (0.28)** | $3767.1 \pm 156.2$ | $3358.8 \pm 277.1$ | $\mathbf{38.9 \pm 27.0}$ | **$88.90\% \pm 3.68\%$** | $11.20 \pm 0.92$ | $21.31 \pm 5.93$ | $1.86\% \pm 0.96\%$ |

* **Packet loss reduction:** $95.1\%$ reduction in dropped packets under heavy traffic saturation.
* **Delivery success:** PDR increased from $77.47\%$ to $88.90\%$ ($+11.43$ percentage points).
