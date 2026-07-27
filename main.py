"""
Punto de entrada de la aplicación Traductor de Juegos en Tiempo Real.
"""

import sys
import os

# Agregar el directorio raíz al path para importar 'src'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
