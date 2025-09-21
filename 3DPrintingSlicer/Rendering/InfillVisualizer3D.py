import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QSlider, QLabel,
                             QCheckBox,
                             QLineEdit, QRadioButton, QButtonGroup, QGroupBox,
                             QFileDialog, QProgressBar, QTextEdit, QSplitter,
                             QFrame, QGridLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
import matplotlib

from GCode.GCodeGenerator import GCodeGenerator

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import numpy as np


class InfillVisualizer3D(QMainWindow):
    def __init__(self, z_slicer, gcode_evaluator):
        super().__init__()
        self.output_filename = "output.gcode"
        self.line_width = 0.5
        self.wall_count = 3
        self.draw_infill = True
        self.autoplay = None
        self.z_slicer = z_slicer
        self.gcode_evaluator = gcode_evaluator
        self.filename = None
        self.slices = []
        self.visible_slices = {}
        self.visible_operation_lines = {}
        self.draw_operation_lines = True
        self.generation_num = 1
        self.specify_height = True
        self.show_all_previous = True

        self.step_duration = 500  # milliseconds

        self.setupUI()
        self.setupStyle()

    def setupUI(self):
        self.setWindowTitle("3D G-Code Visualizer")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel (controls)
        self.setupControlPanel(splitter)

        # Right panel (3D visualization)
        self.setupVisualizationPanel(splitter)

        # Set splitter proportions
        splitter.setSizes([350, 1050])

    def setupControlPanel(self, parent):
        from PyQt5.QtWidgets import QScrollArea

        # Create scroll area for the control panel
        scroll_area = QScrollArea()
        scroll_area.setFixedWidth(400)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        parent.addWidget(scroll_area)

        # Control panel container inside scroll area
        control_panel = QFrame()
        control_panel.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        scroll_area.setWidget(control_panel)

        layout = QVBoxLayout(control_panel)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title_label = QLabel("3D G-Code Visualizer")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # File operations group
        self.setupFileGroup(layout)

        # Navigation group
        self.setupNavigationGroup(layout)

        # Layer settings group
        self.setupLayerSettingsGroup(layout)

        # Display options group
        self.setupDisplayGroup(layout)

        # Status and progress
        self.setupStatusGroup(layout)

        # Add stretch to push everything to top
        layout.addStretch()

        control_panel.setMinimumHeight(800)

    def setupFileGroup(self, parent_layout):
        group = QGroupBox("File Operations")
        layout = QVBoxLayout(group)

        # Load file button
        self.load_button = QPushButton("Load STL/G-Code File")
        self.load_button.clicked.connect(self.load_file)
        layout.addWidget(self.load_button)

        # Current file label
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

        # Write G-code button and filename input
        write_layout = QHBoxLayout()
        self.write_button = QPushButton("Write G-Code to File")
        self.write_button.clicked.connect(self.write_gcode_to_file)
        write_layout.addWidget(self.write_button)
        self.output_file_input = QLineEdit(self.output_filename)
        self.output_file_input.setPlaceholderText("Output G-Code Filename")
        self.output_file_input.textChanged.connect(self.update_output_filename)
        write_layout.addWidget(self.output_file_input)

        layout.addLayout(write_layout)

        parent_layout.addWidget(group)

    def setupNavigationGroup(self, parent_layout):
        group = QGroupBox("Navigation")
        layout = QVBoxLayout(group)

        # Current layer/operation info
        self.current_info = QLabel("Layer: 0 / 0")
        layout.addWidget(self.current_info)

        # Slider for navigation
        self.navigation_slider = QSlider(Qt.Horizontal)
        self.navigation_slider.setMinimum(0)
        self.navigation_slider.setMaximum(0)
        self.navigation_slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.navigation_slider)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.prev_button.clicked.connect(self.previous_layer)
        self.next_button.clicked.connect(self.next_layer)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)

        #Playback speed control
        speed_layout = QHBoxLayout()
        self.slower_button = QPushButton("<")
        self.faster_button = QPushButton(">")
        self.slower_button.clicked.connect(self.slower_autoplay)
        self.faster_button.clicked.connect(self.faster_autoplay)
        speed_layout.addWidget(QLabel("Speed:"))
        speed_layout.addWidget(self.slower_button)
        speed_layout.addWidget(self.faster_button)
        layout.addLayout(speed_layout)

        # Auto-play controls
        autoplay_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")
        self.play_button.clicked.connect(self.start_autoplay)
        self.pause_button.clicked.connect(self.pause_autoplay)
        self.reset_button.clicked.connect(self.reset_view)
        autoplay_layout.addWidget(self.play_button)
        autoplay_layout.addWidget(self.pause_button)
        autoplay_layout.addWidget(self.reset_button)
        layout.addLayout(autoplay_layout)



        parent_layout.addWidget(group)

        # Setup auto-play timer
        self.autoplay_timer = QTimer()
        self.autoplay_timer.timeout.connect(self.autoplay_step)

    def setupLayerSettingsGroup(self, parent_layout):
        group = QGroupBox("Layer Settings")
        layout = QVBoxLayout(group)

        # Layer specification radio buttons
        self.layer_mode_group = QButtonGroup()
        self.thickness_radio = QRadioButton("Layer Thickness")
        self.count_radio = QRadioButton("Number of Layers")
        self.thickness_radio.setChecked(True)

        self.layer_mode_group.addButton(self.thickness_radio, 0)
        self.layer_mode_group.addButton(self.count_radio, 1)
        self.layer_mode_group.buttonClicked.connect(self.on_layer_mode_changed)

        layout.addWidget(self.thickness_radio)
        layout.addWidget(self.count_radio)

        # Value input
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        self.value_input = QLineEdit("1.0")
        self.value_input.returnPressed.connect(self.apply_all_settings)
        value_layout.addWidget(self.value_input)
        layout.addLayout(value_layout)

        # Line width input
        line_width_layout = QHBoxLayout()
        line_width_layout.addWidget(QLabel("Line Width (mm):"))
        self.line_width_input = QLineEdit("0.5")
        self.line_width_input.returnPressed.connect(self.apply_all_settings)
        line_width_layout.addWidget(self.line_width_input)
        layout.addLayout(line_width_layout)

        # Wall count input
        wall_count_layout = QHBoxLayout()
        wall_count_layout.addWidget(QLabel("Wall Count:"))
        self.wall_count_input = QLineEdit("3")
        self.wall_count_input.returnPressed.connect(self.apply_all_settings)
        wall_count_layout.addWidget(self.wall_count_input)
        layout.addLayout(wall_count_layout)

        # Apply button
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self.apply_all_settings)
        layout.addWidget(self.apply_button)

        parent_layout.addWidget(group)

    def setupDisplayGroup(self, parent_layout):
        group = QGroupBox("Display Options")
        layout = QVBoxLayout(group)

        # Show all layers checkbox
        self.show_all_checkbox = QCheckBox("Show All Previous Layers")
        self.show_all_checkbox.setChecked(True)
        self.show_all_checkbox.toggled.connect(self.toggle_show_all)
        layout.addWidget(self.show_all_checkbox)

        self.show_infill_checkbox = QCheckBox("Show Infill")
        self.show_infill_checkbox.setChecked(True)
        self.show_infill_checkbox.toggled.connect(self.toggle_show_infill)
        layout.addWidget(self.show_infill_checkbox)

        # Line properties
        line_layout = QGridLayout()
        line_layout.addWidget(QLabel("Line Width:"), 0, 0)
        self.line_width_slider = QSlider(Qt.Horizontal)
        self.line_width_slider.setRange(1, 10)
        self.line_width_slider.setValue(2)
        self.line_width_slider.valueChanged.connect(self.update_line_properties)
        line_layout.addWidget(self.line_width_slider, 0, 1)

        line_layout.addWidget(QLabel("Transparency:"), 1, 0)
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setRange(1, 100)
        self.alpha_slider.setValue(30)
        self.alpha_slider.valueChanged.connect(self.update_line_properties)
        line_layout.addWidget(self.alpha_slider, 1, 1)

        layout.addLayout(line_layout)

        # Plot bounds controls
        bounds_group = QGroupBox("Plot Bounds")
        bounds_layout = QGridLayout(bounds_group)

        # Auto bounds checkbox
        self.auto_bounds_checkbox = QCheckBox("Auto-fit bounds")
        self.auto_bounds_checkbox.setChecked(True)
        self.auto_bounds_checkbox.toggled.connect(self.toggle_auto_bounds)
        bounds_layout.addWidget(self.auto_bounds_checkbox, 0, 0, 1, 2)

        # Manual bounds inputs
        bounds_layout.addWidget(QLabel("X Min:"), 1, 0)
        self.x_min_input = QLineEdit("0")
        self.x_min_input.setEnabled(False)
        bounds_layout.addWidget(self.x_min_input, 1, 1)

        bounds_layout.addWidget(QLabel("X Max:"), 2, 0)
        self.x_max_input = QLineEdit("100")
        self.x_max_input.setEnabled(False)
        bounds_layout.addWidget(self.x_max_input, 2, 1)

        bounds_layout.addWidget(QLabel("Y Min:"), 3, 0)
        self.y_min_input = QLineEdit("0")
        self.y_min_input.setEnabled(False)
        bounds_layout.addWidget(self.y_min_input, 3, 1)

        bounds_layout.addWidget(QLabel("Y Max:"), 4, 0)
        self.y_max_input = QLineEdit("100")
        self.y_max_input.setEnabled(False)
        bounds_layout.addWidget(self.y_max_input, 4, 1)

        bounds_layout.addWidget(QLabel("Z Min:"), 5, 0)
        self.z_min_input = QLineEdit("0")
        self.z_min_input.setEnabled(False)
        bounds_layout.addWidget(self.z_min_input, 5, 1)

        bounds_layout.addWidget(QLabel("Z Max:"), 6, 0)
        self.z_max_input = QLineEdit("100")
        self.z_max_input.setEnabled(False)
        bounds_layout.addWidget(self.z_max_input, 6, 1)

        # Apply bounds button
        self.apply_bounds_button = QPushButton("Apply Bounds")
        self.apply_bounds_button.setEnabled(False)
        self.apply_bounds_button.clicked.connect(self.apply_custom_bounds)
        bounds_layout.addWidget(self.apply_bounds_button, 7, 0, 1, 2)

        layout.addWidget(bounds_group)

        # View controls
        view_layout = QHBoxLayout()
        self.reset_view_button = QPushButton("Reset View")
        self.fit_view_button = QPushButton("Fit to View")
        self.reset_view_button.clicked.connect(self.reset_camera)
        self.fit_view_button.clicked.connect(self.fit_to_view)
        view_layout.addWidget(self.reset_view_button)
        view_layout.addWidget(self.fit_view_button)
        layout.addLayout(view_layout)

        parent_layout.addWidget(group)

    def setupStatusGroup(self, parent_layout):
        group = QGroupBox("Status")
        layout = QVBoxLayout(group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        parent_layout.addWidget(group)

    def setupVisualizationPanel(self, parent):
        # 3D visualization panel
        viz_panel = QFrame()
        viz_panel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        parent.addWidget(viz_panel)

        layout = QVBoxLayout(viz_panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(12, 8), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')

        # Setup 3D plot
        self.ax.set_xlabel('X (mm)', fontsize=10)
        self.ax.set_ylabel('Y (mm)', fontsize=10)
        self.ax.set_zlabel('Z (mm)', fontsize=10)
        self.ax.set_title('3D Layer Visualization', fontsize=12,
                          fontweight='bold')

        layout.addWidget(self.canvas)

    def setupStyle(self):
        # Modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
                background-color: #3b3b3b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #64ffda;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #555555;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #64ffda;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #4fd3a6;
            }
            QLineEdit {
                padding: 6px;
                border: 2px solid #555555;
                border-radius: 4px;
                background-color: #404040;
                color: white;
            }
            QLineEdit:focus {
                border-color: #64ffda;
            }
            QCheckBox, QRadioButton {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #555555;
                background-color: #404040;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #64ffda;
                background-color: #64ffda;
                border-radius: 3px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #555555;
                background-color: #404040;
                border-radius: 8px;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #64ffda;
                background-color: #64ffda;
                border-radius: 8px;
            }
            QTextEdit {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                color: white;
                padding: 5px;
            }
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 5px;
                text-align: center;
                background-color: #404040;
            }
            QProgressBar::chunk {
                background-color: #64ffda;
                border-radius: 3px;
            }
            QFrame {
                background-color: #3b3b3b;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select STL or G-Code file",
            "",
            "STL Files (*.stl);;G-Code Files (*.gcode);;All Files (*)"
        )

        if filename:
            self.filename = filename
            self.file_label.setText(f"File: {os.path.basename(filename)}")
            self.log_status(f"Loaded file: {os.path.basename(filename)}")
            self.regenerate()

    def write_gcode_to_file(self):
        gcode_generator = GCodeGenerator(self.z_slicer.infill_slices)
        finished = gcode_generator.generate_gcode(self.output_filename)

        if finished:
            self.log_status(f"G-code written to {self.output_filename}")
            self.output_filename = "output.gcode"


    def update_output_filename(self, text):
        self.output_filename = text if text else "output.gcode"

    def regenerate(self):
        if not self.filename:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_status("Processing file...")

        # Clear existing visualizations
        self.ax.clear()
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_zlabel('Z (mm)')

        self.visible_slices = {}
        self.visible_operation_lines = {}

        try:
            if self.filename.lower().endswith('.stl'):
                self.draw_operation_lines = False
                self.z_slicer.compute_slices_from_stl(
                    self.filename,
                    specify_height=self.specify_height,
                    num=self.generation_num,
                    line_width=self.line_width,
                    wall_count=self.wall_count
                )
                self.progress_bar.setValue(50)
                self.load_slices()
            else:
                self.draw_operation_lines = True
                self.gcode_evaluator.parse(self.filename)
                self.progress_bar.setValue(50)
                self.load_from_gcode()

            self.progress_bar.setValue(100)
            self.log_status("File processed successfully!")

        except Exception as e:
            self.log_status(f"Error processing file: {str(e)}")
            print(f"Debug - Error details: {e}")  # For debugging
        finally:
            self.progress_bar.setVisible(False)

    def load_slices(self):
        self.slices = self.z_slicer.get_slices()
        self.navigation_slider.setMaximum(max(0, len(self.slices) - 1))
        self.navigation_slider.setValue(0)
        self.update_current_info()

        # Compute and apply axis limits for STL data
        self.compute_axis_limits()

        # Update the graphics after bounds are set
        self.update_graphics()

    def load_from_gcode(self):
        if not hasattr(self.gcode_evaluator, 'operations'):
            self.log_status("Error: G-code evaluator has no operations")
            return

        self.navigation_slider.setMaximum(
            max(0, len(self.gcode_evaluator.operations) - 1))
        self.navigation_slider.setValue(0)

        # Reset the gcode evaluator state
        self.gcode_evaluator.index = 0

        if hasattr(self.gcode_evaluator, 'actual_position'):
            self.gcode_evaluator.actual_position = [0, 0, 0]  # Reset to origin

        # Clear any existing operation lines
        for line_collection in self.visible_operation_lines.values():
            if line_collection in self.ax.collections:
                line_collection.remove()
        self.visible_operation_lines = {}

        # Set default printer bounds for G-code
        self.set_printer_bounds(235, 235, 235)

        self.update_current_info()
        self.log_status(
            f"Loaded G-code with {len(self.gcode_evaluator.operations)} operations")
        self.update_graphics()

    def compute_axis_limits(self):

        if not self.slices:
            return

        x_coords = []
        y_coords = []
        z_coords = []

        for slice_data in self.slices:
            if len(slice_data.vertices) > 0:
                x_coords.extend(slice_data.vertices[:, 0])
                y_coords.extend(slice_data.vertices[:, 1])
                z_coords.extend(slice_data.vertices[:, 2])

        if x_coords:
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            z_min, z_max = min(z_coords), max(z_coords)

            # Add some padding
            x_range = x_max - x_min
            y_range = y_max - y_min
            z_range = z_max - z_min
            max_range = max(x_range, y_range, z_range)

            # Center and expand to make it cubic
            x_center = (x_max + x_min) / 2
            y_center = (y_max + y_min) / 2
            z_center = (z_max + z_min) / 2

            half_range = max_range / 2 * 1.1  # 10% padding

            self.x_min = x_center - half_range
            self.x_max = x_center + half_range
            self.y_min = y_center - half_range
            self.y_max = y_center + half_range
            self.z_min = z_center - half_range
            self.z_max = z_center + half_range

            # Update the input fields with computed values
            self.x_min_input.setText(f"{self.x_min:.2f}")
            self.x_max_input.setText(f"{self.x_max:.2f}")
            self.y_min_input.setText(f"{self.y_min:.2f}")
            self.y_max_input.setText(f"{self.y_max:.2f}")
            self.z_min_input.setText(f"{self.z_min:.2f}")
            self.z_max_input.setText(f"{self.z_max:.2f}")

            # Apply the computed limits immediately if auto-bounds is enabled
            if self.auto_bounds_checkbox.isChecked():
                self.apply_axis_limits()
                self.log_status("Auto-computed bounds applied")

    def apply_axis_limits(self):
        try:
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
            y_min = float(self.y_min_input.text())
            y_max = float(self.y_max_input.text())
            z_min = float(self.z_min_input.text())
            z_max = float(self.z_max_input.text())

            self.ax.set_xlim(x_min, x_max)
            self.ax.set_ylim(y_min, y_max)
            self.ax.set_zlim(z_min, z_max)

            self.canvas.draw()

        except ValueError as e:
            self.log_status(f"Invalid bounds values: {e}")

    def toggle_auto_bounds(self, checked):
        # Enable/disable manual input fields
        self.x_min_input.setEnabled(not checked)
        self.x_max_input.setEnabled(not checked)
        self.y_min_input.setEnabled(not checked)
        self.y_max_input.setEnabled(not checked)
        self.z_min_input.setEnabled(not checked)
        self.z_max_input.setEnabled(not checked)
        self.apply_bounds_button.setEnabled(not checked)

        if checked and hasattr(self, 'slices') and self.slices:
            # Recompute and apply auto bounds
            self.compute_axis_limits()
        elif checked:
            self.log_status(
                "Auto bounds enabled - will apply when data is loaded")

        self.log_status(f"Auto bounds: {'enabled' if checked else 'disabled'}")

    def apply_custom_bounds(self):
        self.apply_axis_limits()
        self.log_status("Custom bounds applied")

    def set_printer_bounds(self, x_max=235, y_max=235, z_max=235):
        self.auto_bounds_checkbox.setChecked(False)
        self.toggle_auto_bounds(False)

        self.x_min_input.setText("0")
        self.x_max_input.setText(str(x_max))
        self.y_min_input.setText("0")
        self.y_max_input.setText(str(y_max))
        self.z_min_input.setText("0")
        self.z_max_input.setText(str(z_max))

        self.apply_axis_limits()
        self.log_status(f"Printer bounds set: {x_max}x{y_max}x{z_max}")

    def set_custom_bounds(self, x_min=0, x_max=100, y_min=0, y_max=100, z_min=0,
                          z_max=100):
        self.auto_bounds_checkbox.setChecked(False)
        self.toggle_auto_bounds(False)

        self.x_min_input.setText(str(x_min))
        self.x_max_input.setText(str(x_max))
        self.y_min_input.setText(str(y_min))
        self.y_max_input.setText(str(y_max))
        self.z_min_input.setText(str(z_min))
        self.z_max_input.setText(str(z_max))

        self.apply_axis_limits()

    def update_graphics(self):
        # Don't clear existing graphics for operation lines - we want them to persist
        if not self.draw_operation_lines:
            # Clear existing graphics for slices
            self.ax.clear()
            self.ax.set_xlabel('X (mm)')
            self.ax.set_ylabel('Y (mm)')
            self.ax.set_zlabel('Z (mm)')

        # Apply current axis limits
        self.apply_axis_limits()

        current_index = self.navigation_slider.value()

        if self.draw_operation_lines:
            self.update_operation_lines(current_index)
        else:
            self.update_slices(current_index)

        self.canvas.draw()

    def update_slices(self, index):
        if not self.slices or index >= len(self.slices):
            return

        line_width = self.line_width_slider.value()
        alpha = self.alpha_slider.value() / 100.0

        if self.show_all_previous:
            indices = range(index + 1)
        else:
            indices = [index]

        for i in indices:
            slice_data = self.slices[i]
            slice_vertices = slice_data.infill_slice.all_vertices if self.draw_infill else slice_data.vertices
            slice_edges = slice_data.infill_slice.all_edges if self.draw_infill else slice_data.edges
            if len(slice_vertices) == 0 or len(slice_edges) == 0:
                continue

            lines = []
            for edge in slice_edges:
                if edge[0] < len(slice_vertices) and edge[1] < len(
                        slice_vertices):
                    lines.append([slice_vertices[edge[0]],
                                  slice_vertices[edge[1]]])

            if lines:
                lc = Line3DCollection(lines, colors='blue',
                                      linewidths=line_width, alpha=alpha)
                self.ax.add_collection3d(lc)

        if index < len(self.slices):
            z_val = self.slices[index].z0 if hasattr(self.slices[index],
                                                     'z0') else index
            self.ax.set_title(f'Layer {index + 1}: z = {z_val:.2f} mm')

    def update_operation_lines(self, index):
        if not hasattr(self.gcode_evaluator,
                       'operations') or index < 0 or index >= len(
                self.gcode_evaluator.operations):
            return

        # If going backwards, reset everything and rebuild from scratch
        if index < self.gcode_evaluator.index:
            self.gcode_evaluator.index = 0
            self.gcode_evaluator.reset()
            # Clear all existing lines
            for line_collection in self.visible_operation_lines.values():
                if line_collection in self.ax.collections:
                    line_collection.remove()
            self.visible_operation_lines = {}

        line_width = self.line_width_slider.value()
        alpha = self.alpha_slider.value() / 100.0

        lines = []

        # Execute operations up to the current index
        while self.gcode_evaluator.index <= index:
            current_op_index = self.gcode_evaluator.index

            # Store the starting position
            start_pos = np.array(self.gcode_evaluator.actual_position.copy())

            # Execute the next command
            self.gcode_evaluator.execute_next_command()

            # Get the ending position
            end_pos = np.array(self.gcode_evaluator.actual_position.copy())

            # Check if we should draw this line (extruder on, movement occurred)
            should_draw = True
            if hasattr(self.gcode_evaluator, 'can_draw'):
                should_draw = self.gcode_evaluator.can_draw()

            # Only create new line collection if we don't already have one for this operation
            if (should_draw and not np.array_equal(start_pos, end_pos) and
                    current_op_index not in self.visible_operation_lines):
                # Create line for this single operation
                line = np.array([
                    [start_pos[0], start_pos[1], start_pos[2]],
                    [end_pos[0], end_pos[1], end_pos[2]]
                ])

                lines.append(line)


        lc = Line3DCollection(lines, colors='red',
                              linewidths=line_width, alpha=alpha)
        self.ax.add_collection3d(lc)
        self.visible_operation_lines[index] = lc

        # Update the title with current operation info
        current_op = index + 1
        total_ops = len(self.gcode_evaluator.operations)

        # Try to get current position for display
        try:
            pos = self.gcode_evaluator.actual_position
            pos_str = f"X:{pos[0]:.1f} Y:{pos[1]:.1f} Z:{pos[2]:.1f}"
            self.ax.set_title(f'Operation {current_op}/{total_ops} - {pos_str}')
        except:
            self.ax.set_title(f'Operation {current_op}/{total_ops}')

        # Log progress for debugging
        visible_lines = len(
            [lc for lc in self.visible_operation_lines.values() if
             lc in self.ax.collections])
        self.log_status(
            f"Op {current_op}/{total_ops}: {visible_lines} line segments visible")

    def on_slider_changed(self, value):
        self.update_current_info()
        self.update_graphics()

    def update_current_info(self):
        current = self.navigation_slider.value()
        maximum = self.navigation_slider.maximum()

        if self.draw_operation_lines:
            self.current_info.setText(
                f"Operation: {current + 1} / {maximum + 1}")
        else:
            self.current_info.setText(f"Layer: {current + 1} / {maximum + 1}")

    def previous_layer(self):
        current = self.navigation_slider.value()
        if current > 0:
            self.navigation_slider.setValue(current - 1)

    def next_layer(self):
        current = self.navigation_slider.value()
        maximum = self.navigation_slider.maximum()
        if current < maximum:
            self.navigation_slider.setValue(current + 1)

    def start_autoplay(self):
        self.autoplay = True
        self.autoplay_timer.start(self.step_duration)
        self.log_status("Auto-play started")

    def pause_autoplay(self):
        self.autoplay = False
        self.autoplay_timer.stop()
        self.log_status("Auto-play paused")

    def slower_autoplay(self):
        self.step_duration = min(self.step_duration + 100, 2000)
        print(self.step_duration)
        if not self.autoplay:
            return

        self.pause_autoplay()
        self.start_autoplay()

    def faster_autoplay(self):
        self.step_duration = max(self.step_duration - 100, 10)
        print(self.step_duration)
        if not self.autoplay:
            return

        self.pause_autoplay()
        self.start_autoplay()



    def autoplay_step(self):
        current = self.navigation_slider.value()
        maximum = self.navigation_slider.maximum()

        step_length = 1 if self.step_duration > 220 else 10 if self.step_duration > 120 else 100 if self.step_duration > 20 else 1000

        if current < maximum:
            self.navigation_slider.setValue(min(current + step_length, maximum))
        else:
            self.autoplay = False
            self.autoplay_timer.stop()
            self.log_status("Auto-play completed")

    def reset_view(self):
        self.navigation_slider.setValue(0)
        self.log_status("View reset to first layer")

    def toggle_show_all(self, checked):
        self.show_all_previous = checked
        self.update_graphics()

    def toggle_show_infill(self, checked):
        self.draw_infill = checked
        self.update_graphics()

    def on_layer_mode_changed(self):
        self.specify_height = self.thickness_radio.isChecked()

    def apply_all_settings(self):
        self.apply_generation_settings()
        self.apply_line_width()
        self.apply_wall_count()

    def apply_generation_settings(self):
        try:
            value = float(self.value_input.text())
            if value <= 0:
                raise ValueError("Value must be positive")

            self.generation_num = value
            self.log_status(f"Applied setting: {value}")
            if self.filename:
                self.regenerate()

        except ValueError as e:
            self.log_status(f"Invalid value: {e}")

    def apply_line_width(self):
        try:
            line_width = float(self.line_width_input.text())
            if line_width <= 0:
                raise ValueError("Line width must be positive")
            self.line_width = line_width
            self.log_status(f"Applied line width: {line_width} mm")
            if self.filename:
                self.regenerate()
        except ValueError as e:
            self.log_status(f"Invalid line width: {e}")

    def apply_wall_count(self):
        try:
            wall_count = int(self.wall_count_input.text())
            if wall_count < 0:
                raise ValueError("Wall count cannot be negative")
            self.wall_count = wall_count
            self.log_status(f"Applied wall count: {wall_count}")
            if self.filename:
                self.regenerate()
        except ValueError as e:
            self.log_status(f"Invalid wall count: {e}")


    def update_line_properties(self):
        self.update_graphics()

    def reset_camera(self):
        self.ax.view_init(elev=20, azim=45)
        self.canvas.draw()

    def fit_to_view(self):
        if self.slices and not self.draw_operation_lines:
            # For STL data, recompute bounds from data
            self.auto_bounds_checkbox.setChecked(True)
            self.toggle_auto_bounds(True)
            self.compute_axis_limits()
        else:
            # For G-code or when no data, just refresh current bounds
            self.apply_axis_limits()
        self.log_status("View fitted to data")

    def log_status(self, message):
        self.status_text.append(f"[{QTimer().remainingTime()}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())