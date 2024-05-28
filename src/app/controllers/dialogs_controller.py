from src.app.views.dialogs import EngenhariaDialog, ComercialDialog


class DialogsController:
    def __init__(self):
        self.engenharia_dialog = None
        self.comercial_dialog = None

    def show_engenharia_dialog(self):
        self.engenharia_dialog = EngenhariaDialog()
        self.engenharia_dialog.exec_()

    def show_comercial_dialog(self):
        self.comercial_dialog = ComercialDialog()
        self.comercial_dialog.exec_()
