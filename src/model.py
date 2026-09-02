"""
model.py
========
Núcleo del Modelamiento Basado en Agentes (ABM) para el control de congestión.
Define Packet, NodeState, RouterAgent y NetworkCongestionModel.
"""

from __future__ import annotations
import collections
from dataclasses import dataclass
from enum import Enum
import random
from typing import Dict, List, Optional
import networkx as nx
import numpy as np
import pandas as pd

from src.config import (
    NUM_NODES, WATTS_STROGATZ_K, WATTS_STROGATZ_P,
    QUEUE_CAPACITY, LINK_CAPACITY, ALERT_THRESHOLD, CRIT_THRESHOLD,
    DEFAULT_SIMULATION_STEPS
)
from src.topology import TopologyFactory
from src.strategies import (
    CongestionControlStrategy,
    DistributedBackpressureStrategy
)
from src.metrics import MetricsObserver


class NodeState(Enum):
    """Patrón State: Estados del enrutador según ocupación de búfer."""
    NORMAL = "NORMAL"         # Ocupación < 50%
    ALERT = "ALERT"           # 50% <= Ocupación < 80%
    CONGESTED = "CONGESTED"   # Ocupación >= 80%


@dataclass
class Packet:
    """Entidad discreta de datos que transita por la red."""
    packet_id: int
    src: int
    dst: int
    t_gen: int
    hops: int = 0
    prev_hop: Optional[int] = None
    payload_size: int = 1


class RouterAgent:
    """
    Agente Enrutador Autónomo.
    """
    def __init__(
        self,
        node_id: int,
        model: NetworkCongestionModel,
        queue_capacity: int = QUEUE_CAPACITY,
        link_capacity: int = LINK_CAPACITY,
        alert_threshold: float = ALERT_THRESHOLD,
        crit_threshold: float = CRIT_THRESHOLD
    ):
        self.node_id = node_id
        self.model = model
        self.queue_capacity = queue_capacity
        self.link_capacity = link_capacity
        self.alert_threshold = alert_threshold
        self.crit_threshold = crit_threshold

        self.queue: collections.deque[Packet] = collections.deque()
        self.incoming_buffer: List[Packet] = []
        self.state: NodeState = NodeState.NORMAL
        self.neighbors: List[int] = []

        self.generated_count: int = 0
        self.delivered_count: int = 0
        self.dropped_queue_full: int = 0
        self.forwarded_count: int = 0

    @property
    def occupancy_ratio(self) -> float:
        return len(self.queue) / self.queue_capacity

    def update_state(self) -> None:
        ratio = self.occupancy_ratio
        if ratio >= self.crit_threshold:
            self.state = NodeState.CONGESTED
        elif ratio >= self.alert_threshold:
            self.state = NodeState.ALERT
        else:
            self.state = NodeState.NORMAL

    def receive_packet(self, packet: Packet) -> bool:
        if len(self.queue) + len(self.incoming_buffer) < self.queue_capacity:
            self.incoming_buffer.append(packet)
            return True
        else:
            self.dropped_queue_full += 1
            self.model.total_dropped += 1
            return False

    def flush_incoming_buffer(self) -> None:
        while self.incoming_buffer and len(self.queue) < self.queue_capacity:
            self.queue.append(self.incoming_buffer.pop(0))
        if self.incoming_buffer:
            self.dropped_queue_full += len(self.incoming_buffer)
            self.model.total_dropped += len(self.incoming_buffer)
            self.incoming_buffer.clear()

    def process_and_forward(self) -> None:
        packets_to_send = min(self.link_capacity, len(self.queue))
        for _ in range(packets_to_send):
            if not self.queue:
                break
            packet = self.queue.popleft()
            packet.hops += 1

            # Caso 1: Destino alcanzado
            if packet.dst == self.node_id:
                self.delivered_count += 1
                self.model.on_packet_delivered(packet)
                continue

            # Caso 2: Reenviar al siguiente salto delegando en la estrategia
            next_hop = self.model.strategy.select_next_hop(
                current_node=self.node_id,
                dst_node=packet.dst,
                neighbors=self.neighbors,
                graph=self.model.graph,
                agent_map=self.model.agent_map,
                distances=self.model.all_pairs_distances,
                packet=packet
            )

            if next_hop is not None:
                packet.prev_hop = self.node_id
                receiver = self.model.agent_map[next_hop]
                received = receiver.receive_packet(packet)
                if received:
                    self.forwarded_count += 1
            else:
                self.dropped_queue_full += 1
                self.model.total_dropped += 1


class NetworkCongestionModel:
    """
    Modelo Central de Simulación de Tráfico y Control de Congestión.
    """
    def __init__(
        self,
        num_nodes: int = NUM_NODES,
        k_neighbors: int = WATTS_STROGATZ_K,
        rewire_prob: float = WATTS_STROGATZ_P,
        injection_rate: float = 0.12,
        queue_capacity: int = QUEUE_CAPACITY,
        link_capacity: int = LINK_CAPACITY,
        strategy: Optional[CongestionControlStrategy] = None,
        condition_name: str = "WithControl",
        load_label: str = "Media",
        seed: int = 42,
        max_steps: int = DEFAULT_SIMULATION_STEPS
    ):
        self.num_nodes = num_nodes
        self.k_neighbors = k_neighbors
        self.rewire_prob = rewire_prob
        self.injection_rate = injection_rate
        self.queue_capacity = queue_capacity
        self.link_capacity = link_capacity
        self.strategy = strategy or DistributedBackpressureStrategy()
        self.condition_name = condition_name
        self.load_label = load_label
        self.seed = seed
        self.max_steps = max_steps

        random.seed(seed)
        np.random.seed(seed)

        self.graph = TopologyFactory.create_watts_strogatz(
            n=num_nodes, k=k_neighbors, p=rewire_prob, seed=seed
        )
        self.all_pairs_distances: Dict[int, Dict[int, int]] = dict(
            nx.all_pairs_shortest_path_length(self.graph)
        )
        self.betweenness_centrality = nx.betweenness_centrality(self.graph)

        self.agents: List[RouterAgent] = []
        self.agent_map: Dict[int, RouterAgent] = {}
        for i in range(num_nodes):
            agent = RouterAgent(
                node_id=i,
                model=self,
                queue_capacity=queue_capacity,
                link_capacity=link_capacity
            )
            agent.neighbors = list(self.graph.neighbors(i))
            self.agents.append(agent)
            self.agent_map[i] = agent

        self.current_step: int = 0
        self.packet_counter: int = 0
        self.total_generated: int = 0
        self.total_delivered: int = 0
        self.total_dropped: int = 0

        self.step_generated_count: int = 0
        self.step_delivered_count: int = 0
        self.step_dropped_count: int = 0

        self.latencies_history: List[int] = []
        self.metrics = MetricsObserver()

    def on_packet_delivered(self, packet: Packet) -> None:
        self.total_delivered += 1
        self.step_delivered_count += 1
        latency = self.current_step - packet.t_gen
        self.latencies_history.append(latency)

    def inject_traffic(self) -> None:
        for agent in self.agents:
            effective_rate = self.injection_rate
            if self.strategy.should_throttle_injection(agent):
                effective_rate *= 0.50

            if random.random() < effective_rate:
                self.packet_counter += 1
                dst = random.choice([x for x in range(self.num_nodes) if x != agent.node_id])
                pkt = Packet(
                    packet_id=self.packet_counter,
                    src=agent.node_id,
                    dst=dst,
                    t_gen=self.current_step
                )
                self.total_generated += 1
                self.step_generated_count += 1
                agent.generated_count += 1

                if len(agent.queue) < agent.queue_capacity:
                    agent.queue.append(pkt)
                else:
                    agent.dropped_queue_full += 1
                    self.total_dropped += 1
                    self.step_dropped_count += 1

    def step(self) -> None:
        self.step_generated_count = 0
        self.step_delivered_count = 0
        self.step_dropped_count = 0

        # 1. Inyección de tráfico
        self.inject_traffic()

        # 2. Vaciado de búferes entrantes
        for agent in self.agents:
            agent.flush_incoming_buffer()

        # 3. Sensado de ocupación
        for agent in self.agents:
            agent.update_state()

        # 4. Procesamiento y reenvío concurrente
        agent_order = self.agents.copy()
        random.shuffle(agent_order)
        for agent in agent_order:
            agent.process_and_forward()

        # 5. Actualización de estado
        for agent in self.agents:
            agent.update_state()

        # 6. Registro de métricas
        self.metrics.record_step(self)
        self.current_step += 1

    def run(self, steps: Optional[int] = None) -> pd.DataFrame:
        total_steps = steps or self.max_steps
        for _ in range(total_steps):
            self.step()
        return self.metrics.get_dataframe()
