import sys

from Rendering.LayerRenderer import LayerRenderer
from LayerSlicing.ZSlicer import ZSlicer

def main():
    file_name = "/Users/pranavsukesh/Documents/GitHub/3DPrintingSlicer/3DPrintingSlicer/STLFiles/20mm_cube.stl"

    z_slicer = ZSlicer()
    z_slicer.compute_slices_from_stl(True, file_name, num_slices=20)

    layer_renderer = LayerRenderer(z_slicer)
    layer_renderer.render_all_slices()


if __name__ == "__main__":
    main()