import matplotlib.pyplot as plt

from LayerSlicing.ZSlicer import ZSlicer

class LayerRenderer:
    def __init__(self, z_slicer):
        self.z_slicer = z_slicer
        self.plots = []


    def render_all_slices(self):
        for i in range(len(self.z_slicer.get_slices())):
            self.render_slice(i)


    def initialize_plot(self, z_slice):
        # for the given z_slice, plots each vertex as a point, and draws lines between connected vertices

        fig, ax = plt.subplots()
        self.plots.append(ax)

        z = z_slice.z0
        ax.set_title(f'Z Slice at {z:.2f}')

        for vertex in z_slice.vertices:
            ax.plot(vertex[0], vertex[1], 'bo')

        print(f"Rendering slice at z={z} with {len(z_slice.vertices)} vertices and {len(z_slice.edges)} edges.")
        for edge in z_slice.edges:
            v1 = z_slice.vertices[edge[0]]
            v2 = z_slice.vertices[edge[1]]
            ax.plot([v1[0], v2[0]], [v1[1], v2[1]], 'r-')

        plt.show()



    def render_slice(self, index):
        z_slice = self.z_slicer.get_slices()[index]

        self.initialize_plot(z_slice)


