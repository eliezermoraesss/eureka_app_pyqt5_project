from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSizePolicy, QSpacerItem
from PyQt5.QtGui import QIcon, QColor, QPalette


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SMARTPLIC® v2.2.1 - Dark theme - TEST_DB")

        # Configurar o ícone da janela
        icon_path = "src/resources/images/010.png"
        self.setWindowIcon(QIcon(icon_path))

        # Ajuste a cor de fundo da janela
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor('#363636'))  # Substitua pela cor desejada
        self.setPalette(palette)

        # Aplicar folha de estilo ao aplicativo
        self.setStyleSheet("""
            * {
                background-color: #363636;
            }

            QLabel, QCheckBox {
                color: #EEEEEE;
                font-size: 11px;
                font-weight: bold;
            }

            QLineEdit {
                background-color: #A7A6A6;
                border: 1px solid #262626;
                padding: 5px;
                border-radius: 8px;
            }

            QPushButton {
                background-color: #0a79f8;
                color: #fff;
                padding: 5px 15px;
                border: 2px;
                border-radius: 8px;
                font-size: 11px;
                height: 20px;
                font-weight: bold;
                margin-top: 6px;
                margin-bottom: 6px;
            }

            QPushButton:hover {
                background-color: #fff;
                color: #0a79f8
            }

            QPushButton:pressed {
                background-color: #6703c5;
                color: #fff;
            }
        """)

        # Botões
        self.btn_eng = QPushButton("Engenharia", self)
        self.btn_eng.setMinimumWidth(150)

        self.btn_comercial = QPushButton("Comercial", self)
        self.btn_comercial.setMinimumWidth(150)

        layout = QVBoxLayout()
        layout_linha_01 = QHBoxLayout()

        layout_linha_01.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout_linha_01.addWidget(self.btn_eng)
        layout_linha_01.addWidget(self.btn_comercial)
        layout_linha_01.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(layout_linha_01)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
