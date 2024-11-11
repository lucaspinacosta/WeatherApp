import subprocess
import sys

from PyQt5.QtWidgets import (QApplication, QLabel, QMessageBox, QPushButton,
                             QVBoxLayout, QWidget)
from scripts.terminal_utilities_manager import TerminalUtilitiesManager


class SystemManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set up the layout
        layout = QVBoxLayout()

        # Title label
        title = QLabel('System Management Tool', self)
        layout.addWidget(title)

        # Terminal Utilities Management Button
        terminal_util_btn = QPushButton('Manage Terminal Utilities', self)
        terminal_util_btn.clicked.connect(self.manage_terminal_utilities)
        layout.addWidget(terminal_util_btn)

        # System Checks Button
        system_checks_btn = QPushButton('Perform System Checks', self)
        system_checks_btn.clicked.connect(self.perform_system_checks)
        layout.addWidget(system_checks_btn)

        # Nerd Fonts and Terminal Setup Button
        nerd_fonts_btn = QPushButton(
            'Install Nerd Fonts and Setup Terminals', self)
        nerd_fonts_btn.clicked.connect(self.install_nerd_fonts)
        layout.addWidget(nerd_fonts_btn)

        # Set layout
        self.setLayout(layout)
        self.setWindowTitle('System Manager')
        self.setGeometry(300, 300, 400, 300)
        self.terminal_util_fnc = TerminalUtilitiesManager()
        self.terminal_util_fnc.initUI()

    # Functions for each task
    def manage_terminal_utilities(self):
        # Here you can create a new window for terminal utilities management
        msg = QMessageBox()
        msg.setText("Managing Terminal Utilities...")
        msg.exec_()
        self.terminal_util_fnc.manage_utility()
        # You can add actual checks and install/remove logic here

    def perform_system_checks(self):
        # Here you can implement system checks as defined in script3
        msg = QMessageBox()
        msg.setText("Performing System Checks...")
        msg.exec_()
        # Add system checks like checking distribution, package managers, etc.

    def install_nerd_fonts(self):
        # This would be for installing nerd fonts (replicating script5)
        msg = QMessageBox()
        msg.setText("Installing Nerd Fonts...")
        msg.exec_()
        # Use subprocess to download/install nerd fonts as done in script 5


if __name__ == '__main__':
    app = QApplication(sys.argv)
    manager = SystemManager()
    manager.show()
    sys.exit(app.exec_())
