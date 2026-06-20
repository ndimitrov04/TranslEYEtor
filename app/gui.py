# Necessary Dependencies
# --------------------------------------------------------------------------------
# Custom
import app.globals as globals
from app.startup.init import *
# Utilities
import pyautogui
from pathlib import Path
# PyQt6 dependencies
from PyQt6.QtCore import (Qt, QTimer, 
                          QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal)
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget, QComboBox,
                             QLabel, QPushButton, QSystemTrayIcon, QMenu, QLineEdit)
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon, QPixmap, QAction

# GUI Setup
# ================================================================================
# Windows API constants - Ensure window is clickthrough at OS level
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
# ================================================================================


# GUI Classes
# ================================================================================

# GUI Text Window Module
class TranslationWindow(QWidget):
    def __init__(self, text, dimensions, font_size):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)
    
        label = QLabel(text, self)
        label.setWordWrap(True)
        label.setFixedWidth(dimensions[0] + 8)
        label.setFixedHeight(dimensions[1] + 8)
        label.move(0, 0)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)
        # White text on black translucent background
        label.setStyleSheet(f"""
            color: white;
            font-size: {font_size+1}px;
            background: rgba(0, 0, 0, 160);
            padding: 4px;
            border-radius: 6px;
        """)

    # Ensure window is clickthrough on OS level when shown
    def showEvent(self, event):
        super().showEvent(event)

        hwnd = int(self.winId())

        styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            styles | WS_EX_LAYERED | WS_EX_TRANSPARENT
        )

# GUI Screenshot Outline Module
class ScreenshotFrame(QWidget):
    def __init__(self, capture_area):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)

        self.resize(capture_area[0], capture_area[1])

        # Loading indicator via pulsing effect, updates every 50ms
        self._pulse_factor = 0.9
        self._pulsing = True
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(50)

    # Ensure window is clickthrough on OS level when shown
    def showEvent(self, event):
        super().showEvent(event)

        hwnd = int(self.winId())

        styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            styles | WS_EX_LAYERED | WS_EX_TRANSPARENT
        )

    # Pulsing effect logic
    @pyqtProperty(float)
    def pulse_factor(self):
        return self._pulse_factor
    @pulse_factor.setter
    def pulse_factor(self, value):
        self._pulse_factor = max(0.3, min(1.0, value))
        self.update()
    def update_pulse(self):
        if self._pulsing:
            # Cycle from 0.3 to 1.0 and back using sine wave
            self._pulse_factor = 0.6 + 0.4 * math.sin(time.time() * 4)
            self.update()
    
    # Draw rect and apply pulsing effect to rect pen
    def paintEvent(self, event):
        painter = QPainter(self)

        base_color = QColor(70, 140, 255)
        base_color.setAlphaF(self._pulse_factor) # Apply pulsing effect
        
        pen = QPen(base_color, 3)
        painter.setPen(pen)
        painter.drawRect(3, 3, self.width() - 6, self.height() - 6)
        painter.end()

    # Fade out frame
    def start_fade_out(self):
        # Stop pulsing
        self._pulsing = False
        self.pulse_timer.stop()
        self._pulse_factor = 1.0
        self.update()

        # Create animation for the "windowOpacity" property
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(2500)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
        # Connect finished signal to close or cleanup if needed
        self.animation.finished.connect(self.cleanup)
    
        self.animation.start()

    def cleanup(self):
        self.close()

# GUI Screen-selection Overlay Window
class SelectionWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodTransparent)

    # Draw screen selection rect
    def paintEvent(self, event):
        painter = QPainter(self)

        base_color = QColor(255, 0, 0)
        
        pen = QPen(base_color, 3)
        painter.setPen(pen)

        if globals.top_left_sel != [0, 0]:
            globals.bottom_right_sel = pyautogui.position()

        painter.drawRect(globals.top_left_sel[0], globals.top_left_sel[1], globals.bottom_right_sel[0] - globals.top_left_sel[0], globals.bottom_right_sel[1] - globals.top_left_sel[1])
        QTimer.singleShot(16, self.update) # ~62FPS (1000ms/16ms = ~62f/s)
        painter.end()

    # Ensure window is clickthrough on OS level when shown
    def showEvent(self, event):
        super().showEvent(event)

        hwnd = int(self.winId())

        styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            styles | WS_EX_TRANSPARENT
        )

# Tray Option Menu
class TrayApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TranslEYEtor")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.drag_pos = None

        # Main container
        root = QWidget()
        root.setObjectName("RootWidget")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(12, 0, 12, 12)
        root_layout.setSpacing(0)

        # Custom bar
        self.title_bar = QWidget()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(46) 

        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(12, 6, 12, 6)
        title_bar_layout.setSpacing(10)

        self.title_icon = QLabel()
        self.title_icon.setFixedSize(28, 28)

        icon_pix = QPixmap(
            str(Path(__file__).resolve().parent) + "/resources/icon.png"
        )

        self.title_icon.setPixmap(
            icon_pix.scaled(
                26, 26,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        self.title_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_text = QLabel("TranslEYEtor")
        self.title_text.setObjectName("TitleText")

        self.close_btn = QPushButton("—")
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.clicked.connect(self.hide_to_tray)

        title_bar_layout.addWidget(self.title_icon)
        title_bar_layout.addWidget(self.title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_btn)

        root_layout.addWidget(self.title_bar)

        # Content card
        content_card = QWidget()
        content_card.setObjectName("ContentCard")

        layout = QVBoxLayout(content_card)
        layout.setContentsMargins(24, 0, 24, 16)
        layout.setSpacing(12)

        root_layout.addWidget(content_card)

        # App icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(
            str(Path(__file__).resolve().parent) + "/resources/icon.png"
        )

        scaled = pixmap.scaled(
            72,
            72,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.icon_label.setPixmap(scaled)

        # Give symmetric vertical breathing room
        self.icon_label.setContentsMargins(0, 16, 0, 48)
        self.icon_label.setFixedHeight(132)

        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Version
        self.ver_label = QLabel(f"Version {version}")
        self.ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ver_label.setObjectName("VersionLabel")
        layout.addWidget(self.ver_label)

        # Usage instructions
        self.inst_label = QLabel(
            "Hold CTRL + SHIFT and drag your mouse over an area you want translated."
        )
        self.inst_label.setWordWrap(True)
        self.inst_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.inst_label)

        # Native language lineedit
        self.native_label = QLabel("Native Language")
        self.native_label.setObjectName("SectionLabel")
        layout.addWidget(self.native_label)

        self.language_textbox = QLineEdit()
        self.language_textbox.setText("English")
        self.language_textbox.setPlaceholderText("Please enter your native language.")
        self.language_textbox.returnPressed.connect(self.native_lang_changed)
        self.language_textbox.textChanged.connect(self.unconfirmed_change)
        self.language_textbox.setFixedHeight(40)
        layout.addWidget(self.language_textbox)

        self.unconfirmed_change_label = QLabel(
            "Press ENTER to confirm change."
        )

        self.unconfirmed_change_label.setStyleSheet(
            "color:#ff6b6b;font-weight:600;"
        )

        layout.addWidget(self.unconfirmed_change_label)
        self.unconfirmed_change_label.hide()

        # Language family combobox
        self.foreign_label = QLabel("Foreign Language Family")
        self.foreign_label.setObjectName("SectionLabel")
        layout.addWidget(self.foreign_label)

        self.lang_family_select = QComboBox()
        self.lang_family_select.addItems(
            [
                "Latin",
                "Cyrillic",
                "Arabic",
                "Chinese",
                "Japanese",
                "Korean"
            ]
        )
        self.lang_family_select.currentIndexChanged.connect(
            self.lang_family_changed
        )
        self.lang_family_select.setFixedHeight(40)
        layout.addWidget(self.lang_family_select)

        # Buttons
        self.minimize_btn = QPushButton("Minimize to Tray")
        self.minimize_btn.clicked.connect(self.hide_to_tray)
        self.minimize_btn.setFixedHeight(42)
        layout.addWidget(self.minimize_btn)
        self.minimize_btn.hide()

        self.interrupt_btn = QPushButton(
            "Interrupt Translation"
        )
        self.interrupt_btn.clicked.connect(
            self.interrupt_translation_pipeline
        )
        self.interrupt_btn.setFixedHeight(42)
        layout.addWidget(self.interrupt_btn)

        # Credits
        self.cred_label = QLabel()
        self.cred_label.setText(
            'Created by <a href="https://nportfolio-1966f0.webflow.io/">Nikola Dimitrov</a>'
        )
        self.cred_label.setOpenExternalLinks(True)
        self.cred_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cred_label)

        # Autofit content
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

        # Styling
        self.setStyleSheet("""
        QWidget {
            font-family: Segoe UI;
            font-size: 13px;
            color: #21435f;
        }

        #RootWidget {
            background: transparent;
        }

        #TitleBar {
            background: #5ec6ff;
            border-top-left-radius: 18px;
            border-top-right-radius: 18px;
        }

        #TitleText {
            color: white;
            font-size: 15px;
            font-weight: 700;
        }

        #ContentCard {
            background: #f7fbff;
            border-bottom-left-radius: 18px;
            border-bottom-right-radius: 18px;
            border-left: 1px solid #d7ebfa;
            border-right: 1px solid #d7ebfa;
            border-bottom: 1px solid #d7ebfa;
        }

        QLabel {
            background: transparent;
        }

        #VersionLabel {
            color: #6d93ad;
            font-size: 12px;
        }

        #SectionLabel {
            font-weight: 600;
            color: #2d5f82;
            margin-top: 4px;
        }

        QLineEdit {
            background: white;
            border: 1px solid #cde6f7;
            border-radius: 10px;
            padding-left: 10px;
        }

        QLineEdit:focus {
            border: 2px solid #5ec6ff;
        }

        QComboBox {
            background: white;
            border: 1px solid #cde6f7;
            border-radius: 10px;
            padding: 6px 34px 6px 10px;
            color: #21435f;
        }

        QComboBox:hover {
            border: 1px solid #5ec6ff;
        }

        QComboBox:focus {
            border: 2px solid #5ec6ff;
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border-left: none;
        }

        QComboBox::down-arrow {
            image: none;
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #5ec6ff;
        }

        QComboBox QAbstractItemView {
            background: white;
            border: 1px solid #cde6f7;
            selection-background-color: #5ec6ff;
            selection-color: white;
            outline: 0;
        }

        QPushButton {
            background: #5ec6ff;
            border: none;
            border-radius: 10px;
            color: white;
            font-weight: 600;
        }       

        QPushButton:hover {
            background: #4dbaf6;
        }

        QPushButton:pressed {
            background: #39adee;
        }

        #CloseButton {
            background: transparent;
            color: white;
            border-radius: 6px;
            font-size: 15px;
        }

        #CloseButton:hover {
            background: rgba(255,255,255,0.18);
        }

        QToolTip {
            background: white;
            color: black;
            border: 1px solid #cde6f7;
        }
        """)

        # Windows taskbar
        import ctypes

        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            myappid
        )

        self.setWindowIcon(
            QIcon(
                str(Path(__file__).resolve().parent)
                + "/resources/icon.png"
            )
        )

        # System tray
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(
            QIcon(
                str(Path(__file__).resolve().parent)
                + "/resources/icon.png"
            )
        )
        self.tray_icon.activated.connect(
            self.on_tray_activated
        )
        self.tray_icon.setToolTip("TranslEYEtor")
        self.tray_icon.show()

        self._current_tray_icon = None

        self.tray_sync_timer = QTimer(self)
        self.tray_sync_timer.setInterval(200)
        self.tray_sync_timer.timeout.connect(
            self.update_tray_icon
        )
        self.tray_sync_timer.start()

        self.update_tray_icon()

        self.tray_menu = QMenu()

        self.show_action = QAction("Show Window", self)
        self.interrupt_action = QAction("Interrupt Translation", self)
        self.quit_action = QAction("Quit", self)

        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.interrupt_action)
        self.tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)

        self.show_action.triggered.connect(self.restore_window)
        self.interrupt_action.triggered.connect(self.interrupt_translation_pipeline)
        self.quit_action.triggered.connect(self.quit_app)

        self.tray_icon.show()

    # Custom window dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if (
            event.buttons()
            == Qt.MouseButton.LeftButton
            and self.drag_pos
        ):
            self.move(
                event.globalPosition().toPoint()
                - self.drag_pos
            )

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    # Main window handlers
    # Creates a simple fallback icon if no .png/.ico is provided.
    def create_app_icon(self) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.darkCyan)
        return QIcon(pixmap)
    
    # Hides window and shows tray notification (optional).
    def hide_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            "App Minimized", 
            "Window hidden. Double-click tray icon to restore.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    # Shows window, activates focus, and raises above other windows.
    def restore_window(self):
        self.show()
        self.activateWindow()
        self.raise_()
        
    # Handles single/double clicks on the tray icon.
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_window()
    
    # Intercepts X button or Alt+F4 to hide instead of quit.
    def closeEvent(self, event):
        event.ignore()  # Prevent actual close
        self.hide_to_tray()

    # Updates tray icon based on server state
    def update_tray_icon(self):
    
        # Priority: Server stopped > Working > Idle
        if not globals.translation_server_ready:
            icon_path = str(Path(__file__).resolve().parent) + "/resources/blocked.png"
        elif globals.working:
            icon_path = str(Path(__file__).resolve().parent) + "/resources/working.png"
        else:
            icon_path = str(Path(__file__).resolve().parent) + "/resources/icon.png"
            
        # Prevent unnecessary UI flicker by skipping identical paths
        if getattr(self, '_current_tray_icon', None) == icon_path:
            return
            
        try:
            self.tray_icon.setIcon(QIcon(icon_path))
            self._current_tray_icon = icon_path
        except Exception as e:
            print(f"[TrayIcon] Failed to load {icon_path}: {e}")


    # Widget handlers
    
    def unconfirmed_change(self):
        self.unconfirmed_change_label.show()

    def native_lang_changed(self):
        globals.native_language = self.language_textbox.text()
        print("New native lang: " + str(globals.native_language))
        # Restart translation server with new options
        globals.translation_server_running = False
        self.unconfirmed_change_label.hide()

    def lang_family_changed(self, index):
        print("Index changed", index)
        # Select easy_reader based on chosen lang list
        globals.lang_code = index
        # Restart translation server with new options
        globals.translation_server_running = False

    def interrupt_translation_pipeline(self):
        print("User has requested a translation server interruption...")
        globals.translation_server_running = False

    def quit_app(self):
        print("Closing TranslEYEtor...")
        import psutil
        for p in psutil.Process(os.getpid()).children(recursive=True):
            p.kill()
        QApplication.quit()
        sys.exit(0)

# ================================================================================
