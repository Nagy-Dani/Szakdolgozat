"""Main application window with sidebar navigation and stacked pages."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QMenuBar, QStatusBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon

from config import APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, SIDEBAR_WIDTH
from views.rider_input_view import RiderInputView
from views.bike_input_view import BikeInputView
from views.video_capture_view import VideoCaptureView
from views.analysis_view import AnalysisView
from views.results_view import ResultsView


class MainWindow(QMainWindow):
    """Top-level window with sidebar navigation and stacked content pages."""

    # Navigation signals
    page_changed = pyqtSignal(int)
    new_session_requested = pyqtSignal()
    save_session_requested = pyqtSignal()
    load_session_requested = pyqtSignal()
    export_pdf_requested = pyqtSignal()

    PAGES = ["👤  Rider", "🚲  Bike", "🎥  Video", "📐  Analysis", "📊  Results"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # --- Create child views ---
        self.rider_view = RiderInputView()
        self.bike_view = BikeInputView()
        self.video_view = VideoCaptureView()
        self.analysis_view = AnalysisView()
        self.results_view = ResultsView()

        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()

    # ------------------------------------------------------------------ UI

    def _setup_menu(self) -> None:
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")

        act_new = QAction("&New Session", self)
        act_new.setShortcut("Ctrl+N")
        act_new.triggered.connect(self.new_session_requested.emit)
        file_menu.addAction(act_new)

        act_open = QAction("&Open Session…", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.load_session_requested.emit)
        file_menu.addAction(act_open)

        act_save = QAction("&Save Session", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.save_session_requested.emit)
        file_menu.addAction(act_save)

        file_menu.addSeparator()

        act_export = QAction("&Export PDF…", self)
        act_export.triggered.connect(self.export_pdf_requested.emit)
        file_menu.addAction(act_export)

        help_menu = menu.addMenu("&Help")
        act_about = QAction("&About", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QWidget()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("""
            #sidebar {
                background-color: #1e1e2e;
                border-right: 1px solid #333;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 16, 0, 16)

        title = QLabel(APP_NAME)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #7aa2f7; padding: 12px;")
        sidebar_layout.addWidget(title)

        self._nav_list = QListWidget()
        self._nav_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                font-size: 14px;
                color: #cdd6f4;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-radius: 6px;
                margin: 2px 8px;
            }
            QListWidget::item:selected {
                background-color: #313244;
                color: #7aa2f7;
            }
            QListWidget::item:hover {
                background-color: #2a2a3c;
            }
        """)
        for page_name in self.PAGES:
            self._nav_list.addItem(QListWidgetItem(page_name))
        self._nav_list.currentRowChanged.connect(self._on_page_selected)
        sidebar_layout.addWidget(self._nav_list)
        sidebar_layout.addStretch()

        main_layout.addWidget(sidebar)

        # --- Content stack ---
        self._stack = QStackedWidget()
        self._stack.addWidget(self.rider_view)
        self._stack.addWidget(self.bike_view)
        self._stack.addWidget(self.video_view)
        self._stack.addWidget(self.analysis_view)
        self._stack.addWidget(self.results_view)
        main_layout.addWidget(self._stack, stretch=1)

        # Default selection
        self._nav_list.setCurrentRow(0)

    def _setup_statusbar(self) -> None:
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    # ------------------------------------------------------------------ Slots

    def _on_page_selected(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self.page_changed.emit(index)

    def navigate_to(self, index: int) -> None:
        """Programmatically switch to a page."""
        self._nav_list.setCurrentRow(index)

    def set_status(self, message: str) -> None:
        self._status.showMessage(message)

    def _show_about(self) -> None:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>AI-powered bike fitting assistant.</p>"
            f"<p>Upload a side-view video of yourself pedaling, enter your "
            f"body measurements, and get actionable recommendations to "
            f"optimize your bike fit.</p>",
        )
