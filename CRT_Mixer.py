import json
import os
import sys

from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from artifacting import apply_artifacting
from crt_filter import apply_crt_filter
from noise_overlay import apply_noise_overlay
from pixel_sorter_parallel import sort_all_pixels, sort_pixels_parallel
from rgb_distortion import (
    apply_channel_swap,
    apply_chromatic_aberration,
    apply_rgb_shift,
)


class FullResPreviewWindow(QMainWindow):
    """Separate window for full resolution preview with zoom and pan."""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Full Resolution Preview")
        self.setGeometry(100, 100, 1200, 900)

        # Store temp file path for cleanup
        self.temp_file_path = image_path

        # Central widget with scroll area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Scroll area for image
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        scroll.setWidget(self.image_label)
        layout.addWidget(scroll)

        # Zoom controls
        controls_layout = QHBoxLayout()

        zoom_out_btn = QPushButton("Zoom Out (50%)")
        zoom_out_btn.clicked.connect(lambda: self.set_zoom(0.5))
        controls_layout.addWidget(zoom_out_btn)

        zoom_fit_btn = QPushButton("Fit to Window")
        zoom_fit_btn.clicked.connect(lambda: self.set_zoom("fit"))
        controls_layout.addWidget(zoom_fit_btn)

        zoom_100_btn = QPushButton("100%")
        zoom_100_btn.clicked.connect(lambda: self.set_zoom(1.0))
        controls_layout.addWidget(zoom_100_btn)

        zoom_200_btn = QPushButton("Zoom In (200%)")
        zoom_200_btn.clicked.connect(lambda: self.set_zoom(2.0))
        controls_layout.addWidget(zoom_200_btn)

        controls_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        controls_layout.addWidget(close_btn)

        layout.addLayout(controls_layout)

        # Load image
        self.original_pixmap = QPixmap(image_path)
        self.scroll_area = scroll
        self.set_zoom("fit")

    def set_zoom(self, scale):
        """Set zoom level. scale can be a float or 'fit'."""
        if scale == "fit":
            # Fit to window
            available_size = self.scroll_area.size()
            scaled = self.original_pixmap.scaled(
                available_size.width() - 20,
                available_size.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            self.scroll_area.setWidgetResizable(True)
        else:
            # Scale by factor
            new_width = int(self.original_pixmap.width() * scale)
            new_height = int(self.original_pixmap.height() * scale)
            scaled = self.original_pixmap.scaled(
                new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            self.scroll_area.setWidgetResizable(False)
            self.image_label.adjustSize()

    def closeEvent(self, event):
        """Clean up temp file when window closes."""
        if (
            hasattr(self, "temp_file_path")
            and self.temp_file_path
            and os.path.exists(self.temp_file_path)
        ):
            try:
                os.unlink(self.temp_file_path)
            except (OSError, PermissionError) as e:
                print(f"Warning: Could not delete temp file {self.temp_file_path}: {e}")
        event.accept()


class PixelSorterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.input_path = None
        self.is_video = False
        self.recent_files = []
        self.recent_projects = []
        self.max_recent_files = 10
        self.max_recent_projects = 10
        self.load_recent_files()
        self.load_recent_projects()
        self.init_ui()
        self.live_preview_enabled = False
        self.preview_timer = None
        self.is_processing = False  # Flag to prevent concurrent processing

    def init_ui(self):
        self.setWindowTitle("CRT Mixer")
        self.setGeometry(100, 100, 1000, 800)

        # Create menu bar
        self.create_menu_bar()

        # Central widget with scroll area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout()
        central_widget.setLayout(outer_layout)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Scrollable content widget
        scroll_content = QWidget()
        main_layout = QVBoxLayout()
        scroll_content.setLayout(main_layout)
        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)

        # Header with title and logo
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)

        # Title on the left
        title = QLabel("CRT Mixer")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(title)

        # Spacer
        header_layout.addStretch()

        # Logo on the right
        logo_path = os.path.join(os.path.dirname(__file__), "logo.svg")
        if os.path.exists(logo_path):
            from PyQt5.QtSvg import QSvgWidget

            svg_widget = QSvgWidget(logo_path)
            svg_widget.setFixedSize(100, 40)  # Compact size matching title height
            header_layout.addWidget(svg_widget)

        main_layout.addLayout(header_layout)

        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout()

        self.select_btn = QPushButton("Select Input File")
        self.select_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px; font-size: 12px;"
        )
        self.select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_btn)

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("padding: 10px;")
        file_layout.addWidget(self.file_label)
        file_layout.addStretch()

        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # Parameters group
        params_group = QGroupBox("Sorting Parameters")
        params_layout = QVBoxLayout()

        # Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            ["brightness", "red", "green", "blue", "hue", "saturation"]
        )
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        params_layout.addLayout(mode_layout)

        # Direction
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Direction:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["horizontal", "vertical"])
        dir_layout.addWidget(self.direction_combo)
        dir_layout.addStretch()
        params_layout.addLayout(dir_layout)

        # Threshold
        thresh_layout = QHBoxLayout()
        thresh_layout.addWidget(QLabel("Threshold:"))
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(255)
        self.threshold_slider.setValue(80)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(25)
        thresh_layout.addWidget(self.threshold_slider)

        self.threshold_label = QLabel("80")
        self.threshold_label.setStyleSheet("font-weight: bold; min-width: 30px;")
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(str(v))
        )
        thresh_layout.addWidget(self.threshold_label)
        params_layout.addLayout(thresh_layout)

        # Checkboxes
        check_layout = QHBoxLayout()
        self.reverse_check = QCheckBox("Reverse sort")
        self.sort_all_check = QCheckBox("Sort ALL pixels")
        check_layout.addWidget(self.reverse_check)
        self.no_sort_check = QCheckBox("No Sort (effects only)")
        check_layout.addWidget(self.sort_all_check)
        check_layout.addWidget(self.no_sort_check)
        check_layout.addStretch()
        params_layout.addLayout(check_layout)

        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)

        # RGB Effects group
        rgb_group = QGroupBox("RGB Effects")
        rgb_layout = QVBoxLayout()

        # Channel Swap
        swap_layout = QHBoxLayout()
        swap_layout.addWidget(QLabel("Channel Swap:"))
        self.channel_swap_combo = QComboBox()
        self.channel_swap_combo.addItems(
            ["None", "RGB→RBG", "RGB→GRB", "RGB→GBR", "RGB→BRG", "RGB→BGR"]
        )
        swap_layout.addWidget(self.channel_swap_combo)
        swap_layout.addStretch()
        rgb_layout.addLayout(swap_layout)

        # RGB Shift
        shift_layout = QHBoxLayout()
        shift_layout.addWidget(QLabel("RGB Shift:"))
        shift_layout.addWidget(QLabel("R:"))
        self.red_shift = QSpinBox()
        self.red_shift.setRange(-50, 50)
        self.red_shift.setValue(0)
        shift_layout.addWidget(self.red_shift)

        shift_layout.addWidget(QLabel("G:"))
        self.green_shift = QSpinBox()
        self.green_shift.setRange(-50, 50)
        self.green_shift.setValue(0)
        shift_layout.addWidget(self.green_shift)

        shift_layout.addWidget(QLabel("B:"))
        self.blue_shift = QSpinBox()
        self.blue_shift.setRange(-50, 50)
        self.blue_shift.setValue(0)
        shift_layout.addWidget(self.blue_shift)
        shift_layout.addStretch()
        rgb_layout.addLayout(shift_layout)

        # Chromatic Aberration
        chroma_layout = QHBoxLayout()
        chroma_layout.addWidget(QLabel("Chromatic Aberration:"))
        self.chroma_slider = QSlider(Qt.Horizontal)
        self.chroma_slider.setMinimum(0)
        self.chroma_slider.setMaximum(20)
        self.chroma_slider.setValue(0)
        chroma_layout.addWidget(self.chroma_slider)

        self.chroma_label = QLabel("0")
        self.chroma_label.setStyleSheet("font-weight: bold; min-width: 30px;")
        self.chroma_slider.valueChanged.connect(
            lambda v: self.chroma_label.setText(str(v))
        )
        chroma_layout.addWidget(self.chroma_label)
        rgb_layout.addLayout(chroma_layout)

        rgb_group.setLayout(rgb_layout)
        main_layout.addWidget(rgb_group)

        # CRT Filter group
        crt_group = QGroupBox("CRT Filter")
        crt_layout_main = QVBoxLayout()

        # Enable checkbox
        self.crt_check = QCheckBox("Apply CRT filter")
        crt_layout_main.addWidget(self.crt_check)

        # Scanline intensity
        scanline_layout = QHBoxLayout()
        scanline_layout.addWidget(QLabel("Scanline Intensity:"))
        self.scanline_slider = QSlider(Qt.Horizontal)
        self.scanline_slider.setMinimum(0)
        self.scanline_slider.setMaximum(20)
        self.scanline_slider.setValue(8)
        scanline_layout.addWidget(self.scanline_slider)
        self.scanline_label = QLabel("8")
        self.scanline_label.setStyleSheet("font-weight: bold; min-width: 30px;")
        self.scanline_slider.valueChanged.connect(
            lambda v: self.scanline_label.setText(str(v))
        )
        scanline_layout.addWidget(self.scanline_label)
        crt_layout_main.addLayout(scanline_layout)

        # Curvature
        curve_layout = QHBoxLayout()
        curve_layout.addWidget(QLabel("Screen Curvature:"))
        self.curvature_slider = QSlider(Qt.Horizontal)
        self.curvature_slider.setMinimum(0)
        self.curvature_slider.setMaximum(50)
        self.curvature_slider.setValue(20)
        curve_layout.addWidget(self.curvature_slider)
        self.curvature_label = QLabel("0.02")
        self.curvature_label.setStyleSheet("font-weight: bold; min-width: 50px;")
        self.curvature_slider.valueChanged.connect(
            lambda v: self.curvature_label.setText(f"{v / 1000:.3f}")
        )
        curve_layout.addWidget(self.curvature_label)
        crt_layout_main.addLayout(curve_layout)

        # Brightness
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(QLabel("Brightness:"))
        self.crt_brightness_slider = QSlider(Qt.Horizontal)
        self.crt_brightness_slider.setMinimum(80)
        self.crt_brightness_slider.setMaximum(150)
        self.crt_brightness_slider.setValue(120)
        bright_layout.addWidget(self.crt_brightness_slider)
        self.crt_brightness_label = QLabel("1.2")
        self.crt_brightness_label.setStyleSheet("font-weight: bold; min-width: 50px;")
        self.crt_brightness_slider.valueChanged.connect(
            lambda v: self.crt_brightness_label.setText(f"{v / 100:.2f}")
        )
        bright_layout.addWidget(self.crt_brightness_label)
        crt_layout_main.addLayout(bright_layout)

        # Scanline Thickness
        thick_layout = QHBoxLayout()
        thick_layout.addWidget(QLabel("Scanline Thickness:"))
        self.scanline_thick_slider = QSlider(Qt.Horizontal)
        self.scanline_thick_slider.setMinimum(1)
        self.scanline_thick_slider.setMaximum(5)
        self.scanline_thick_slider.setValue(1)
        thick_layout.addWidget(self.scanline_thick_slider)
        self.scanline_thick_label = QLabel("1")
        self.scanline_thick_label.setStyleSheet("font-weight: bold; min-width: 30px;")
        self.scanline_thick_slider.valueChanged.connect(
            lambda v: self.scanline_thick_label.setText(str(v))
        )
        thick_layout.addWidget(self.scanline_thick_label)
        crt_layout_main.addLayout(thick_layout)

        # Scanline Count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Scanline Count:"))
        self.scanline_count_slider = QSlider(Qt.Horizontal)
        self.scanline_count_slider.setMinimum(0)
        self.scanline_count_slider.setMaximum(1080)
        self.scanline_count_slider.setValue(600)
        count_layout.addWidget(self.scanline_count_slider)
        self.scanline_count_label = QLabel("600")
        self.scanline_count_label.setStyleSheet("font-weight: bold; min-width: 50px;")
        self.scanline_count_slider.valueChanged.connect(
            lambda v: self.scanline_count_label.setText(str(v))
        )
        count_layout.addWidget(self.scanline_count_label)
        crt_layout_main.addLayout(count_layout)

        # Phosphor Glow
        glow_layout = QHBoxLayout()
        glow_layout.addWidget(QLabel("Phosphor Glow:"))
        self.phosphor_glow_slider = QSlider(Qt.Horizontal)
        self.phosphor_glow_slider.setMinimum(0)
        self.phosphor_glow_slider.setMaximum(100)
        self.phosphor_glow_slider.setValue(0)
        glow_layout.addWidget(self.phosphor_glow_slider)
        self.phosphor_glow_label = QLabel("0.0")
        self.phosphor_glow_label.setStyleSheet("font-weight: bold; min-width: 50px;")
        self.phosphor_glow_slider.valueChanged.connect(
            lambda v: self.phosphor_glow_label.setText(f"{v / 100:.2f}")
        )
        glow_layout.addWidget(self.phosphor_glow_label)
        crt_layout_main.addLayout(glow_layout)
        crt_group.setLayout(crt_layout_main)
        main_layout.addWidget(crt_group)

        # Noise Overlay group
        noise_group = QGroupBox("Noise Overlay")
        noise_layout_main = QVBoxLayout()

        # Enable checkbox
        self.noise_check = QCheckBox("Apply noise overlay")
        noise_layout_main.addWidget(self.noise_check)

        # Noise type
        noise_type_layout = QHBoxLayout()
        noise_type_layout.addWidget(QLabel("Noise Type:"))
        self.noise_type_combo = QComboBox()
        self.noise_type_combo.addItems(["Gaussian", "Film Grain", "Salt & Pepper"])
        noise_type_layout.addWidget(self.noise_type_combo)
        noise_type_layout.addStretch()
        noise_layout_main.addLayout(noise_type_layout)

        # Noise intensity
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("Intensity:"))
        self.noise_intensity_slider = QSlider(Qt.Horizontal)
        self.noise_intensity_slider.setMinimum(0)
        self.noise_intensity_slider.setMaximum(100)
        self.noise_intensity_slider.setValue(10)
        intensity_layout.addWidget(self.noise_intensity_slider)
        self.noise_intensity_label = QLabel("0.10")
        self.noise_intensity_label.setStyleSheet("font-weight: bold; min-width: 50px;")
        self.noise_intensity_slider.valueChanged.connect(
            lambda v: self.noise_intensity_label.setText(f"{v / 100:.2f}")
        )
        intensity_layout.addWidget(self.noise_intensity_label)
        noise_layout_main.addLayout(intensity_layout)

        noise_group.setLayout(noise_layout_main)
        main_layout.addWidget(noise_group)

        # Artifacting group
        artifact_group = QGroupBox("Artifacting")
        artifact_layout_main = QVBoxLayout()

        # Enable checkbox
        self.artifact_check = QCheckBox("Apply artifacting")
        artifact_layout_main.addWidget(self.artifact_check)

        # Artifact type
        artifact_type_layout = QHBoxLayout()
        artifact_type_layout.addWidget(QLabel("Artifact Type:"))
        self.artifact_type_combo = QComboBox()
        self.artifact_type_combo.addItems(
            ["JPEG Compression", "VHS Tracking", "Digital Glitch", "Color Bleed"]
        )
        artifact_type_layout.addWidget(self.artifact_type_combo)
        artifact_type_layout.addStretch()
        artifact_layout_main.addLayout(artifact_type_layout)

        # Artifact intensity
        artifact_intensity_layout = QHBoxLayout()
        artifact_intensity_layout.addWidget(QLabel("Intensity:"))
        self.artifact_intensity_slider = QSlider(Qt.Horizontal)
        self.artifact_intensity_slider.setMinimum(0)
        self.artifact_intensity_slider.setMaximum(100)
        self.artifact_intensity_slider.setValue(50)
        artifact_intensity_layout.addWidget(self.artifact_intensity_slider)
        self.artifact_intensity_label = QLabel("0.50")
        self.artifact_intensity_label.setStyleSheet(
            "font-weight: bold; min-width: 50px;"
        )
        self.artifact_intensity_slider.valueChanged.connect(
            lambda v: self.artifact_intensity_label.setText(f"{v / 100:.2f}")
        )
        artifact_intensity_layout.addWidget(self.artifact_intensity_label)
        artifact_layout_main.addLayout(artifact_intensity_layout)

        artifact_group.setLayout(artifact_layout_main)
        main_layout.addWidget(artifact_group)

        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel("Select an image to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(600, 400)
        self.preview_label.setStyleSheet(
            "background-color: #f0f0f0; border: 1px solid #ccc;"
        )
        preview_layout.addWidget(self.preview_label)

        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # Action buttons
        button_layout = QHBoxLayout()

        # Live preview checkbox
        self.live_preview_check = QCheckBox("Live Preview (auto-update)")
        self.live_preview_check.setStyleSheet("font-weight: bold; color: #9C27B0;")
        self.live_preview_check.stateChanged.connect(self.toggle_live_preview)
        button_layout.addWidget(self.live_preview_check)
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 12px; font-size: 13px; font-weight: bold;"
        )
        self.preview_btn.clicked.connect(self.preview_sort)
        button_layout.addWidget(self.preview_btn)

        self.save_btn = QPushButton("Save As...")
        self.save_btn.setStyleSheet(
            "background-color: #FF9800; color: white; padding: 12px; font-size: 13px; font-weight: bold;"
        )
        self.save_btn.clicked.connect(self.save_sorted)
        button_layout.addWidget(self.save_btn)

        self.fullres_preview_btn = QPushButton("Full Res Preview")
        self.fullres_preview_btn.setStyleSheet(
            "background-color: #9C27B0; color: white; padding: 12px; font-size: 13px; font-weight: bold;"
        )
        self.fullres_preview_btn.clicked.connect(self.fullres_preview)
        button_layout.addWidget(self.fullres_preview_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Add some spacing at bottom
        main_layout.addStretch()

        # Status bar (outside scroll area)
        self.status_label = QLabel("Ready - Select a file to begin")
        self.status_label.setStyleSheet("background-color: #e0e0e0; padding: 8px;")
        outer_layout.addWidget(self.status_label)

    def create_menu_bar(self):
        """Create the menu bar with File menu."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.select_file)
        file_menu.addAction(open_action)

        # Open Recent submenu
        self.recent_menu = QMenu("Open &Recent", self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()

        file_menu.addSeparator()

        # Save Project action
        save_project_action = QAction("&Save Project...", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)

        # Load Project action
        load_project_action = QAction("&Load Project...", self)
        load_project_action.setShortcut("Ctrl+L")
        load_project_action.triggered.connect(self.load_project)
        file_menu.addAction(load_project_action)

        # Load Recent Project submenu
        self.recent_projects_menu = QMenu("Load Recent &Project", self)
        file_menu.addMenu(self.recent_projects_menu)
        self.update_recent_projects_menu()

        file_menu.addSeparator()

        # Quit action
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    def load_recent_files(self):
        """Load recent files list from a config file."""
        config_path = os.path.expanduser("~/.crt_mixer_recent")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.recent_files = [
                        line.strip() for line in f.readlines() if line.strip()
                    ]
                # Filter out files that no longer exist
                self.recent_files = [f for f in self.recent_files if os.path.exists(f)]
            except Exception as e:
                print(f"Error loading recent files: {e}")
                self.recent_files = []

    def save_recent_files(self):
        """Save recent files list to a config file."""
        config_path = os.path.expanduser("~/.crt_mixer_recent")
        try:
            with open(config_path, "w") as f:
                for file_path in self.recent_files[: self.max_recent_files]:
                    f.write(file_path + "\n")
        except Exception as e:
            print(f"Error saving recent files: {e}")

    def add_recent_file(self, file_path):
        """Add a file to the recent files list."""
        # Remove if already in list
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)

        # Add to beginning of list
        self.recent_files.insert(0, file_path)

        # Keep only max_recent_files
        self.recent_files = self.recent_files[: self.max_recent_files]

        # Save and update menu
        self.save_recent_files()
        self.update_recent_menu()

    def update_recent_menu(self):
        """Update the Open Recent menu with current recent files."""
        self.recent_menu.clear()

        if not self.recent_files:
            no_recent_action = QAction("No Recent Files", self)
            no_recent_action.setEnabled(False)
            self.recent_menu.addAction(no_recent_action)
        else:
            for file_path in self.recent_files:
                action = QAction(os.path.basename(file_path), self)
                action.setToolTip(file_path)
                action.triggered.connect(
                    lambda checked, path=file_path: self.open_recent_file(path)
                )
                self.recent_menu.addAction(action)

            self.recent_menu.addSeparator()

            clear_action = QAction("Clear Recent Files", self)
            clear_action.triggered.connect(self.clear_recent_files)
            self.recent_menu.addAction(clear_action)

    def open_recent_file(self, file_path):
        """Open a file from the recent files list."""
        if os.path.exists(file_path):
            self.load_file(file_path)
        else:
            QMessageBox.warning(
                self, "File Not Found", f"The file no longer exists:\n{file_path}"
            )
            # Remove from recent files
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
                self.save_recent_files()
                self.update_recent_menu()

    def clear_recent_files(self):
        """Clear the recent files list."""
        self.recent_files = []
        self.save_recent_files()
        self.update_recent_menu()

    def load_recent_projects(self):
        """Load recent projects list from a config file."""
        config_path = os.path.expanduser("~/.crt_mixer_recent_projects")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.recent_projects = [
                        line.strip() for line in f.readlines() if line.strip()
                    ]
                # Filter out projects that no longer exist
                self.recent_projects = [
                    f for f in self.recent_projects if os.path.exists(f)
                ]
            except Exception as e:
                print(f"Error loading recent projects: {e}")
                self.recent_projects = []

    def save_recent_projects(self):
        """Save recent projects list to a config file."""
        config_path = os.path.expanduser("~/.crt_mixer_recent_projects")
        try:
            with open(config_path, "w") as f:
                for project_path in self.recent_projects[: self.max_recent_projects]:
                    f.write(project_path + "\n")
        except Exception as e:
            print(f"Error saving recent projects: {e}")

    def add_recent_project(self, project_path):
        """Add a project to the recent projects list."""
        # Remove if already in list
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)

        # Add to beginning of list
        self.recent_projects.insert(0, project_path)

        # Keep only max_recent_projects
        self.recent_projects = self.recent_projects[: self.max_recent_projects]

        # Save and update menu
        self.save_recent_projects()
        self.update_recent_projects_menu()

    def update_recent_projects_menu(self):
        """Update the Load Recent Project menu with current recent projects."""
        self.recent_projects_menu.clear()

        if not self.recent_projects:
            no_recent_action = QAction("No Recent Projects", self)
            no_recent_action.setEnabled(False)
            self.recent_projects_menu.addAction(no_recent_action)
        else:
            for project_path in self.recent_projects:
                action = QAction(os.path.basename(project_path), self)
                action.setToolTip(project_path)
                action.triggered.connect(
                    lambda checked, path=project_path: self.open_recent_project(path)
                )
                self.recent_projects_menu.addAction(action)

            self.recent_projects_menu.addSeparator()

            clear_action = QAction("Clear Recent Projects", self)
            clear_action.triggered.connect(self.clear_recent_projects)
            self.recent_projects_menu.addAction(clear_action)

    def open_recent_project(self, project_path):
        """Open a project from the recent projects list."""
        if os.path.exists(project_path):
            self.load_project_from_path(project_path)
        else:
            QMessageBox.warning(
                self,
                "Project Not Found",
                f"The project file no longer exists:\n{project_path}",
            )
            # Remove from recent projects
            if project_path in self.recent_projects:
                self.recent_projects.remove(project_path)
                self.save_recent_projects()
                self.update_recent_projects_menu()

    def clear_recent_projects(self):
        """Clear the recent projects list."""
        self.recent_projects = []
        self.save_recent_projects()
        self.update_recent_projects_menu()

    def save_project(self):
        """Save current project settings to a JSON file."""
        if not self.input_path:
            QMessageBox.warning(
                self, "No Image", "Please load an image first before saving a project."
            )
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "CRT Mixer Project (*.crtmix);;All Files (*.*)"
        )

        if filename:
            try:
                project_data = {
                    "version": "1.0",
                    "input_file": self.input_path,
                    "sorting": {
                        "mode": self.mode_combo.currentText(),
                        "direction": self.direction_combo.currentText(),
                        "threshold": self.threshold_slider.value(),
                        "reverse": self.reverse_check.isChecked(),
                        "sort_all": self.sort_all_check.isChecked(),
                        "no_sort": self.no_sort_check.isChecked(),
                    },
                    "rgb": {
                        "channel_swap": self.channel_swap_combo.currentText(),
                        "red_shift": self.red_shift.value(),
                        "green_shift": self.green_shift.value(),
                        "blue_shift": self.blue_shift.value(),
                        "chromatic_aberration": self.chroma_slider.value(),
                    },
                    "crt": {
                        "enabled": self.crt_check.isChecked(),
                        "scanline_intensity": self.scanline_slider.value(),
                        "scanline_thickness": self.scanline_thick_slider.value(),
                        "scanline_count": self.scanline_count_slider.value(),
                        "curvature": self.curvature_slider.value(),
                        "brightness": self.crt_brightness_slider.value(),
                        "phosphor_glow": self.phosphor_glow_slider.value(),
                    },
                    "noise": {
                        "enabled": self.noise_check.isChecked(),
                        "type": self.noise_type_combo.currentText(),
                        "intensity": self.noise_intensity_slider.value(),
                    },
                    "artifacting": {
                        "enabled": self.artifact_check.isChecked(),
                        "type": self.artifact_type_combo.currentText(),
                        "intensity": self.artifact_intensity_slider.value(),
                    },
                }

                with open(filename, "w") as f:
                    json.dump(project_data, f, indent=2)

                # Add to recent projects
                self.add_recent_project(filename)

                self.status_label.setText(
                    f"✓ Project saved: {os.path.basename(filename)}"
                )
                QMessageBox.information(
                    self, "Success", f"Project saved to:\n{filename}"
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project: {e}")

    def load_project(self):
        """Load project settings from a JSON file (with file dialog)."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "CRT Mixer Project (*.crtmix);;All Files (*.*)"
        )

        if filename:
            self.load_project_from_path(filename)

    def load_project_from_path(self, filename):
        """Load project settings from a specific file path."""
        try:
            with open(filename, "r") as f:
                project_data = json.load(f)

            # Load input file
            if "input_file" in project_data:
                input_file = project_data["input_file"]
                if os.path.exists(input_file):
                    self.load_file(input_file)
                else:
                    QMessageBox.warning(
                        self,
                        "Input File Not Found",
                        f"The original input file was not found:\n{input_file}\n\nYou can load a different image manually.",
                    )

            # Load sorting settings
            if "sorting" in project_data:
                s = project_data["sorting"]
                self.mode_combo.setCurrentText(s.get("mode", "brightness"))
                self.direction_combo.setCurrentText(s.get("direction", "horizontal"))
                self.threshold_slider.setValue(s.get("threshold", 80))
                self.reverse_check.setChecked(s.get("reverse", False))
                self.sort_all_check.setChecked(s.get("sort_all", False))
                self.no_sort_check.setChecked(s.get("no_sort", False))

            # Load RGB settings
            if "rgb" in project_data:
                r = project_data["rgb"]
                self.channel_swap_combo.setCurrentText(r.get("channel_swap", "None"))
                self.red_shift.setValue(r.get("red_shift", 0))
                self.green_shift.setValue(r.get("green_shift", 0))
                self.blue_shift.setValue(r.get("blue_shift", 0))
                self.chroma_slider.setValue(r.get("chromatic_aberration", 0))

            # Load CRT settings
            if "crt" in project_data:
                c = project_data["crt"]
                self.crt_check.setChecked(c.get("enabled", False))
                self.scanline_slider.setValue(c.get("scanline_intensity", 8))
                self.scanline_thick_slider.setValue(c.get("scanline_thickness", 1))
                self.scanline_count_slider.setValue(c.get("scanline_count", 600))
                self.curvature_slider.setValue(c.get("curvature", 20))
                self.crt_brightness_slider.setValue(c.get("brightness", 120))
                self.phosphor_glow_slider.setValue(c.get("phosphor_glow", 0))

            # Load noise settings
            if "noise" in project_data:
                n = project_data["noise"]
                self.noise_check.setChecked(n.get("enabled", False))
                self.noise_type_combo.setCurrentText(n.get("type", "Gaussian"))
                self.noise_intensity_slider.setValue(n.get("intensity", 10))

            # Load artifacting settings
            if "artifacting" in project_data:
                a = project_data["artifacting"]
                self.artifact_check.setChecked(a.get("enabled", False))
                self.artifact_type_combo.setCurrentText(
                    a.get("type", "JPEG Compression")
                )
                self.artifact_intensity_slider.setValue(a.get("intensity", 50))

            # Add to recent projects
            self.add_recent_project(filename)

            self.status_label.setText(f"✓ Project loaded: {os.path.basename(filename)}")
            QMessageBox.information(
                self, "Success", f"Project loaded from:\n{filename}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project: {e}")

    def load_file(self, filename):
        """Load a file (extracted from select_file logic)."""
        # Validate file exists and is readable
        if not os.path.exists(filename):
            QMessageBox.critical(self, "Error", "Selected file does not exist")
            return

        if not os.access(filename, os.R_OK):
            QMessageBox.critical(self, "Error", "Cannot read selected file")
            return

        # Validate it's a valid image
        try:
            img = Image.open(filename)
            img.verify()  # Verify it's a valid image
            img.close()

            # Reopen to get actual image (verify() closes the file)
            img = Image.open(filename)
            width, height = img.size
            img.close()

            # Check image size limits (max 8K resolution)
            max_dimension = 8192
            if width > max_dimension or height > max_dimension:
                QMessageBox.warning(
                    self,
                    "Large Image Warning",
                    f"Image is very large ({width}x{height}). Processing may be slow.\n\n"
                    f"Recommended maximum: {max_dimension}x{max_dimension} pixels",
                )

            self.input_path = filename
            self.file_label.setText(os.path.basename(filename))
            self.load_image_preview(filename)
            self.status_label.setText(
                f"Image loaded: {os.path.basename(filename)} ({width}x{height})"
            )

            # Add to recent files
            self.add_recent_file(filename)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid image file: {e}")
            return

    def select_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input File",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp);;All Files (*.*)",
        )

        if filename:
            self.load_file(filename)

    def load_image_preview(self, path):
        try:
            pixmap = QPixmap(path)
            scaled_pixmap = pixmap.scaled(
                600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")

    def apply_effects(self, input_path, output_path, is_preview=False):
        """Apply all selected effects in order."""
        import tempfile

        current_path = input_path
        temp_files = []

        try:
            print(f"[DEBUG] Starting apply_effects with input: {input_path}")
            # Step 1: Noise Overlay (applied first)
            if self.noise_check.isChecked():
                temp0 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp0.close()
                temp_files.append(temp0.name)

                noise_type_map = {
                    "Gaussian": "gaussian",
                    "Film Grain": "film_grain",
                    "Salt & Pepper": "salt_pepper",
                }
                noise_type = noise_type_map.get(
                    self.noise_type_combo.currentText(), "gaussian"
                )

                apply_noise_overlay(
                    current_path,
                    temp0.name,
                    intensity=self.noise_intensity_slider.value() / 100,
                    noise_type=noise_type,
                )
                current_path = temp0.name

            # Step 2: Artifacting
            if self.artifact_check.isChecked():
                temp_art = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp_art.close()
                temp_files.append(temp_art.name)

                artifact_type_map = {
                    "JPEG Compression": "jpeg",
                    "VHS Tracking": "vhs",
                    "Digital Glitch": "digital_glitch",
                    "Color Bleed": "color_bleed",
                }
                artifact_type = artifact_type_map.get(
                    self.artifact_type_combo.currentText(), "jpeg"
                )

                apply_artifacting(
                    current_path,
                    temp_art.name,
                    intensity=self.artifact_intensity_slider.value() / 100,
                    artifact_type=artifact_type,
                )
                current_path = temp_art.name

            # Step 3: Channel swap
            swap_mode = self.channel_swap_combo.currentText()
            if swap_mode != "None":
                temp1 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp1.close()
                temp_files.append(temp1.name)

                swap_map = {
                    "RGB→RBG": "rbg",
                    "RGB→GRB": "grb",
                    "RGB→GBR": "gbr",
                    "RGB→BRG": "brg",
                    "RGB→BGR": "bgr",
                }
                apply_channel_swap(current_path, temp1.name, swap_map[swap_mode])
                current_path = temp1.name

            # Step 4: RGB Shift
            if (
                self.red_shift.value() != 0
                or self.green_shift.value() != 0
                or self.blue_shift.value() != 0
            ):
                temp2 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp2.close()
                temp_files.append(temp2.name)

                apply_rgb_shift(
                    current_path,
                    temp2.name,
                    red_x=self.red_shift.value(),
                    green_x=self.green_shift.value(),
                    blue_x=self.blue_shift.value(),
                )
                current_path = temp2.name

            # Step 5: Chromatic Aberration
            if self.chroma_slider.value() > 0:
                temp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp3.close()
                temp_files.append(temp3.name)

                apply_chromatic_aberration(
                    current_path, temp3.name, self.chroma_slider.value()
                )
                current_path = temp3.name

            # Step 6: Pixel sorting
            # Skip sorting if "No Sort" is checked
            if not self.no_sort_check.isChecked():
                temp4 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp4.close()
                temp_files.append(temp4.name)

                if self.sort_all_check.isChecked():
                    sort_all_pixels(
                        current_path,
                        temp4.name,
                        self.mode_combo.currentText(),
                        self.reverse_check.isChecked(),
                    )
                else:
                    sort_pixels_parallel(
                        current_path,
                        temp4.name,
                        self.mode_combo.currentText(),
                        self.direction_combo.currentText(),
                        self.threshold_slider.value(),
                        self.reverse_check.isChecked(),
                        preview_mode=is_preview,
                    )
                current_path = temp4.name

            # Step 7: CRT Filter
            if self.crt_check.isChecked():
                temp5 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp5.close()
                temp_files.append(temp5.name)

                apply_crt_filter(
                    current_path,
                    temp5.name,
                    hard_scan=-self.scanline_slider.value(),
                    display_warp_x=self.curvature_slider.value() / 1000,
                    display_warp_y=self.curvature_slider.value() / 1000,
                    brightness=self.crt_brightness_slider.value() / 100,
                    scanline_intensity=self.scanline_slider.value() / 100,
                    scanline_thickness=self.scanline_thick_slider.value(),
                    scanline_count=self.scanline_count_slider.value(),
                    phosphor_glow=self.phosphor_glow_slider.value() / 100,
                )
                current_path = temp5.name

            # Copy final result to output
            import shutil

            shutil.copy(current_path, output_path)

        finally:
            # Clean up temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except (OSError, PermissionError) as e:
                        print(f"Warning: Could not delete temp file {temp_file}: {e}")

            # Force garbage collection to free memory
            import gc

            gc.collect()

    def toggle_live_preview(self, state):
        """Enable or disable live preview mode."""
        from PyQt5.QtCore import QTimer

        self.live_preview_enabled = state == Qt.Checked

        if self.live_preview_enabled:
            if not self.input_path:
                QMessageBox.warning(
                    self, "No File", "Please select an input file first"
                )
                self.live_preview_check.setChecked(False)
                return

            # Warn about performance with many effects
            effects_count = sum(
                [
                    self.noise_check.isChecked(),
                    self.artifact_check.isChecked(),
                    self.crt_check.isChecked(),
                    not self.no_sort_check.isChecked(),
                    self.channel_swap_combo.currentText() != "None",
                    any(
                        [
                            self.red_shift.value(),
                            self.green_shift.value(),
                            self.blue_shift.value(),
                        ]
                    ),
                    self.chroma_slider.value() > 0,
                ]
            )

            if effects_count >= 3:
                QMessageBox.information(
                    self,
                    "Live Preview",
                    "You have multiple effects enabled. Live preview may be slow.\n\n"
                    "Tip: Disable some effects or use the Preview button instead for better performance.",
                )

            # Create timer for debounced updates
            if self.preview_timer is None:
                self.preview_timer = QTimer()
                self.preview_timer.timeout.connect(self.auto_preview)

            # Connect all controls to trigger preview update
            self.connect_live_preview_signals()

            # Do initial preview
            self.schedule_preview_update()
            self.status_label.setText("Live preview enabled")
        else:
            # Disconnect signals
            if self.preview_timer:
                self.preview_timer.stop()
            self.disconnect_live_preview_signals()
            self.status_label.setText("Live preview disabled")

    def connect_live_preview_signals(self):
        """Connect all control signals to trigger preview updates."""
        # Sorting controls
        self.mode_combo.currentIndexChanged.connect(self.schedule_preview_update)
        self.direction_combo.currentIndexChanged.connect(self.schedule_preview_update)
        self.threshold_slider.valueChanged.connect(self.schedule_preview_update)
        self.reverse_check.stateChanged.connect(self.schedule_preview_update)
        self.sort_all_check.stateChanged.connect(self.schedule_preview_update)
        self.no_sort_check.stateChanged.connect(self.schedule_preview_update)

        # RGB controls
        self.channel_swap_combo.currentIndexChanged.connect(
            self.schedule_preview_update
        )
        self.red_shift.valueChanged.connect(self.schedule_preview_update)
        self.green_shift.valueChanged.connect(self.schedule_preview_update)
        self.blue_shift.valueChanged.connect(self.schedule_preview_update)
        self.chroma_slider.valueChanged.connect(self.schedule_preview_update)

        # CRT controls
        self.crt_check.stateChanged.connect(self.schedule_preview_update)
        self.scanline_slider.valueChanged.connect(self.schedule_preview_update)
        self.scanline_thick_slider.valueChanged.connect(self.schedule_preview_update)
        self.scanline_count_slider.valueChanged.connect(self.schedule_preview_update)
        self.curvature_slider.valueChanged.connect(self.schedule_preview_update)
        self.crt_brightness_slider.valueChanged.connect(self.schedule_preview_update)
        self.phosphor_glow_slider.valueChanged.connect(self.schedule_preview_update)

        # Noise controls
        self.noise_check.stateChanged.connect(self.schedule_preview_update)
        self.noise_type_combo.currentIndexChanged.connect(self.schedule_preview_update)
        self.noise_intensity_slider.valueChanged.connect(self.schedule_preview_update)

        # Artifacting controls
        self.artifact_check.stateChanged.connect(self.schedule_preview_update)
        self.artifact_type_combo.currentIndexChanged.connect(
            self.schedule_preview_update
        )
        self.artifact_intensity_slider.valueChanged.connect(
            self.schedule_preview_update
        )

    def disconnect_live_preview_signals(self):
        """Disconnect all control signals."""
        signals = [
            # Sorting controls
            (self.mode_combo.currentIndexChanged, self.schedule_preview_update),
            (self.direction_combo.currentIndexChanged, self.schedule_preview_update),
            (self.threshold_slider.valueChanged, self.schedule_preview_update),
            (self.reverse_check.stateChanged, self.schedule_preview_update),
            (self.sort_all_check.stateChanged, self.schedule_preview_update),
            (self.no_sort_check.stateChanged, self.schedule_preview_update),
            # RGB controls
            (self.channel_swap_combo.currentIndexChanged, self.schedule_preview_update),
            (self.red_shift.valueChanged, self.schedule_preview_update),
            (self.green_shift.valueChanged, self.schedule_preview_update),
            (self.blue_shift.valueChanged, self.schedule_preview_update),
            (self.chroma_slider.valueChanged, self.schedule_preview_update),
            # CRT controls
            (self.crt_check.stateChanged, self.schedule_preview_update),
            (self.scanline_slider.valueChanged, self.schedule_preview_update),
            (self.scanline_thick_slider.valueChanged, self.schedule_preview_update),
            (self.scanline_count_slider.valueChanged, self.schedule_preview_update),
            (self.curvature_slider.valueChanged, self.schedule_preview_update),
            (self.crt_brightness_slider.valueChanged, self.schedule_preview_update),
            (self.phosphor_glow_slider.valueChanged, self.schedule_preview_update),
            # Noise controls
            (self.noise_check.stateChanged, self.schedule_preview_update),
            (self.noise_type_combo.currentIndexChanged, self.schedule_preview_update),
            (self.noise_intensity_slider.valueChanged, self.schedule_preview_update),
            # Artifacting controls
            (self.artifact_check.stateChanged, self.schedule_preview_update),
            (
                self.artifact_type_combo.currentIndexChanged,
                self.schedule_preview_update,
            ),
            (self.artifact_intensity_slider.valueChanged, self.schedule_preview_update),
        ]

        # Disconnect each signal individually
        for signal, slot in signals:
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                # Signal not connected or already disconnected
                pass

    def schedule_preview_update(self):
        """Schedule a preview update after a short delay (debouncing)."""
        if self.live_preview_enabled and self.preview_timer:
            # Restart timer - waits 1000ms after last change (increased for stability)
            self.preview_timer.stop()
            self.preview_timer.start(1000)  # 1000ms delay

    def auto_preview(self):
        """Automatically update preview (called by timer)."""
        if self.preview_timer:
            self.preview_timer.stop()

        # Only start preview if not already processing
        if not self.is_processing:
            self.preview_sort()

    def preview_sort(self):
        if not self.input_path:
            QMessageBox.warning(self, "No File", "Please select an input file first")
            return

        # Prevent concurrent processing
        if self.is_processing:
            self.status_label.setText("Processing in progress, please wait...")
            return

        self.is_processing = True
        self.status_label.setText("Processing preview...")
        QApplication.processEvents()

        try:
            import tempfile
            import traceback

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_path = temp_file.name
            temp_file.close()

            print(f"[DEBUG] Preview: temp file = {temp_path}")
            self.apply_effects(self.input_path, temp_path, is_preview=True)

            # Load preview
            self.load_image_preview(temp_path)
            os.unlink(temp_path)
            self.status_label.setText("Preview complete")

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"[ERROR] Preview failed: {error_details}")
            QMessageBox.critical(
                self, "Error", f"Processing failed: {e}\n\nCheck console for details."
            )
            self.status_label.setText("Error occurred")
        finally:
            self.is_processing = False

    def fullres_preview(self):
        """Open full resolution preview in separate window."""
        if not self.input_path:
            QMessageBox.warning(self, "No File", "Please select an input file first")
            return

        # Prevent concurrent processing
        if self.is_processing:
            QMessageBox.warning(self, "Busy", "Processing in progress, please wait...")
            return

        self.is_processing = True
        self.status_label.setText("Processing full resolution preview...")
        QApplication.processEvents()

        try:
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_path = temp_file.name
            temp_file.close()

            self.apply_effects(self.input_path, temp_path, is_preview=False)

            # Open in separate preview window
            self.preview_window = FullResPreviewWindow(temp_path, self)
            self.preview_window.show()

            self.status_label.setText("✓ Full resolution preview opened in new window")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed: {e}")
            self.status_label.setText("Error occurred")
        finally:
            self.is_processing = False

    def save_sorted(self):
        if not self.input_path:
            QMessageBox.warning(self, "No File", "Please select an input file first")
            return

        # Prevent concurrent processing
        if self.is_processing:
            QMessageBox.warning(self, "Busy", "Processing in progress, please wait...")
            return

        # Suggest output filename
        base, ext = os.path.splitext(self.input_path)
        suffix = "_mixed"
        default_name = base + suffix + ext

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Mixed File",
            default_name,
            "JPEG (*.jpg);;PNG (*.png);;All Files (*.*)",
        )

        if output_path:
            self.is_processing = True
            self.status_label.setText("Processing...")
            QApplication.processEvents()

            try:
                self.apply_effects(self.input_path, output_path, is_preview=False)

                self.status_label.setText(f"✓ Saved to {os.path.basename(output_path)}")
                QMessageBox.information(
                    self, "Success", f"File saved to:\n{output_path}"
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Processing failed: {e}")
                self.status_label.setText("Error occurred")
            finally:
                self.is_processing = False


def main():
    app = QApplication(sys.argv)
    window = PixelSorterApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
