import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal, QUuid
from PyQt5.QtWidgets import QSizeGrip, QScrollArea, QFileDialog, QMessageBox

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Application Window")
        self.setGeometry(100, 100, 700, 500)  # x, y, width, height
        
        self.floating_windows = {} # Store by ID
        self.current_target_window_id = None

        # Main layout
        main_layout = QtWidgets.QVBoxLayout()

        # Control Area for New Window and Selector
        control_area_layout = QtWidgets.QHBoxLayout()
        self.new_window_button = QtWidgets.QPushButton("New Floating Window", self)
        self.new_window_button.setToolTip("Create a new floating window.")
        self.new_window_button.clicked.connect(self._create_new_floating_window)
        control_area_layout.addWidget(self.new_window_button)

        self.active_window_selector = QtWidgets.QComboBox(self)
        self.active_window_selector.setToolTip("Select the floating window to control or view.")
        self.active_window_selector.setPlaceholderText("Select a window to control")
        self.active_window_selector.currentIndexChanged.connect(self._update_current_target_from_selector)
        control_area_layout.addWidget(self.active_window_selector, 1) # Give combobox more stretch
        main_layout.addLayout(control_area_layout)

        # Original label
        app_label = QtWidgets.QLabel("This is the main window. Control floating windows from here.", self)
        app_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(app_label)

        # QLineEdit for text input
        self.text_input = QtWidgets.QLineEdit(self)
        self.text_input.setToolTip("Enter text to display in the selected floating window. This text will also be used for the window title.")
        self.text_input.setPlaceholderText("Enter text for the selected floating window")
        self.text_input.textChanged.connect(self.handle_text_changed)
        main_layout.addWidget(self.text_input)

        # Customization controls
        customization_layout = QtWidgets.QFormLayout()

        # Background Color
        self.bg_color_button = QtWidgets.QPushButton("Change BG Color", self)
        self.bg_color_button.setToolTip("Change the background color of the selected floating window.")
        self.bg_color_button.clicked.connect(self._handle_bg_color_change)
        customization_layout.addRow("Background Color:", self.bg_color_button)

        # Transparency
        self.transparency_slider = QtWidgets.QSlider(Qt.Horizontal, self)
        self.transparency_slider.setToolTip("Adjust the transparency of the selected floating window (0 = fully transparent, 100 = fully opaque).")
        self.transparency_slider.setRange(0, 100)
        self.transparency_slider.setValue(100) 
        self.transparency_slider.valueChanged.connect(self._handle_transparency_change)
        customization_layout.addRow("Transparency:", self.transparency_slider)

        # Font Family
        self.font_family_combo = QtWidgets.QFontComboBox(self)
        self.font_family_combo.setToolTip("Select the font family for the text in the selected floating window.")
        self.font_family_combo.currentFontChanged.connect(self._handle_font_family_change)
        customization_layout.addRow("Font Family:", self.font_family_combo)

        # Font Size
        self.font_size_spinbox = QtWidgets.QSpinBox(self)
        self.font_size_spinbox.setToolTip("Select the font size for the text in the selected floating window.")
        self.font_size_spinbox.setRange(8, 72)
        self.font_size_spinbox.valueChanged.connect(self._handle_font_size_change)
        customization_layout.addRow("Font Size:", self.font_size_spinbox)

        # Font Color
        self.font_color_button = QtWidgets.QPushButton("Change Font Color", self)
        self.font_color_button.setToolTip("Change the text color of the selected floating window.")
        self.font_color_button.clicked.connect(self._handle_font_color_change)
        customization_layout.addRow("Font Color:", self.font_color_button)

        # Show/Hide Floating Window Buttons
        self.show_button = QtWidgets.QPushButton("Show Selected Window", self)
        self.show_button.setToolTip("Show (fade-in) the currently selected floating window.")
        self.show_button.clicked.connect(self._handle_show_selected)
        customization_layout.addRow(self.show_button)

        self.hide_button = QtWidgets.QPushButton("Hide Selected Window", self)
        self.hide_button.setToolTip("Hide (fade-out) the currently selected floating window. This will also remove it from the selector.")
        self.hide_button.clicked.connect(self._handle_hide_selected)
        customization_layout.addRow(self.hide_button)

        # Text Scroll Animation Buttons
        self.start_scroll_button = QtWidgets.QPushButton("Start Scroll on Selected", self)
        self.start_scroll_button.setToolTip("Start the text scrolling animation on the selected floating window.")
        self.start_scroll_button.clicked.connect(self._handle_start_scroll_selected)
        customization_layout.addRow(self.start_scroll_button)

        self.stop_scroll_button = QtWidgets.QPushButton("Stop Scroll on Selected", self)
        self.stop_scroll_button.setToolTip("Stop the text scrolling animation on the selected floating window.")
        self.stop_scroll_button.clicked.connect(self._handle_stop_scroll_selected)
        customization_layout.addRow(self.stop_scroll_button)

        # Save/Load Text Buttons
        self.save_text_button = QtWidgets.QPushButton("Save Selected's Text", self)
        self.save_text_button.setToolTip("Save the text content of the selected floating window to a file.")
        self.save_text_button.clicked.connect(self._save_text_to_file)
        customization_layout.addRow(self.save_text_button)

        self.load_text_button = QtWidgets.QPushButton("Load Text to Selected", self)
        self.load_text_button.setToolTip("Load text content from a file into the selected floating window.")
        self.load_text_button.clicked.connect(self._load_text_from_file)
        customization_layout.addRow(self.load_text_button)
        
        main_layout.addLayout(customization_layout)

        # Set central widget
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        self._update_controls_for_no_target() # Initially disable/set placeholder for controls

    def get_current_target_window(self):
        if self.current_target_window_id:
            return self.floating_windows.get(self.current_target_window_id)
        return None

    def _create_new_floating_window(self):
        new_window = FloatingWindow()
        self.floating_windows[new_window.id] = new_window
        new_window.window_closed.connect(self._handle_floating_window_closed)
        
        window_display_name = f"Window {self.active_window_selector.count() + 1} ({new_window.id[:4]}..)"
        self.active_window_selector.addItem(window_display_name, new_window.id)
        self.active_window_selector.setCurrentIndex(self.active_window_selector.count() - 1)
        
        # Initialize font from main window controls
        initial_font = self.font_family_combo.currentFont()
        new_window.update_font_family(initial_font.family())
        new_window.update_font_size(self.font_size_spinbox.value()) # Use current spinbox value
        
        new_window.fade_in()
        # _update_current_target_from_selector will be called, which updates controls
        self.text_input.setFocus() # Set focus to text input after new window creation

    def _update_current_target_from_selector(self, index):
        if index == -1:
            self.current_target_window_id = None
            self._update_controls_for_no_target()
        else:
            self.current_target_window_id = self.active_window_selector.itemData(index)
            self._update_controls_from_target()

    def _update_controls_from_target(self):
        target = self.get_current_target_window()
        if target:
            self.text_input.setText(target.get_current_text())
            self.text_input.setEnabled(True)
            
            # Block signals while setting values to prevent feedback loops
            self.font_family_combo.blockSignals(True)
            self.font_family_combo.setCurrentFont(QtGui.QFont(target.current_font_family))
            self.font_family_combo.blockSignals(False)
            
            self.font_size_spinbox.blockSignals(True)
            self.font_size_spinbox.setValue(target.current_font_size)
            self.font_size_spinbox.blockSignals(False)

            self.transparency_slider.blockSignals(True)
            self.transparency_slider.setValue(int(target.windowOpacity() * 100))
            self.transparency_slider.blockSignals(False)

            # Enable all control buttons
            for i in range(self.customization_layout.rowCount()):
                widget = self.customization_layout.itemAt(i, QtWidgets.QFormLayout.FieldRole).widget()
                if widget: widget.setEnabled(True)
            self.text_input.setPlaceholderText("Enter text for the selected floating window")

        else: 
            self._update_controls_for_no_target()
            
    def _update_controls_for_no_target(self):
        self.text_input.setText("")
        self.text_input.setPlaceholderText("No window selected. Create or select one.")
        self.text_input.setEnabled(False)
        
        for i in range(self.customization_layout.rowCount()):
            item = self.customization_layout.itemAt(i, QtWidgets.QFormLayout.FieldRole)
            if item and item.widget():
                 item.widget().setEnabled(False)
        
        self.font_family_combo.setEnabled(True) 
        self.font_size_spinbox.setEnabled(True)


    def _handle_floating_window_closed(self, window_id):
        if window_id in self.floating_windows:
            del self.floating_windows[window_id]
        
        for i in range(self.active_window_selector.count()):
            if self.active_window_selector.itemData(i) == window_id:
                self.active_window_selector.removeItem(i)
                break
        
        if self.active_window_selector.count() == 0:
            self.current_target_window_id = None
            self._update_controls_for_no_target()


    def handle_text_changed(self, text):
        target = self.get_current_target_window()
        if target:
            target.update_text(text)

    def _handle_bg_color_change(self):
        target = self.get_current_target_window()
        if target:
            color = QtWidgets.QColorDialog.getColor(parent=self) 
            if color.isValid():
                target.set_background_color(color.name())

    def _handle_transparency_change(self, value):
        target = self.get_current_target_window()
        if target:
            opacity = value / 100.0
            target.set_transparency(opacity)

    def _handle_font_family_change(self, font):
        target = self.get_current_target_window()
        if target:
            target.update_font_family(font.family())

    def _handle_font_size_change(self, size):
        target = self.get_current_target_window()
        if target:
            target.update_font_size(size)

    def _handle_font_color_change(self):
        target = self.get_current_target_window()
        if target:
            color = QtWidgets.QColorDialog.getColor(initial=QtGui.QColor(target.current_font_color), parent=self)
            if color.isValid():
                target.update_font_color(color.name())
    
    def _handle_show_selected(self):
        target = self.get_current_target_window()
        if target: 
            target.fade_in()
        else:
            QMessageBox.information(self, "Info", "No window selected to show.")


    def _handle_hide_selected(self):
        target = self.get_current_target_window()
        if target: 
            target.fade_out()
        else:
            QMessageBox.information(self, "Info", "No window selected to hide.")


    def _handle_start_scroll_selected(self):
        target = self.get_current_target_window()
        if target: 
            target.start_text_scroll()
        else:
            QMessageBox.information(self, "Info", "No window selected to start scroll.")


    def _handle_stop_scroll_selected(self):
        target = self.get_current_target_window()
        if target: 
            target.stop_text_scroll()
        else:
            QMessageBox.information(self, "Info", "No window selected to stop scroll.")


    def _save_text_to_file(self):
        target = self.get_current_target_window()
        if not target:
            QMessageBox.information(self, "Info", "No window selected to save text from.")
            return
        current_text = target.get_current_text()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Text", f"floating_text_{target.id[:4]}.txt", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(current_text)
            except IOError as e:
                QMessageBox.warning(self, "Save Error", f"Could not save file: {e}")

    def _load_text_from_file(self):
        target = self.get_current_target_window()
        if not target:
            QMessageBox.information(self, "Info", "No window selected to load text into.")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Text", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    target.update_text(content)
                    self.text_input.setText(content) 
            except (IOError, UnicodeDecodeError) as e:
                QMessageBox.warning(self, "Load Error", f"Could not load file: {e}")


class FloatingWindow(QtWidgets.QWidget):
    window_closed = pyqtSignal(str) 

    def __init__(self):
        super().__init__()
        self.id = QUuid.createUuid().toString() 
        self.base_title = "Floating Window"
        self.setWindowTitle(f"{self.base_title} ({self.id[:4]}...)")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setGeometry(200, 200, 300, 100) 
        self.drag_position = None
        self.animation_duration = 500
        self.fade_animation = None 
        self.setWindowOpacity(0.0) 

        self.current_font_family = "Arial" 
        self.current_font_size = 16 
        self.current_font_color = "#000000" 

        self._background_color = "white"
        self.set_background_color(self._background_color) 

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5) 

        self.label = QtWidgets.QLabel("Hello World", self)
        self.label.setAlignment(Qt.AlignCenter) 
        self.label.setWordWrap(True) 

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(self.label)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self._apply_font_changes() 
        
        self.main_layout.insertWidget(0, self.scroll_area) 

        self.scroll_timer = QTimer(self)
        self.scroll_timer.setInterval(50) 
        self.scroll_timer.timeout.connect(self._perform_scroll)
        self.scroll_step = 1 

        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addStretch()  
        self.size_grip = QSizeGrip(self)
        bottom_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        
        self.main_layout.addLayout(bottom_layout)
        self.setLayout(self.main_layout)

    def fade_in(self):
        if self.fade_animation and self.fade_animation.state() == QPropertyAnimation.Running:
            self.fade_animation.stop() 
        
        self.show() 
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(self.animation_duration)
        self.fade_animation.setStartValue(self.windowOpacity()) 
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()

    def fade_out(self):
        if self.fade_animation and self.fade_animation.state() == QPropertyAnimation.Running:
            self.fade_animation.stop() 

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(self.animation_duration)
        self.fade_animation.setStartValue(self.windowOpacity()) 
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.finished.connect(self._emit_close_signal) 
        self.fade_animation.start()

    def _emit_close_signal(self):
        self.hide() 
        self.window_closed.emit(self.id) 

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            event.accept()

    def _perform_scroll(self):
        v_scrollbar = self.scroll_area.verticalScrollBar()
        if v_scrollbar.maximum() > 0: 
            new_value = v_scrollbar.value() + self.scroll_step
            v_scrollbar.setValue(new_value)
            if v_scrollbar.value() >= v_scrollbar.maximum() and self.scroll_step > 0: 
                v_scrollbar.setValue(0) 

    def start_text_scroll(self):
        self.scroll_timer.start()

    def stop_text_scroll(self):
        self.scroll_timer.stop()

    def update_text(self, new_text):
        self.label.setText(new_text)
        self.scroll_area.verticalScrollBar().setValue(0) 
        self.label.adjustSize() 
        
        if new_text:
            self.setWindowTitle(f"{new_text[:25]}... ({self.id[:4]}..)" if len(new_text) > 25 else f"{new_text} ({self.id[:4]}..)")
        else:
            self.setWindowTitle(f"{self.base_title} ({self.id[:4]}...)")


    def get_current_text(self):
        return self.label.text()

    def set_background_color(self, color_name_or_hex):
        self._background_color = color_name_or_hex
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(self._background_color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def set_transparency(self, opacity_value):
        self.setWindowOpacity(opacity_value)

    def _apply_font_changes(self):
        font = QtGui.QFont(self.current_font_family, self.current_font_size)
        self.label.setFont(font)
        self.label.setStyleSheet(f"color: {self.current_font_color};")
        self.label.adjustSize() 

    def update_font_family(self, font_family):
        self.current_font_family = font_family
        self._apply_font_changes()

    def update_font_size(self, font_size):
        self.current_font_size = font_size
        self._apply_font_changes()

    def update_font_color(self, font_color_name_or_hex):
        self.current_font_color = font_color_name_or_hex
        self._apply_font_changes()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    main_window = MainWindow() 
    main_window.show()

    sys.exit(app.exec_())
