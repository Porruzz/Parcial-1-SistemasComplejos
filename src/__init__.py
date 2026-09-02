"""
src package initialization
"""
from src.model import NetworkCongestionModel, RouterAgent, Packet, NodeState
from src.strategies import BaselineShortestPathStrategy, DistributedBackpressureStrategy
from src.topology import TopologyFactory
from src.metrics import MetricsObserver
