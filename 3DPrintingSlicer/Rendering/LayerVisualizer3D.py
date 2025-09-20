import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import numpy as np

class LayerVisualizer3D:
    def __init__(self, z_slicer, line_color='blue', line_alpha=0.5, line_width=1):
        self.z_slicer = z_slicer
        self.slices = []
        self.line_color = line_color
        self.line_alpha = line_alpha
        self.line_width = line_width

        self.fig = None
        self.ax = None

        self.current_index = 0
        self.all_lines = []


    def _compute_axis_limits(self):
        x_dim = np.empty(2)
        y_dim = np.empty(2)
        z_dim = np.empty(2)

        for z_slice in self.z_slicer.get_slices():
            if len(z_slice.vertices) == 0:
                continue
            x_coords = z_slice.vertices[:, 0]
            y_coords = z_slice.vertices[:, 1]
            z_coords = z_slice.vertices[:, 2]
            x_dim = np.array([min(x_dim[0], np.min(x_coords)),
                                   max(x_dim[1], np.max(x_coords))]) \
                if x_dim.size else np.array(
                [np.min(x_coords), np.max(x_coords)])
            y_dim = np.array([min(y_dim[0], np.min(y_coords)),
                                   max(y_dim[1], np.max(y_coords))]) \
                if y_dim.size else np.array(
                [np.min(y_coords), np.max(y_coords)])
            z_dim = np.array([min(z_dim[0], np.min(z_coords)),
                                   max(z_dim[1], np.max(z_coords))]) \
                if z_dim.size else np.array(
                [np.min(z_coords), np.max(z_coords)])

        self.x_min, self.x_max = x_dim
        self.y_min, self.y_max = y_dim
        self.z_min, self.z_max = z_dim


    def add_next_slice(self):
        if self.current_index < len(self.slices):
            slice_data = self.slices[self.current_index]

            vertices = slice_data.vertices
            edges = slice_data.edges
            lines = np.array([[vertices[edge[0]], vertices[edge[1]]] for edge in edges])

            line_collection = Line3DCollection(
                lines, colors=self.line_color, linewidths=self.line_width, alpha=self.line_alpha
            )
            self.ax.add_collection3d(line_collection)
            self.all_lines.append(line_collection)
            self.current_index += 1
            plt.draw()

    def remove_last_slice(self):
        if self.current_index > 0:
            self.current_index -= 1
            line_collection = self.all_lines.pop()
            line_collection.remove()
            plt.draw()

    def on_key_press(self, event):
        if event.key in ['right', 'up']:
            self.add_next_slice()
        elif event.key in ['left', 'down']:
            self.remove_last_slice()

    def show(self):
        self.slices = self.z_slicer.get_slices()

        self._compute_axis_limits()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_xlim(self.x_min - 1, self.x_max + 1)
        self.ax.set_ylim(self.y_min - 1, self.y_max + 1)
        self.ax.set_zlim(self.z_min - 1, self.z_max + 1)

        # Connect key press
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)


        plt.show()
