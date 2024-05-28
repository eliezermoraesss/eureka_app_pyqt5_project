from ..views.main_window import MainWindow
from src.app.controllers.dialogs_controller import DialogsController


class MainController:
    def __init__(self):
        self.main_window = MainWindow()
        self.dialogs_controller = DialogsController()

        self.main_window.btn_eng.clicked.connect(self.show_engenharia_dialog)
        self.main_window.btn_comercial.clicked.connect(self.show_comercial_dialog)

    def show_main_window(self):
        self.main_window.show()

    def show_engenharia_dialog(self):
        self.dialogs_controller.show_engenharia_dialog()

    def show_comercial_dialog(self):
        self.dialogs_controller.show_comercial_dialog()
