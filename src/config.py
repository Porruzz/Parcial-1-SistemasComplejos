"""
Modulo de Configuracion Global (src/config.py)
==============================================
Define los hiperparametros, umbrales operativos, escenarios de carga de trafico,
semillas deterministas y constantes visuales utilizadas por el modelo basado en agentes.

Todos los valores numericos estan formalmente acoplados con la formulacion matematica
del sistema complejo y permiten reproducibilidad exacta en las evaluaciones factoriales.
"""

# ==========================================
# 1. PARAMETROS TOPOLOGICOS DE RED
# ==========================================
# Numero total de nodos (enrutadores) que componen la red compleja.
NUM_NODES = 50

# Grado inicial de cada nodo en el anillo regular antes del proceso de reconexion (k vecinos cercanos).
WATTS_STROGATZ_K = 4

# Probabilidad de reconexion estocastica de enlaces para inducir la propiedad de Mundo Pequeno (Watts-Strogatz).
WATTS_STROGATZ_P = 0.10


# ==========================================
# 2. PARAMETROS DE HARDWARE Y BUFER
# ==========================================
# Capacidad maxima de la cola FIFO en cada enrutador (C_q paquetes).
QUEUE_CAPACITY = 20

# Capacidad de procesamiento y transmision del enlace por tick de simulacion (C_ell paquetes / tick).
LINK_CAPACITY = 2

# Umbral de alerta temprana: 50% de ocupacion de cola (gamma_alert = 0.50).
ALERT_THRESHOLD = 0.50

# Umbral critico de congestion: 80% de ocupacion de cola (gamma_crit = 0.80).
CRIT_THRESHOLD = 0.80


# ==========================================
# 3. PARAMETROS DEL MECANISMO DE CONTROL DISTRIBUIDO
# ==========================================
# Coeficiente de ponderacion cuadratica para la razon de ocupacion de cola del vecino (alpha).
ALPHA_PENALTY = 2.0

# Penalizacion fija aplicada cuando un nodo vecino se encuentra en estado CONGESTED (beta).
BETA_PENALTY = 4.0

# Penalizacion anti-rebote (anti ping-pong) para prevenir bucles entre nodos adyacentes.
PREV_HOP_PENALTY = 8.0

# Proporcion minima de vecinos saturados para activar el freno de inyeccion en origen (throttling).
THROTTLE_RATIO = 0.50


# ==========================================
# 4. ESCENARIOS DE CARGA DE TRAFICO (LAMBDA)
# ==========================================
# Probabilidad de inyeccion de paquetes por nodo por tick para cada escenario experimental.
LOAD_SCENARIOS = {
    "Baja": 0.04,   # Regimen subcritico (flujo libre)
    "Media": 0.12,  # Regimen intermedio (cercano a transicion de fase)
    "Alta": 0.28    # Regimen supercritico (saturacion y cuellos de botella)
}


# ==========================================
# 5. PARAMETROS DEL DISENO EXPERIMENTAL
# ==========================================
# Semillas pseudoaleatorias deterministas utilizadas para garantizar reproducibilidad exacta (M = 10 replicas).
EXPERIMENT_SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]

# Duracion estandar de cada corrida experimental en pasos temporales discretos (ticks).
DEFAULT_SIMULATION_STEPS = 300


# ==========================================
# 6. CONFIGURACION DE COLORES PARA VISUALIZACION
# ==========================================
# Codigos hexadecimales para representar los estados de la maquina finita (FSM) de los nodos.
STATE_COLORS = {
    "NORMAL": "#40c057",       # Verde (Ocupacion < 50%)
    "ALERT": "#fcc419",        # Amarillo / Naranja (50% <= Ocupacion < 80%)
    "CONGESTED": "#fa5252"     # Rojo carmesi (Ocupacion >= 80%)
}

# Codigos hexadecimales para contrastar las condiciones de enrutamiento en graficas.
CONDITION_COLORS = {
    "Sin Control": "#d9534f",   # Rojo terracota
    "Con Control": "#2b8a3e"    # Verde bosque
}
