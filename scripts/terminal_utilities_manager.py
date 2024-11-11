import subprocess

from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton, QVBoxLayout


class TerminalUtilitiesManager(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Add buttons for each terminal utility
        alacritty_btn = QPushButton('Manage Alacritty', self)
        kitty_btn = QPushButton('Manage Kitty', self)
        wezterm_btn = QPushButton('Manage WezTerm', self)

        layout.addWidget(alacritty_btn)
        layout.addWidget(kitty_btn)
        layout.addWidget(wezterm_btn)

        # Connect buttons to actions
        alacritty_btn.clicked.connect(lambda: self.manage_utility("alacritty"))
        kitty_btn.clicked.connect(lambda: self.manage_utility("kitty"))
        wezterm_btn.clicked.connect(lambda: self.manage_utility("wezterm"))

        # Set the layout
        self.setLayout(layout)
        self.setWindowTitle('Terminal Utilities Manager')

    def manage_utility(self, utility_name):
        # Check if the utility is installed
        if self.is_installed(utility_name):
            response = QMessageBox.question(self, 'Uninstall?', f'{utility_name} is installed. Do you want to uninstall it?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if response == QMessageBox.Yes:
                self.uninstall_utility(utility_name)
        else:
            response = QMessageBox.question(self, 'Install?', f'{utility_name} is not installed. Do you want to install it?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if response == QMessageBox.Yes:
                self.install_utility(utility_name)

    def is_installed(self, utility_name):
        """Check if a utility is installed"""
        try:
            subprocess.run([utility_name, '--version'], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            return False

    def install_utility(self, utility_name):
        """Run the install command for the utility"""
        try:
            if utility_name == "alacritty":
                subprocess.run(['sudo', 'zypper', 'install',
                               '-y', 'alacritty'], check=True)
            elif utility_name == "kitty":
                subprocess.run(['sudo', 'zypper', 'install',
                               '-y', 'kitty'], check=True)
            elif utility_name == "wezterm":
                subprocess.run(['sudo', 'zypper', 'install',
                               '-y', 'wezterm'], check=True)
            QMessageBox.information(
                self, "Success", f"{utility_name} installed successfully!")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to install {
                                 utility_name}. Error: {str(e)}")

    def uninstall_utility(self, utility_name):
        """Run the uninstall command for the utility"""
        try:
            subprocess.run(['sudo', 'zypper', 'remove',
                           '-y', utility_name], check=True)
            QMessageBox.information(
                self, "Success", f"{utility_name} uninstalled successfully!")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to uninstall {
                                 utility_name}. Error: {str(e)}")
