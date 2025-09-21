from PyQt5.QtWidgets import QApplication, QFileDialog
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.widgets import Slider, CheckButtons, Button
import numpy as np

from Perimeters.PerimeterGenerator import PerimeterGenerator


class PerimeterVisualizer3D:
    def __init__(self, z_slicer, line_color='blue', line_alpha=0.5, line_width=1):
        self.button = None
        self.visible_slices = {}
        self.z_slicer = z_slicer
        self.slices = []
        self.line_color = line_color
        self.line_alpha = line_alpha
        self.line_width = line_width

        self.fig = None
        self.ax = None

        self.current_index = 0
        self.all_lines = []

        self.show_all_previous = True
        self.line_collections = []
        self.slider = None
        self.checkbox = None

        self.generate_plot()


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

        max_bound = np.max([x_dim[1]-x_dim[0], y_dim[1]-y_dim[0], z_dim[1]-z_dim[0]]) / 2

        self.x_min = self.y_min = -max_bound
        self.x_max = self.y_max = max_bound
        self.z_min = z_dim[0]
        self.z_max = z_dim[0] + 2 * max_bound


    def on_key_press(self, event):
        if event.key in ['right', 'up']:
            new_val = min(self.slider.val + 1, len(self.slices)-1)
            self.slider.set_val(new_val)
        elif event.key in ['left', 'down']:
            new_val = max(self.slider.val - 1, 0)
            self.slider.set_val(new_val)


    def toggle_show_all(self, label):
        self.show_all_previous = not self.show_all_previous
        self.update_slices(self.slider.val)


    def disable_slices(self):
        for lc in self.visible_slices.values():
            lc.remove()
        self.visible_slices = {}
        self.fig.canvas.draw_idle()


    def update_slices(self, val):
        index = int(self.slider.val)

        if index < 0 or index >= len(self.slices):
            return

        if self.show_all_previous:
            desired_slices = set(range(index + 1))
        else:
            desired_slices = {index}

        current_slices = set(self.visible_slices.keys())

        # Slices to remove
        for i in current_slices - desired_slices:
            self.visible_slices[i].remove()
            del self.visible_slices[i]

        # Slices to add
        for i in desired_slices - current_slices:
            slice_data = self.slices[i]

            perimeter_generator = PerimeterGenerator(slice_data)
            polygons = perimeter_generator.create_polygons(slice_data)

            lines = []
            for polygon in polygons:
                x, y = polygon.exterior.xy
                z = np.full_like(x, slice_data.z0)
                points = np.array([x, y, z]).T
                for j in range(len(points) - 1):
                    lines.append([points[j], points[j + 1]])

            lc = Line3DCollection(lines, colors=self.line_color,
                                  linewidths=self.line_width,
                                  alpha=self.line_alpha)
            self.ax.add_collection3d(lc)
            self.visible_slices[i] = lc

        z_val = self.slices[index].z0
        self.slider.label.set_text(f'z = {z_val:.2f} mm')

        self.fig.canvas.draw_idle()

    def load_file(self, event=None):
        filename = pick_file()
        if not filename:
            return

        for lc in self.visible_slices.values():
            lc.remove()
        self.visible_slices.clear()

        print(f"Loading file: {filename}")

        self.z_slicer.compute_slices_from_stl(filename, specify_height=False, num=100)
        self.current_index = 0
        self.visible_slices = {}
        self.load_slices()

    def generate_plot(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('x (mm)')
        self.ax.set_ylabel('y (mm)')
        self.ax.set_zlabel('z (mm)')

        ax_slider = plt.axes([0.9, 0.1, 0.05, 0.7])
        self.slider = Slider(
            ax_slider,
            'Slice',
            0, 1,
            valinit=0,
            valstep=1,
            orientation='vertical'
        )
        self.slider.on_changed(self.update_slices)

        ax_checkbox = plt.axes([0.05, 0.05, 0.2, 0.2])
        self.checkbox = CheckButtons(ax_checkbox, ['Show All\nLayers'],
                                     [self.show_all_previous])
        self.checkbox.on_clicked(self.toggle_show_all)

        ax_button = plt.axes([0.1, 0.7, 0.1, 0.05])
        self.button = Button(ax_button, 'Load File')
        self.button.on_clicked(self.load_file)

        plt.suptitle('Generating 3D Layer Visualization', fontsize=16,
                     fontweight='bold')

        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

    def load_slices(self):
        self.slices = self.z_slicer.get_slices()

        self._compute_axis_limits()
        self.ax.set_xlim(self.x_min - 1, self.x_max + 1)
        self.ax.set_ylim(self.y_min - 1, self.y_max + 1)
        self.ax.set_zlim(self.z_min - 1, self.z_max + 1)

        self.slider.valmin = 0
        self.slider.valmax = len(self.z_slicer.get_slices()) - 1
        self.slider.ax.set_ylim(0, max(0, len(self.slices) - 1))
        self.slider.set_val(0)

        self.update_slices(0)

    def show(self):
        plt.show()

def pick_file():
    # QApplication must exist only once
    app = QApplication.instance() or QApplication(sys.argv)
    filename, _ = QFileDialog.getOpenFileName(
        None, "Select STL file", "", "STL Files (*.stl);;All Files (*)"
    )
    return filename