"""
main.py
=======
Punto de entrada principal (CLI) del proyecto de Sistemas Complejos.
Permite ejecutar experimentos por lotes, generar figuras científicas y lanzar la demostración interactiva en vivo.

Uso:
  python main.py --experiment                     # Ejecuta las 60 simulaciones factoriales
  python main.py --plot                           # Genera las figuras científicas en figures/
  python main.py --demo                           # Demostración interactiva en vivo (Con Control, Alta Carga)
  python main.py --demo --condition "Sin Control" # Demostración sin control
  python main.py --all                            # Ejecuta experimentos, gráficas e informe
"""

import argparse
import sys
from src.experiments import run_experiments
from src.plotting import generate_all_plots
from src.visualizer import run_live_visualizer


def main():
    parser = argparse.ArgumentParser(
        description="Sistema Basado en Agentes para el Control Descentralizado de Congestión en Redes de Datos."
    )
    parser.add_argument("--experiment", action="store_true", help="Ejecuta la matriz experimental completa (60 corridas).")
    parser.add_argument("--plot", action="store_true", help="Genera todas las figuras científicas (300 DPI) en figures/.")
    parser.add_argument("--demo", action="store_true", help="Lanza el visualizador interactivo en tiempo real.")
    parser.add_argument("--condition", type=str, default="Con Control", choices=["Sin Control", "Con Control"], help="Condición para la demo.")
    parser.add_argument("--load", type=str, default="Alta", choices=["Baja", "Media", "Alta"], help="Nivel de carga para la demo.")
    parser.add_argument("--all", action="store_true", help="Ejecuta la suite experimental completa y regenera todas las gráficas.")

    args = parser.parse_args()

    if len(sys.argv) == 1 or args.all:
        print(">> Ejecutando pipeline completo...")
        run_experiments()
        generate_all_plots()
        print("\n>> Proceso finalizado con éxito.")
        return

    if args.experiment:
        run_experiments()

    if args.plot:
        generate_all_plots()

    if args.demo:
        print(f">> Iniciando demostración visual en vivo: Condición='{args.condition}', Carga='{args.load}'...")
        run_live_visualizer(condition=args.condition, load=args.load)


if __name__ == "__main__":
    main()
