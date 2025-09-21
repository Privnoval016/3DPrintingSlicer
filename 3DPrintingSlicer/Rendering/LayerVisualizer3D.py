from PyQt5.QtWidgets import QApplication, QFileDialog
import sys
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.widgets import Slider, CheckButtons, Button, TextBox
import numpy as np


class LayerVisualizer3D:
    def __init__(self, z_slicer, line_color='blue', line_alpha=0.5, line_width=1):
        self.ignore_checkbox = False
        self.regen_button = None
        self.ignore_regen_callback = False
        self.gen_num_cached = 1
        self.height_toggle_checkbox = None
        self.un_height_toggle_checkbox = None
        self.filename = None
        self.generation_num = 1

        self.specify_height = True
        self.specify_height_cached = False

        self.text_box = None
        self.load_button = None
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
        self.show_layers_checkbox = None

        self.generate_plot()


    def _compute_axis_limits(self):
        x_dim = np.zeros(2)
        y_dim = np.zeros(2)
        z_dim = np.zeros(2)

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

        self.x_min = (x_dim[0] + x_dim[1]) / 2 - max_bound
        self.x_max = self.x_min + 2 * max_bound
        self.y_min = (y_dim[0] + y_dim[1]) / 2 - max_bound
        self.y_max = self.y_min + 2 * max_bound
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
            vertices = slice_data.vertices
            edges = slice_data.edges
            lines = np.array(
                [[vertices[edge[0]], vertices[edge[1]]] for edge in edges])

            if len(lines) == 0:
                continue

            lc = Line3DCollection(lines, colors=self.line_color,
                                  linewidths=self.line_width,
                                  alpha=self.line_alpha)
            self.ax.add_collection3d(lc)
            self.visible_slices[i] = lc

        z_val = self.slices[index].z0
        self.slider.label.set_text(f'z = {z_val:.2f} mm')

        self.fig.canvas.draw_idle()

    def load_file(self, event=None):
        self.filename = pick_file()
        if not self.filename:
            return

        print(f"Loading file: {self.filename}")

        self.gen_num_cached = self.generation_num
        self.text_box.set_val(str(self.generation_num))
        if not self.specify_height_cached == self.specify_height:
            self.height_toggle_checkbox.set_active(0)  # Uncheck the box if the cache is different from the actual value

        self.regenerate()

    def regenerate(self):
        for lc in self.visible_slices.values():
            lc.remove()
        self.visible_slices.clear()

        if not self.filename:
            return

        self.z_slicer.compute_slices_from_stl(self.filename, specify_height=self.specify_height, num=self.generation_num)
        self.current_index = 0
        self.visible_slices = {}
        self.load_slices()

    def on_checkbox(self, label):
        if self.ignore_checkbox:
            return

        self.ignore_checkbox = True

        # Determine which checkbox was clicked
        if label == 'Layer Thickness':
            self.specify_height_cached = True
            # Ensure mutual exclusivity
            if not self.height_toggle_checkbox.get_status()[0]:  # if A is unchecked, toggle back on
                self.height_toggle_checkbox.set_active(0)
            if self.height_toggle_checkbox.get_status()[1]:
                self.height_toggle_checkbox.set_active(1)

        elif label == 'Number of Layers':
            self.specify_height_cached = False
            if self.height_toggle_checkbox.get_status()[0]:
                self.height_toggle_checkbox.set_active(0)
            if not self.height_toggle_checkbox.get_status()[1]:
                self.height_toggle_checkbox.set_active(1)

        self.ignore_checkbox = False


    def update_generation_num_cached(self, text):
        if self.ignore_regen_callback:
            return

        try:
            value = int(text)
            if value > 0:
                self.gen_num_cached = value
            else:
                print("Please enter a positive integer.")
        except ValueError:
            print("Invalid input. Please enter a positive integer.")

    def update_generation(self, event):
        if ((self.generation_num == self.gen_num_cached and self.specify_height_cached == self.specify_height)
                or self.ignore_regen_callback):
            return

        if self.specify_height_cached and self.gen_num_cached >= (self.z_slicer.max_z - self.z_slicer.min_z) / 3:
            self.ignore_regen_callback = True
            self.gen_num_cached = self.generation_num
            self.text_box.set_val(str(self.generation_num))

            if not self.specify_height_cached == self.specify_height:
                self.height_toggle_checkbox.set_active(0)  # Uncheck the box if the cache is different from the actual value
            self.ignore_regen_callback = False
            print("Layer height too large for model height.")
            return

        if not self.specify_height_cached and self.gen_num_cached <= 1:
            self.ignore_regen_callback = True
            self.text_box.set_val(str(self.generation_num))
            self.gen_num_cached = self.generation_num
            if not self.specify_height_cached == self.specify_height:
                self.height_toggle_checkbox.set_active(1)  # Uncheck the box if the cache is different from the actual value
            self.ignore_regen_callback = False
            print("Number of layers must be greater than 1.")
            return

        self.generation_num = self.gen_num_cached
        self.specify_height = self.specify_height_cached
        self.regenerate()

    def generate_plot(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('x (mm)')
        self.ax.set_ylabel('y (mm)')
        self.ax.set_zlabel('z (mm)')

        # Slider for navigating slices
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

        # Checkbutton for showing all previous layers
        ax_layer_checkbox = plt.axes([0.01, 0.05, 0.2, 0.2])
        self.show_layers_checkbox = CheckButtons(ax_layer_checkbox, ['Show All\nLayers'],
                                                 [self.show_all_previous])
        self.show_layers_checkbox.on_clicked(self.toggle_show_all)

        # Button for loading STL file
        ax_button = plt.axes([0.01, 0.75, 0.1, 0.05])
        self.load_button = Button(ax_button, 'Load File')
        self.load_button.on_clicked(self.load_file)

        # Checkbox for specifying layer thickness
        ax_gen_checkbox = plt.axes([0.01, 0.5, 0.11, 0.22])
        self.height_toggle_checkbox = CheckButtons(ax_gen_checkbox,
                                                           ['Layer Thickness', 'Number of Layers'],
                                                           [self.specify_height, not self.specify_height])
        self.height_toggle_checkbox.on_clicked(self.on_checkbox)

        # Text box for entering generation number
        ax_text = plt.axes(
            [0.1, 0.44, 0.1, 0.05])  # [left, bottom, width, height]
        self.text_box = TextBox(ax_text, 'Value: ', initial=str(self.generation_num))
        self.text_box.on_submit(self.update_generation_num_cached)

        # Button for reapplying generation
        ax_button = plt.axes([0.01, 0.3, 0.19, 0.05])
        self.regen_button = Button(ax_button, 'Apply Changes')
        self.regen_button.label.set_fontsize(10)
        self.regen_button.on_clicked(self.update_generation)

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