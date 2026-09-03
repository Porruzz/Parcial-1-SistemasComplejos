"""
Modulo de Generacion de Topologias de Red (src/topology.py)
===========================================================
Implementa el Patron de Diseno Creacional Factory (TopologyFactory) para la
construccion determinista, reproducible y completamente conexa de grafos de redes complejas.

La topologia primaria utilizada es el modelo de Mundo Pequeno de Watts-Strogatz (1998),
el cual interpola entre un reticulo regular y un grafo aleatorio preservando un alto
coeficiente de agrupamiento local y caminos caracteristicos cortos mediante enlaces atajo.
"""

import random
import networkx as nx


class TopologyFactory:
    """
    Factoria encargada de instanciar y validar grafos de redes complejas.
    Asegura la propiedad de conexidad global necesaria para el enrutamiento de paquetes.
    """
    
    @staticmethod
    def create_watts_strogatz(
        n: int = 50,
        k: int = 4,
        p: float = 0.10,
        seed: int = 42
    ) -> nx.Graph:
        """
        Construye una red de Mundo Pequeno de Watts-Strogatz garantizando conexidad total.

        Parametros:
        -----------
        n : int
            Numero total de nodos en la red (por defecto 50).
        k : int
            Grado inicial de cada nodo en el anillo regular (debe ser par, por defecto 4).
        p : float
            Probabilidad de reconexion de cada enlace (por defecto 0.10).
        seed : int
            Semilla determinista para la generacion pseudoaleatoria.

        Retorna:
        --------
        nx.Graph
            Grafo no dirigido, simple y 100% conexo.

        Logica del Algoritmo:
        ---------------------
        1. Intenta generar el grafo con la semilla base y semillas incrementales (hasta 50 intentos)
           verificando si nx.is_connected(G) es True.
        2. Si el grafo resulta desconexo tras los intentos, une secuencialmente las componentes
           conexas mediante la adicion de un enlace minimo entre nodos aleatorios de cada componente,
           preservando la estructura global.
        """
        rng = random.Random(seed)
        
        # Fase 1: Intentos deterministas con semillas incrementales para hallar un grafo conexo natural
        for attempt in range(50):
            current_seed = seed + attempt
            grafo = nx.watts_strogatz_graph(n, k, p, seed=current_seed)
            if nx.is_connected(grafo):
                return grafo

        # Fase 2: Mecanismo de respaldo para forzar conexidad uniendo componentes disjuntas
        grafo = nx.watts_strogatz_graph(n, k, p, seed=seed)
        componentes = list(nx.connected_components(grafo))
        for i in range(len(componentes) - 1):
            nodo_u = rng.choice(list(componentes[i]))
            nodo_v = rng.choice(list(componentes[i + 1]))
            grafo.add_edge(nodo_u, nodo_v)
            
        return grafo

    @staticmethod
    def create_barabasi_albert(
        n: int = 50,
        m: int = 2,
        seed: int = 42
    ) -> nx.Graph:
        """
        Construye una red Libre de Escala de Barabasi-Albert mediante enlace preferencial.

        Parametros:
        -----------
        n : int
            Numero total de nodos.
        m : int
            Numero de enlaces con los que se conecta cada nuevo nodo a los existentes.
        seed : int
            Semilla pseudoaleatoria.

        Retorna:
        --------
        nx.Graph
            Grafo libre de escala con distribucion de grado de ley de potencia.
        """
        return nx.barabasi_albert_graph(n, m, seed=seed)
