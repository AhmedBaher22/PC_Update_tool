import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTextEdit, QLabel
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt

from canWithIsoTpSender import *

class FileBrowserApp(QWidget):
    def __init__(self):
        super().__init__()
        self.byte_array = None  # Variable to store the byte array
        self.init_ui()

    def init_ui(self):
        # Set window properties
        self.setWindowTitle("File Browser and Byte Reader")
        self.showMaximized()  # Make the window full screen

        # Layout
        layout = QVBoxLayout()

        # Instructions label
        self.label = QLabel(
            "Click 'Browse File' to select a file and view its byte content:")
        self.label.setFont(QFont("Arial", 16, QFont.Bold))
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Text area to show file content as byte array
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Courier New", 12))
        self.text_area.setStyleSheet(
            "background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self.text_area)

        # Button to browse files
        self.browse_button = QPushButton("Browse File")
        self.browse_button.setFont(QFont("Arial", 14, QFont.Bold))
        self.browse_button.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px; border: none;"
        )
        self.browse_button.setCursor(Qt.PointingHandCursor)
        self.browse_button.clicked.connect(self.open_file_browser)
        layout.addWidget(self.browse_button)

        # Set layout
        self.setLayout(layout)

        # Apply color theme
        self.set_background_color()

    def set_background_color(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f9f9f9"))
        self.setPalette(palette)

    def open_file_browser(self):
        # Open file dialog to select a file
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*)"
        )

        if file_name:
            try:
                # Read file content as byte array
                with open(file_name, "rb") as file:
                    self.byte_array = file.read()

                # Convert byte array to list of integers
                byte_list = list(self.byte_array)

                canTpSend(byte_list)

                # Display byte content and list of integers in the text area
                display_text = (
                    f"Byte Array:\n{self.byte_array}\n\n"
                    f"Byte List (as integers):\n{byte_list}"
                )
                self.text_area.setText(display_text)
            except Exception as e:
                self.text_area.setText(f"Error reading file: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileBrowserApp()
    window.show()
    sys.exit(app.exec_())
