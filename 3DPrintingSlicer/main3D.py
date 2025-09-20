from LayerSlicing.ZSlicer import ZSlicer
from Rendering.LayerVisualizer3D import LayerVisualizer3D

def main():
    file_name = "/Users/pranavsukesh/Documents/GitHub/3DPrintingSlicer/3DPrintingSlicer/STLFiles/LowPolyBenchy.stl"

    z_slicer = ZSlicer()
    z_slicer.compute_slices_from_stl(False, file_name, specify_height=False, num=100)

    layer_visualizer = LayerVisualizer3D(z_slicer)
    layer_visualizer.show()


if __name__ == "__main__":
    main()