import matplotlib.pyplot as plt
import numpy as np


class LayerRenderer:
    def __init__(self, z_slicer):
        self.z_slicer = z_slicer
        self.plots = []
        self.x_dim = np.empty(2)
        self.y_dim = np.empty(2)


    def render_all_slices(self):

        # Determine overall x and y limits across all slices

        print(self.z_slicer.get_slices()[0].vertices)

        for z_slice in self.z_slicer.get_slices():
            if len(z_slice.vertices) == 0:
                continue
            x_coords = z_slice.vertices[:, 0]
            y_coords = z_slice.vertices[:, 1]
            self.x_dim = np.array([min(self.x_dim[0], np.min(x_coords)), max(self.x_dim[1], np.max(x_coords))]) \
                if self.x_dim.size else np.array([np.min(x_coords), np.max(x_coords)])
            self.y_dim = np.array([min(self.y_dim[0], np.min(y_coords)), max(self.y_dim[1], np.max(y_coords))]) \
                if self.y_dim.size else np.array([np.min(y_coords), np.max(y_coords)])

        for i in range(len(self.z_slicer.get_slices())):
            self.render_slice(i)


    def initialize_plot(self, z_slice):
        # for the given z_slice, plots each vertex as a point, and draws lines between connected vertices

        fig, ax = plt.subplots()
        self.plots.append(ax)

        ax.set_xlim(self.x_dim[0] - 1, self.x_dim[1] + 1)
        ax.set_ylim(self.y_dim[0] - 1, self.y_dim[1] + 1)

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


