from LayerSlicing.ZSlicer import ZSlicer
from GCode.GCodeParser import GCodeEvaluator
from Rendering.GCodeVisualizer3D import GCodeVisualizer3D

def main():
    z_slicer = ZSlicer()
    gcode_eval = GCodeEvaluator()

    layer_visualizer = GCodeVisualizer3D(z_slicer, gcode_eval)
    layer_visualizer.show()


if __name__ == "__main__":
    main()