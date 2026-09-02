"""
strategies.py
=============
Implementación del Patrón Strategy para las políticas de enrutamiento y control.
"""

from __future__ import annotations
import random
from typing import Dict, List, Optional, TYPE_CHECKING
import networkx as nx

if TYPE_CHECKING:
    from src.model import RouterAgent, Packet, NodeState
from src.config import ALPHA_PENALTY, BETA_PENALTY, PREV_HOP_PENALTY, THROTTLE_RATIO


class CongestionControlStrategy:
    """Interfaz abstracta de estrategia de enrutamiento."""
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
        raise NotImplementedError

    def should_throttle_injection(self, agent: RouterAgent) -> bool:
        return False


class BaselineShortestPathStrategy(CongestionControlStrategy):
    """
    Línea Base (Sin Control): Enrutamiento estático por camino más corto (Dijkstra).
    Ignora por completo la ocupación de colas y los estados de congestión vecinos.
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
        if not neighbors:
            return None

        best_neighbor = None
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
        return False


class DistributedBackpressureStrategy(CongestionControlStrategy):
    """
    Control Distribuido (Con Control): Desvío adaptativo por gradiente de carga y backpressure.
    Información local (1-hop horizon):
      Cost(u -> v | dst) = dist_topologica(v, dst) + alpha * (rho_v)^2 + beta * I(State_v == CONGESTED)
    Incluye mitigación anti-rebote (anti ping-pong) y frenado hidrodinámico en origen.
    """
    def __init__(self, alpha: float = ALPHA_PENALTY, beta: float = BETA_PENALTY):
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
        if not neighbors:
            return None

        current_dist = distances[current_node].get(dst_node, float('inf'))
        best_neighbor = None
        min_effective_cost = float('inf')
        candidates = []

        from src.model import NodeState

        for v in neighbors:
            neighbor_agent = agent_map[v]
            occupancy_ratio = len(neighbor_agent.queue) / neighbor_agent.queue_capacity
            base_dist = distances[v].get(dst_node, float('inf'))

            congestion_penalty = self.alpha * (occupancy_ratio ** 2)
            if neighbor_agent.state == NodeState.CONGESTED:
                congestion_penalty += self.beta
            elif neighbor_agent.state == NodeState.ALERT:
                congestion_penalty += (self.beta * 0.3)

            prev_hop_penalty = PREV_HOP_PENALTY if (packet is not None and packet.prev_hop == v) else 0.0
            progress_penalty = 1.5 if base_dist >= current_dist else 0.0

            effective_cost = base_dist + congestion_penalty + prev_hop_penalty + progress_penalty

            if effective_cost < min_effective_cost:
                min_effective_cost = effective_cost
                candidates = [v]
            elif abs(effective_cost - min_effective_cost) < 1e-5:
                candidates.append(v)

        return random.choice(candidates) if candidates else None

    def should_throttle_injection(self, agent: RouterAgent) -> bool:
        from src.model import NodeState
        if agent.occupancy_ratio >= agent.alert_threshold:
            return True
        if not agent.neighbors:
            return False
        congested_count = sum(
            1 for n in agent.neighbors if agent.model.agent_map[n].state == NodeState.CONGESTED
        )
        return (congested_count / len(agent.neighbors)) >= THROTTLE_RATIO
