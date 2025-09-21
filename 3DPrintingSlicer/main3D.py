from LayerSlicing.ZSlicer import ZSlicer
from Rendering.LayerVisualizer3D import LayerVisualizer3D

def main():
    z_slicer = ZSlicer()
    layer_visualizer = LayerVisualizer3D(z_slicer)
    layer_visualizer.show()


if __name__ == "__main__":
    main()