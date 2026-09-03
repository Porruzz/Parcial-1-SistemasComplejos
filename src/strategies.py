"""
Modulo de Estrategias de Enrutamiento y Control (src/strategies.py)
==================================================================
Implementa el Patron de Diseno de Comportamiento Strategy (GoF) para desacoplar
la logica de seleccion de siguiente salto y control de congestion del ciclo central del modelo.

Estrategias Implementadas:
--------------------------
1. BaselineShortestPathStrategy:
   Enrutamiento estatico de caminos minimos (Dijkstra). Selecciona exclusivamente
   el vecino con menor distancia topologica al destino, sin retroalimentacion de carga.
2. DistributedBackpressureStrategy:
   Enrutamiento adaptativo descentralizado basado en el calculo de Net Interaction
   (Lafont, 1990) y contrapresion local (Gershenson, 2007). Modula el coste efectivo
   mediante penalizaciones cuadraticas de cola, penalizacion por estado, prevencion
   anti ping-pong y frenado de inyeccion en origen.
"""

from __future__ import annotations
import random
from typing import Dict, List, Optional, TYPE_CHECKING
import networkx as nx

if TYPE_CHECKING:
    from src.model import RouterAgent, Packet, NodeState
from src.config import ALPHA_PENALTY, BETA_PENALTY, PREV_HOP_PENALTY, THROTTLE_RATIO


class CongestionControlStrategy:
    """
    Interfaz abstracta base para las politicas de enrutamiento y control de congestion.
    Define el contrato que deben satisfacer todas las estrategias concretas.
    """

    def select_next_hop(
        self,
        current_node: int,
        dst_node: int,
        neighbors: List[int],
        graph: nx.Graph,
        agent_map: Dict[int, RouterAgent],
        distances: Dict[int, Dict[int, int]],
        packet: Optional[Packet] = None
    ) -> Optional[int]:
        """
        Selecciona el siguiente salto (nodo vecino) para reenviar un paquete dado.

        Parametros:
        -----------
        current_node : int
            Identificador del nodo actual que posee el paquete.
        dst_node : int
            Identificador del nodo destino final del paquete.
        neighbors : List[int]
            Lista de identificadores de los nodos vecinos adyacentes (horizonte de 1 salto).
        graph : nx.Graph
            Grafo global de la topologia.
        agent_map : Dict[int, RouterAgent]
            Diccionario de acceso a las instancias de los agentes enrutadores.
        distances : Dict[int, Dict[int, int]]
            Matriz de distancias topologicas minimas entre todos los pares de nodos.
        packet : Optional[Packet]
            Instancia del paquete en transito con su metadata de origen y salto previo.

        Retorna:
        --------
        Optional[int]
            Identificador del nodo vecino seleccionado, o None si no existen candidatos.
        """
        raise NotImplementedError("Las subclases concretas deben implementar select_next_hop.")

    def should_throttle_injection(self, agent: RouterAgent) -> bool:
        """
        Determina si un nodo de origen debe reducir su tasa de inyeccion de paquetes (freno hidrodinamico).

        Parametros:
        -----------
        agent : RouterAgent
            Instancia del agente enrutador que evalua la inyeccion.

        Retorna:
        --------
        bool
            True si se debe reducir la inyeccion al 50%, False en caso contrario.
        """
        return False


class BaselineShortestPathStrategy(CongestionControlStrategy):
    """
    Estrategia de Linea Base (Sin Control).
    Implementa enrutamiento estatico clasico de caminos minimos (Dijkstra no ponderado).
    Los agentes ignoran completamente la longitud de cola y el estado de saturacion de los vecinos.
    """

    def select_next_hop(
        self,
        current_node: int,
        dst_node: int,
        neighbors: List[int],
        graph: nx.Graph,
        agent_map: Dict[int, RouterAgent],
        distances: Dict[int, Dict[int, int]],
        packet: Optional[Packet] = None
    ) -> Optional[int]:
        """
        Selecciona el vecino que minimice la distancia topologica al destino.
        En caso de empates de distancia minima, rompe la simetria de forma pseudoaleatoria uniforme.
        """
        if not neighbors:
            return None

        min_dist = float('inf')
        candidates = []

        for n in neighbors:
            d = distances[n].get(dst_node, float('inf'))
            if d < min_dist:
                min_dist = d
                candidates = [n]
            elif d == min_dist:
                candidates.append(n)

        return random.choice(candidates) if candidates else None

    def should_throttle_injection(self, agent: RouterAgent) -> bool:
        """La linea base carece de mecanismos de frenado en origen."""
        return False


class DistributedBackpressureStrategy(CongestionControlStrategy):
    """
    Estrategia de Control Distribuido y Auto-Organizado (Con Control).
    
    Formula de Coste Efectivo Local:
    --------------------------------
    Costo(u -> v | dst) = d(v, dst) + alpha * (rho_v)^2 + beta * I(Estado_v == CONGESTED)
                         + gamma_alert * I(Estado_v == ALERT) + P_prev + P_prog

    Componentes:
    ------------
    - d(v, dst): Progreso topologico remanente hacia el destino.
    - alpha * (rho_v)^2: Penalizacion no lineal (cuadratica) por ocupacion de cola del vecino.
    - beta: Penalizacion fija si el vecino esta saturado (>= 80% ocupacion).
    - P_prev: Penalizacion anti ping-pong para evitar bucles entre nodos contiguos.
    - P_prog: Penalizacion si el salto no reduce la distancia topologica.
    """

    def __init__(self, alpha: float = ALPHA_PENALTY, beta: float = BETA_PENALTY):
        """
        Inicializa la estrategia con los coeficientes de penalizacion configurados.
        """
        self.alpha = alpha
        self.beta = beta

    def select_next_hop(
        self,
        current_node: int,
        dst_node: int,
        neighbors: List[int],
        graph: nx.Graph,
        agent_map: Dict[int, RouterAgent],
        distances: Dict[int, Dict[int, int]],
        packet: Optional[Packet] = None
    ) -> Optional[int]:
        """
        Calcula el coste compuesto para cada vecino en el horizonte de 1 salto y elige el de menor coste.
        """
        if not neighbors:
            return None

        current_dist = distances[current_node].get(dst_node, float('inf'))
        min_effective_cost = float('inf')
        candidates = []

        from src.model import NodeState

        for v in neighbors:
            neighbor_agent = agent_map[v]
            occupancy_ratio = len(neighbor_agent.queue) / neighbor_agent.queue_capacity
            base_dist = distances[v].get(dst_node, float('inf'))

            # 1. Penalizacion cuadratica por ocupacion de cola
            congestion_penalty = self.alpha * (occupancy_ratio ** 2)

            # 2. Penalizacion por estado de congestion
            if neighbor_agent.state == NodeState.CONGESTED:
                congestion_penalty += self.beta
            elif neighbor_agent.state == NodeState.ALERT:
                congestion_penalty += (self.beta * 0.30)

            # 3. Penalizacion anti-rebote (anti ping-pong)
            prev_hop_penalty = PREV_HOP_PENALTY if (packet is not None and packet.prev_hop == v) else 0.0

            # 4. Penalizacion de progreso topologico
            progress_penalty = 1.5 if base_dist >= current_dist else 0.0

            # 5. Coste efectivo total
            effective_cost = base_dist + congestion_penalty + prev_hop_penalty + progress_penalty

            # Evaluacion de candidato optimo
            if effective_cost < min_effective_cost:
                min_effective_cost = effective_cost
                candidates = [v]
            elif abs(effective_cost - min_effective_cost) < 1e-5:
                candidates.append(v)

        return random.choice(candidates) if candidates else None

    def should_throttle_injection(self, agent: RouterAgent) -> bool:
        """
        Aplica el principio de autorregulacion en origen:
        Reduce la inyeccion si la propia cola del nodo supera el umbral de alerta (>= 50%)
        o si al menos el 50% de sus vecinos inmediatos se encuentra en estado CONGESTED.
        """
        from src.model import NodeState
        if agent.occupancy_ratio >= agent.alert_threshold:
            return True
        if not agent.neighbors:
            return False

        congested_neighbors = sum(
            1 for n in agent.neighbors if agent.model.agent_map[n].state == NodeState.CONGESTED
        )
        return (congested_neighbors / len(agent.neighbors)) >= THROTTLE_RATIO
