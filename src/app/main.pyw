import sys
from PyQt5.QtWidgets import QApplication
from .controllers.main_controller import MainController


def main():
    app = QApplication(sys.argv)
    main_controller = MainController()
    main_controller.show_main_window()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
