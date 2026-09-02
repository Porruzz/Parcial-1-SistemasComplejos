"""
config.py
=========
Configuración centralizada de hiperparámetros y constantes para la simulación.
"""

# Parámetros Topológicos
NUM_NODES = 50
WATTS_STROGATZ_K = 4
WATTS_STROGATZ_P = 0.10

# Parámetros de Enrutamiento y Búfer
QUEUE_CAPACITY = 20
LINK_CAPACITY = 2
ALERT_THRESHOLD = 0.50     # 50% de ocupación -> Alerta
CRIT_THRESHOLD = 0.80      # 80% de ocupación -> Congestión crítica

# Parámetros de Control Distribuido
ALPHA_PENALTY = 2.0        # Penalización cuadrática por longitud de cola
BETA_PENALTY = 4.0         # Penalización por estado CONGESTED
PREV_HOP_PENALTY = 8.0     # Penalización anti-ping-pong (evitar bucles de rebote)
THROTTLE_RATIO = 0.50      # Proporción de vecinos saturados para activar freno

# Escenarios de Inyección de Tráfico
LOAD_SCENARIOS = {
    "Baja": 0.04,
    "Media": 0.12,
    "Alta": 0.28
}

# Semillas deterministas para replicabilidad estadística (M = 10)
EXPERIMENT_SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
DEFAULT_SIMULATION_STEPS = 300

# Paleta de Colores
STATE_COLORS = {
    "NORMAL": "#40c057",       # Verde esmeralda
    "ALERT": "#fcc419",        # Amarillo / Naranja
    "CONGESTED": "#fa5252"     # Rojo carmesí
}

CONDITION_COLORS = {
    "Sin Control": "#d9534f",
    "Con Control": "#2b8a3e"
}
