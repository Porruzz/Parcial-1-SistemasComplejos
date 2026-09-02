"""
topology.py
===========
Implementación del Patrón Factory para la construcción determinista y conexa de redes complejas.
"""

import random
import networkx as nx


class TopologyFactory:
    """Factoría encargada de generar topologías de redes complejas conexas."""
    
    @staticmethod
    def create_watts_strogatz(n: int = 50, k: int = 4, p: float = 0.10, seed: int = 42) -> nx.Graph:
        """
        Genera una red conexa de Watts-Strogatz (Mundo Pequeño).
        Garantiza que el grafo sea 100% conexo.
        """
        rng = random.Random(seed)
        for attempt in range(50):
            current_seed = seed + attempt
            G = nx.watts_strogatz_graph(n, k, p, seed=current_seed)
            if nx.is_connected(G):
                return G

        # Si tras varios intentos quedan componentes aislados, conectarlos
        G = nx.watts_strogatz_graph(n, k, p, seed=seed)
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            u = rng.choice(list(components[i]))
            v = rng.choice(list(components[i + 1]))
            G.add_edge(u, v)
        return G

    @staticmethod
    def create_barabasi_albert(n: int = 50, m: int = 2, seed: int = 42) -> nx.Graph:
        """Genera una red Libre de Escala (Barabási-Albert) para pruebas adicionales."""
        return nx.barabasi_albert_graph(n, m, seed=seed)
