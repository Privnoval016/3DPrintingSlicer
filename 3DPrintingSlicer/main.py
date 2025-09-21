from LayerSlicing.ZSlicer import ZSlicer
from Rendering.LayerRenderer import LayerRenderer
from Perimeters.PerimeterGenerator import PerimeterGenerator
from Infill.InfillGenerator import InfillGenerator
from Infill.InfillSlice import InfillSlice
import matplotlib.pyplot as plt


def main():
    file_name = "STLFiles/20mm_cube.stl"

    line_width = .5
    wall_count = 4

    z_slicer = ZSlicer()
    z_slicer.compute_slices_from_stl(file_name, specify_height=False, num=100)

    #layer_renderer = LayerRenderer(z_slicer)
    #layer_renderer.render_all_slices()

    for z_slice in z_slicer.get_slices():
        z0 = z_slice.z0
        perimeter_generator = PerimeterGenerator(z_slice)
        perimeters = perimeter_generator.createPerimeters(line_width, wall_count)
        print('Perimeter Generation Done')
        infill_generator = InfillGenerator()
        infill = infill_generator.create_infill(perimeter_generator.polygons, line_width, wall_count, z_slice.z0)
        print('Infill Generation Done')
        infill_vertices, infill_edges = infill_generator.get_vertices_edges()
        infill_slice = InfillSlice(z0, perimeters, infill_vertices, infill_edges)

        fig, ax = plt.subplots()

        if infill is None:
            continue
        for poly in perimeters:
            x, y = poly.exterior.xy
            ax.fill(x, y, alpha=0.5, fc='lightblue', ec='black')

        for line in infill.geoms:
            x, y = line.xy
            ax.plot(x, y, color="red", linewidth=2)

        ax.set_aspect("equal")
        plt.show()

if __name__ == "__main__":
    main()