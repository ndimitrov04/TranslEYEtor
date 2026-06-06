import Globals
from Install import *

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

        if Globals.top_left_sel != [0, 0]:
            Globals.bottom_right_sel = pyautogui.position()

        painter.drawRect(Globals.top_left_sel[0], Globals.top_left_sel[1], Globals.bottom_right_sel[0] - Globals.top_left_sel[0], Globals.bottom_right_sel[1] - Globals.top_left_sel[1])
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
        
        # Basic parameters
        self.setWindowTitle("TranslEYETor")
        self.resize(320, 200)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)  # Explicitly opaque
        
        # Options UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        self.icon_label = QLabel()
        pixmap = QPixmap("icon.png")
        scaled = pixmap.scaled(
            64, 64,
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.SmoothTransformation
        )
        self.icon_label.setPixmap(scaled)
        layout.addWidget(self.icon_label)

        self.ver_label = QLabel(f"Ver. {version}")
        layout.addWidget(self.ver_label)

        self.inst_label = QLabel("Hold CTRL+SHIFT and drag your mouse over an area you want translated.")
        layout.addWidget(self.inst_label)

        self.native_label = QLabel("Native Language")
        layout.addWidget(self.native_label)
        
        self.language_textbox = QTextEdit()
        self.language_textbox.setPlainText("English")
        self.language_textbox.setPlaceholderText("Please enter your native language.")
        self.language_textbox.textChanged.connect(self.native_lang_changed)
        self.language_textbox.setFixedHeight(26)
        layout.addWidget(self.language_textbox)

        self.foreign_label = QLabel("Foreign Language Family")
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
        self.lang_family_select.currentIndexChanged.connect(self.lang_family_changed)
        layout.addWidget(self.lang_family_select)

        self.minimize_btn = QPushButton("Minimize to Tray")
        self.minimize_btn.clicked.connect(self.hide_to_tray)
        layout.addWidget(self.minimize_btn)


        # Set windows taskbar icon
        # Tell windows that python is a host for this app
        # and that windows should use the icon of the app, not the host.
        import ctypes
        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        # Set app icon
        self.setWindowIcon(QIcon("icon.png"))


        # System Tray Setup
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.setToolTip("TranslEYEtor")
        self.tray_icon.show()
        
        # Tray Menu
        self.tray_menu = QMenu()
        self.show_action = QAction("Show Window", self)
        self.quit_action = QAction("Quit", self)
        
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Connect menu actions
        self.show_action.triggered.connect(self.restore_window)
        self.quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.show()
    

    # Main window handlers

    def create_app_icon(self) -> QIcon:
        """Creates a simple fallback icon if no .png/.ico is provided."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.darkCyan)
        return QIcon(pixmap)
        
    def hide_to_tray(self):
        """Hides window and shows tray notification (optional)."""
        self.hide()
        # Optional: Show brief system notification
        self.tray_icon.showMessage(
            "App Minimized", 
            "Window hidden. Double-click tray icon to restore.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        
    def restore_window(self):
        """Shows window, activates focus, and raises above other windows."""
        self.show()
        self.activateWindow()
        self.raise_()
        
    def on_tray_activated(self, reason):
        """Handles single/double clicks on the tray icon."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_window()
            
    def closeEvent(self, event):
        """Intercepts X button or Alt+F4 to hide instead of quit."""
        event.ignore()  # Prevent actual close
        self.hide_to_tray()


    # Widget handlers

    def native_lang_changed(self):
        Globals.native_language = self.language_textbox.toPlainText()
        print("New native lang: " + str(Globals.native_language))

    def lang_family_changed(self, index):
        print("Index changed", index)
        # Select easy_reader based on chosen lang list
        match index:
            case 0:
                Globals.easy_reader = Globals.easy_reader_latin
            case 1:
                Globals.easy_reader = Globals.easy_reader_cyrillic
            case 2:
                Globals.easy_reader = Globals.easy_reader_arabic
            case 3:
                Globals.easy_reader = Globals.easy_reader_chinese
            case 4:
                Globals.easy_reader = Globals.easy_reader_japanese
            case 5:
                Globals.easy_reader = Globals.easy_reader_korean
        print(Globals.easy_reader.lang_char)

# ================================================================================
