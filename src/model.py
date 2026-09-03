"""
Modulo Central del Modelo Basado en Agentes (src/model.py)
==========================================================
Implementa las entidades computacionales, la maquina de estados finitos (Patron State),
el agente autonomo de enrutamiento (RouterAgent) y la clase orquestadora de la simulacion
compleja (NetworkCongestionModel).

Arquitectura del Modelo:
------------------------
- NodeState (Enum): Estados discretos del enrutador (NORMAL, ALERT, CONGESTED).
- Packet (dataclass): Entidad discreta de informacion que fluye a traves de los enlaces.
- RouterAgent: Agente con memoria local finita (cola FIFO), sensado de vecindario y capacidad de reenvio.
- NetworkCongestionModel: Administrador del espacio topologico, inyeccion estocastica y sincronizacion temporal.
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
    """
    Patron State: Representacion de los estados de saturacion de un enrutador.
    - NORMAL: Ocupacion de cola menor al 50%.
    - ALERT: Ocupacion de cola entre 50% y 80% (alerta temprana).
    - CONGESTED: Ocupacion de cola mayor o igual al 80% (saturacion critica).
    """
    NORMAL = "NORMAL"
    ALERT = "ALERT"
    CONGESTED = "CONGESTED"


@dataclass
class Packet:
    """
    Entidad de datos atomica que transita entre los nodos de la red.

    Atributos:
    ----------
    packet_id : int
        Identificador secuencial unico del paquete.
    src : int
        Identificador del nodo de origen que genero el paquete.
    dst : int
        Identificador del nodo destino final del paquete.
    t_gen : int
        Paso temporal (tick) en el que fue creado el paquete.
    hops : int
        Numero de saltos acumulados en el trayecto.
    prev_hop : Optional[int]
        Identificador del nodo inmediatamente anterior en la ruta (para mitigacion de rebote).
    payload_size : int
        Tamano logico del paquete (1 unidad de capacidad de bufer).
    """
    packet_id: int
    src: int
    dst: int
    t_gen: int
    hops: int = 0
    prev_hop: Optional[int] = None
    payload_size: int = 1


class RouterAgent:
    """
    Agente Enrutador Autonomo.
    Representa un nodo de la red con capacidades de almacenamiento finito, sensado local y reenvio.
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
        """
        Inicializa el agente enrutador con sus parametros de hardware y enlaces.
        """
        self.node_id = node_id
        self.model = model
        self.queue_capacity = queue_capacity
        self.link_capacity = link_capacity
        self.alert_threshold = alert_threshold
        self.crit_threshold = crit_threshold

        # Estructuras de colas
        self.queue: collections.deque[Packet] = collections.deque()
        self.incoming_buffer: List[Packet] = []  # Bufer intermedio para evitar sesgos de orden dentro del mismo tick
        self.state: NodeState = NodeState.NORMAL
        self.neighbors: List[int] = []

        # Contadores locales de telemetria
        self.generated_count: int = 0
        self.delivered_count: int = 0
        self.dropped_queue_full: int = 0
        self.forwarded_count: int = 0

    @property
    def occupancy_ratio(self) -> float:
        """Calcula la razon de ocupacion actual de la cola (rho = |Q| / C_q)."""
        return len(self.queue) / self.queue_capacity

    def update_state(self) -> None:
        """
        Actualiza el estado FSM del enrutador de acuerdo a los umbrales de ocupacion.
        """
        ratio = self.occupancy_ratio
        if ratio >= self.crit_threshold:
            self.state = NodeState.CONGESTED
        elif ratio >= self.alert_threshold:
            self.state = NodeState.ALERT
        else:
            self.state = NodeState.NORMAL

    def receive_packet(self, packet: Packet) -> bool:
        """
        Gestiona la recepcion de un paquete entrante.
        Si la cola y el bufer entrante no superan la capacidad maxima, se acepta el paquete.
        En caso contrario, se descarta el paquete y se incrementa el contador de perdidas.

        Retorna:
        --------
        bool
            True si el paquete fue encolado con exito, False si fue descartado por cola llena.
        """
        if len(self.queue) + len(self.incoming_buffer) < self.queue_capacity:
            self.incoming_buffer.append(packet)
            return True
        else:
            self.dropped_queue_full += 1
            self.model.total_dropped += 1
            return False

    def flush_incoming_buffer(self) -> None:
        """
        Transfiere los paquetes recibidos en el bufer entrante hacia la cola principal FIFO.
        """
        while self.incoming_buffer and len(self.queue) < self.queue_capacity:
            self.queue.append(self.incoming_buffer.pop(0))
        if self.incoming_buffer:
            self.dropped_queue_full += len(self.incoming_buffer)
            self.model.total_dropped += len(self.incoming_buffer)
            self.incoming_buffer.clear()

    def process_and_forward(self) -> None:
        """
        Procesa hasta C_ell paquetes de la cola principal en el tick actual:
        - Si el paquete alcanzo su destino final, se registra su entrega y se computa su latencia.
        - Si el paquete requiere continuar en transito, se delega en la estrategia activa la
          seleccion del siguiente salto vecino y se transmite.
        """
        packets_to_send = min(self.link_capacity, len(self.queue))
        for _ in range(packets_to_send):
            if not self.queue:
                break
            packet = self.queue.popleft()
            packet.hops += 1

            # Caso 1: Destino alcanzado en este nodo
            if packet.dst == self.node_id:
                self.delivered_count += 1
                self.model.on_packet_delivered(packet)
                continue

            # Caso 2: Delegacion en la estrategia de enrutamiento
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
    Clase Principal del Modelo Basado en Agentes para la Simulacion de Congestion en Redes.
    Administra la topologia, la ejecucion paso a paso (step) y la sincronizacion de telemetria.
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
        """
        Instancia el modelo completo con la configuracion experimental especificada.
        """
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

        # Fijar semillas para reproducibilidad determinista
        random.seed(seed)
        np.random.seed(seed)

        # Generacion de la topologia Watts-Strogatz
        self.graph = TopologyFactory.create_watts_strogatz(
            n=num_nodes, k=k_neighbors, p=rewire_prob, seed=seed
        )
        self.all_pairs_distances: Dict[int, Dict[int, int]] = dict(
            nx.all_pairs_shortest_path_length(self.graph)
        )
        self.betweenness_centrality = nx.betweenness_centrality(self.graph)

        # Instanciacion de los 50 agentes enrutadores
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

        # Variables de estado global de la simulacion
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
        """Registra la entrega exitosa de un paquete y almacena su latencia extremo a extremo."""
        self.total_delivered += 1
        self.step_delivered_count += 1
        latency = self.current_step - packet.t_gen
        self.latencies_history.append(latency)

    def inject_traffic(self) -> None:
        """
        Fase de generacion de trafico:
        Cada nodo genera estocasticamente un paquete con probabilidad lambda hacia un destino uniforme.
        Si la estrategia activa senala condicion de freno (throttling), la tasa se reduce al 50%.
        """
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
        """
        Ejecuta un ciclo discreto de simulacion (tick temporal):
        1. Generacion e inyeccion estocastica de trafico.
        2. Integracion de paquetes del bufer entrante a las colas.
        3. Sensado local de ocupacion para actualizar estados de saturacion.
        4. Procesamiento y reenvio concurrente en orden aleatorizado.
        5. Actualizacion posterior de estados.
        6. Registro de metricas en el observador.
        """
        self.step_generated_count = 0
        self.step_delivered_count = 0
        self.step_dropped_count = 0

        # 1. Inyeccion
        self.inject_traffic()

        # 2. Vaciado de buferes entrantes
        for agent in self.agents:
            agent.flush_incoming_buffer()

        # 3. Sensado de estado previo
        for agent in self.agents:
            agent.update_state()

        # 4. Procesamiento y reenvio concurrente
        agent_order = self.agents.copy()
        random.shuffle(agent_order)
        for agent in agent_order:
            agent.process_and_forward()

        # 5. Actualizacion posterior de estado
        for agent in self.agents:
            agent.update_state()

        # 6. Registro de telemetria
        self.metrics.record_step(self)
        self.current_step += 1

    def run(self, steps: Optional[int] = None) -> pd.DataFrame:
        """
        Ejecuta la simulacion completa por el numero total de pasos configurado.

        Parametros:
        -----------
        steps : Optional[int]
            Numero de pasos a ejecutar (por defecto max_steps = 300).

        Retorna:
        --------
        pd.DataFrame
            Serie temporal con todas las metricas recolectadas tick a tick.
        """
        total_steps = steps or self.max_steps
        for _ in range(total_steps):
            self.step()
        return self.metrics.get_dataframe()
