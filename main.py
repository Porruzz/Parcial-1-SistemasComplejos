"""
Punto de Entrada Principal y CLI Unificado (main.py)
===================================================
Orquestador de linea de comandos para la ejecucion de experimentos factoriales,
generacion de figuras cientificas a 300 DPI y despliegue del visualizador interactivo.

Modos de Uso por Terminal:
--------------------------
1. Ejecucion del protocolo experimental completo (60 corridas con IC 95%):
   python main.py --experiment

2. Generacion de figuras cientificas a 300 DPI en figures/:
   python main.py --plot

3. Demostracion dinamica interactiva en tiempo real:
   python main.py --demo --condition "Con Control" --load "Alta"
   python main.py --demo --condition "Sin Control" --load "Alta"

4. Pipeline integral automatizado (experimentos + graficas):
   python main.py --all
"""

import argparse
import sys
from src.experiments import run_experiments
from src.plotting import generate_all_plots
from src.visualizer import run_live_visualizer


def main() -> None:
    """
    Parsea los argumentos de linea de comandos y despacha la ejecucion al modulo correspondiente.
    """
    parser = argparse.ArgumentParser(
        description="Modelo Basado en Agentes para el Control Descentralizado de Congestion en Redes Complejas."
    )
    parser.add_argument(
        "--experiment",
        action="store_true",
        help="Ejecuta la matriz experimental completa (60 corridas factoriales con calculo de IC 95%)."
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Genera las figuras cientificas en alta resolucion (300 DPI) en el directorio figures/."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Lanza el visualizador dinamico interactivo en tiempo real con NetworkX y Matplotlib."
    )
    parser.add_argument(
        "--condition",
        type=str,
        default="Con Control",
        choices=["Sin Control", "Con Control"],
        help="Politica de enrutamiento a evaluar en la demostracion interactiva."
    )
    parser.add_argument(
        "--load",
        type=str,
        default="Alta",
        choices=["Baja", "Media", "Alta"],
        help="Nivel de inyeccion de trafico (lambda) para la demostracion interactiva."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ejecuta secuencialmente la suite experimental y regenera las figuras."
    )

    args = parser.parse_args()

    # Si no se pasan argumentos o se solicita --all, ejecutar pipeline completo
    if len(sys.argv) == 1 or args.all:
        print(">> Ejecutando pipeline integral...")
        run_experiments()
        generate_all_plots()
        print("\n>> Pipeline completado exitosamente.")
        return

    # Despacho segun banderas especificas
    if args.experiment:
        run_experiments()

    if args.plot:
        generate_all_plots()

    if args.demo:
        print(f">> Iniciando visualizador en vivo: Condicion='{args.condition}', Carga='{args.load}'...")
        run_live_visualizer(condition=args.condition, load=args.load)


if __name__ == "__main__":
    main()
