from ..views.main_window import MainWindow
from ..views.dialogs import EngenhariaDialog, ComercialDialog
import subprocess


class MainController:
    def __init__(self):
        self.main_window = MainWindow()
        self.setup_connections()

    def setup_connections(self):
        def execute_engenharia_model():
            script_path = "src/models/engenharia_model.py"
            subprocess.run(["python", script_path])

        self.main_window.engenharia_button.clicked.connect(execute_engenharia_model)
        self.main_window.comercial_button.clicked.connect(self.show_comercial_dialog)

    def show_main_window(self):
        self.main_window.show()

    def show_engenharia_dialog(self):
        dialog = EngenhariaDialog()
        dialog.exec_()

    def show_comercial_dialog(self):
        dialog = ComercialDialog()
        dialog.exec_()
