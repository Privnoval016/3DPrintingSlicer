import sys

from PyQt5.QtWidgets import QApplication

from Rendering.InfillVisualizer3D import InfillVisualizer3D
from LayerSlicing.ZSlicer import ZSlicer
from GCode.GCodeParser import GCodeEvaluator

def main():

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    z_slicer = ZSlicer()
    gcode_evaluator = GCodeEvaluator()

    window = InfillVisualizer3D(z_slicer, gcode_evaluator)
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()