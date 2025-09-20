from LayerSlicing.ZSlicer import ZSlicer
from Rendering.LayerRenderer import LayerRenderer
from Perimeters.PerimeterGenerator import PerimeterGenerator

def main():
    file_name = "STLFiles/20mm_cube.stl"

    z_slicer = ZSlicer()
    z_slicer.compute_slices_from_stl(True, file_name, specify_height=False, num=100)

    #layer_renderer = LayerRenderer(z_slicer)
    #layer_renderer.render_all_slices()

    for z_slice in z_slicer.get_slices():
        perimeter_generator = PerimeterGenerator(z_slice)
        perimeter_generator.createPerimeters(0.5,2)



if __name__ == "__main__":
    main()