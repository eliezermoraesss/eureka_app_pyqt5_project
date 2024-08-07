import ctypes
import locale
import os
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import pyperclip
import sys
from PyQt5.QtCore import Qt, QProcess, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QStyle, QAction, QLabel, QSizePolicy, QMenu, QFrame, QCalendarWidget, QDateEdit, QStyledItemDelegate
from sqlalchemy import create_engine


def exibir_mensagem(title, message, icon_type):
    root = tk.Tk()
    root.withdraw()
    root.lift()  # Garante que a janela esteja na frente
    root.title(title)
    root.attributes('-topmost', True)

    if icon_type == 'info':
        messagebox.showinfo(title, message)
    elif icon_type == 'warning':
        messagebox.showwarning(title, message)
    elif icon_type == 'error':
        messagebox.showerror(title, message)

    root.destroy()


def setup_mssql():
    caminho_do_arquivo = (r"\\192.175.175.4\f\INTEGRANTES\ELIEZER\PROJETO SOLIDWORKS "
                          r"TOTVS\libs-python\user-password-mssql\USER_PASSWORD_MSSQL_PROD.txt")
    try:
        with open(caminho_do_arquivo, 'r') as arquivo:
            string_lida = arquivo.read()
            username, password, database, server = string_lida.split(';')
            return username, password, database, server

    except FileNotFoundError:
        ctypes.windll.user32.MessageBoxW(0,
                                         "Erro ao ler credenciais de acesso ao banco de dados MSSQL.\n\nBase de "
                                         "dados ERP TOTVS PROTHEUS.\n\nPor favor, informe ao desenvolvedor/TI "
                                         "sobre o erro exibido.\n\nTenha um bom dia! ツ",
                                         "CADASTRO DE ESTRUTURA - TOTVS®", 16 | 0)
        sys.exit()

    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, "Ocorreu um erro ao ler o arquivo:", "CADASTRO DE ESTRUTURA - TOTVS®",
                                         16 | 0)
        sys.exit()


class DateDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(DateDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        date_edit = QDateEdit(parent)
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy-MM-dd")
        return date_edit

    def setEditorData(self, editor, index):
        date_str = index.data(Qt.EditRole)
        date = QDate.fromString(date_str, "yyyy-MM-dd")
        editor.setDate(date)

    def setModelData(self, editor, model, index):
        date = editor.date()
        date_str = date.toString("yyyy-MM-dd")
        model.setData(index, date_str, Qt.EditRole)
        # Atualizar banco de dados
        self.update_database(index.row(), date_str)

    def update_database(self, row, new_date):
        # Lógica para atualizar a data no banco de dados
        # Use 'row' para identificar a linha específica e 'new_date' para a nova data
        # Por exemplo:
        # id_qp = self.parent().tree.item(row, 0).text()  # Supondo que a primeira coluna tenha o ID do QP
        id_qp = self.parent().tree.item(row, 0).text()  # Certifique-se de ajustar conforme necessário
        query = f"UPDATE enaplic_management.dbo.tb_end_qps SET dt_completed_qp='{new_date}' WHERE cod_qp='{id_qp}'"

        conn_str = f'DRIVER={driver};SERVER={server};UID={username};PWD={password}'
        engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')
        with engine.connect() as connection:
            connection.execute(query)
        engine.dispose()
        exibir_mensagem("Atualização de Data", "Data atualizada com sucesso!", "info")


def show_message(title, message, icon):
    exibir_mensagem(title, message, icon)


class QpClosedApp(QWidget):
    guia_fechada = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("EUREKA® PCP - v2.0")
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

        self.engine = None
        self.interromper_consulta_sql = False
        self.tree = QTableWidget(self)
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)
        self.process = QProcess(self)

        self.altura_linha = 30
        self.tamanho_fonte_tabela = 10

        self.fonte_tabela = 'Segoe UI'
        fonte_campos = "Segoe UI"
        tamanho_fonte_campos = 16

        self.setStyleSheet("""
            * {
                background-color: #373A40;
            }

            QLabel {
                color: #DFE0E2;
                font-size: 12px;
                font-weight: bold;
                padding-left: 3px;
            }
            
            QLabel#label-line-number {
                font-size: 16px;
                font-weight: normal;
            }
            
            QLabel#label-title {
                margin: 10px;
                font-size: 20px;
                font-weight: normal;
            }

            QLineEdit {
                background-color: #EEEEEE;
                border: 1px solid #262626;
                padding: 5px 10px;
                border-radius: 10px;
                height: 24px;
                font-size: 16px;
            }

            QPushButton {
                background-color: #DC5F00;
                color: #EEEEEE;
                padding: 10px;
                border: 2px;
                border-radius: 8px;
                font-size: 12px;
                height: 20px;
                font-weight: bold;
                margin: 10px 5px;
            }

            QPushButton:hover {
                background-color: #E84545;
                color: #fff
            }
    
            QPushButton:pressed {
                background-color: #6703c5;
                color: #fff;
            }

            QTableWidget {
                border: 1px solid #000000;
                background-color: #686D76;
                padding-left: 10px;
                margin: 5px 0;
            }

            QTableWidget QHeaderView::section {
                background-color: #262626;
                color: #A7A6A6;
                padding: 5px;
                height: 18px;
            }

            QTableWidget QHeaderView::section:horizontal {
                border-top: 1px solid #333;
            }

            QTableWidget::item {
                background-color: #363636;
                color: #fff;
                font-weight: bold;
                padding-right: 8px;
                padding-left: 8px;
            }

            QTableWidget::item:selected {
                background-color: #000000;
                color: #EEEEEE;
                font-weight: bold;
            }
            
            QFrame#line {
                color: white;
                background-color: white;
                border: 1px solid white;
            }
        """)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_enaplic_path = os.path.join(script_dir, '..', 'resources', 'images', 'LOGO.jpeg')
        self.logo_label = QLabel(self)
        self.logo_label.setObjectName('logo-enaplic')
        pixmap_logo = QPixmap(logo_enaplic_path).scaledToWidth(60)
        self.logo_label.setPixmap(pixmap_logo)
        self.logo_label.setAlignment(Qt.AlignRight)

        self.label_title = QLabel("CONSULTA DE QP CONCLUÍDAS", self)
        self.label_title.setObjectName('label-title')

        self.line = QFrame(self)
        self.line.setObjectName('line')
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.label_line_number = QLabel("Total de linhas retornadas na consulta: 0", self)
        self.label_line_number.setObjectName('label-line-number')

        self.label_cod_qp = QLabel("CÓDIGO QP", self)
        self.input_cod_qp = QLineEdit(self)
        self.input_cod_qp.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.label_desc_qp = QLabel("DESCRIÇÃO QP", self)
        self.input_desc_qp = QLineEdit(self)
        self.input_desc_qp.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.btn_consultar = QPushButton("CONSULTAR QPS", self)
        self.btn_consultar.clicked.connect(self.consultar_qps)
        self.btn_consultar.setStyleSheet("background-color: #34675C;")

        self.btn_fechar_guia = QPushButton("FECHAR JANELA", self)
        self.btn_fechar_guia.clicked.connect(self.close_window)
        self.btn_fechar_guia.setStyleSheet("background-color: #DC5F00;")

        header = self.tree.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #262626; color: #A7A6A6; }")
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.verticalHeader().setDefaultSectionSize(self.altura_linha)
        self.tree.verticalHeader().setVisible(False)
        self.tree.setFont(QFont(self.fonte_tabela, self.tamanho_fonte_tabela))
        self.tree.setEditTriggers(QTableWidget.NoEditTriggers)

        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.show_context_menu)
        self.context_menu = QMenu(self)

        self.action_menu_01 = QAction("Largura do conteúdo", self)
        self.action_menu_01.triggered.connect(lambda: self.resize_columns(QHeaderView.ResizeToContents))

        self.action_menu_02 = QAction("Largura da janela", self)
        self.action_menu_02.triggered.connect(lambda: self.resize_columns(QHeaderView.Stretch))

        self.context_menu.addAction(self.action_menu_01)
        self.context_menu.addAction(self.action_menu_02)

        layout_principal = QVBoxLayout()
        layout_logo_title = QHBoxLayout()
        layout_consulta = QHBoxLayout()
        layout_botoes = QHBoxLayout()

        layout_logo_title.addWidget(self.logo_label)
        layout_logo_title.addWidget(self.label_title)
        layout_logo_title.addWidget(self.logo_label)

        layout_consulta.addWidget(self.label_cod_qp)
        layout_consulta.addWidget(self.input_cod_qp)
        layout_consulta.addWidget(self.label_desc_qp)
        layout_consulta.addWidget(self.input_desc_qp)
        layout_consulta.addWidget(self.btn_consultar)

        layout_botoes.addWidget(self.label_line_number)
        layout_botoes.addStretch()
        layout_botoes.addWidget(self.btn_fechar_guia)

        layout_principal.addLayout(layout_logo_title)
        layout_principal.addWidget(self.line)
        layout_principal.addLayout(layout_consulta)
        layout_principal.addWidget(self.tree)
        layout_principal.addLayout(layout_botoes)

        self.setLayout(layout_principal)

        self.date_delegate = DateDelegate(self.tree)
        self.tree.setItemDelegateForColumn(3, self.date_delegate)

    def resize_columns(self, resize_mode):
        header = self.tree.horizontalHeader()
        header.setSectionResizeMode(resize_mode)

    def show_context_menu(self, position):
        self.context_menu.exec_(self.tree.mapToGlobal(position))

    def close_window(self):
        self.guia_fechada.emit()
        self.close()

    def consultar_qps(self):
        cod_qp = self.input_cod_qp.text().strip()
        desc_qp = self.input_desc_qp.text().strip()

        #if not cod_qp and not desc_qp:
            #exibir_mensagem("Erro de Consulta", "Por favor, preencha pelo menos um dos campos para a consulta.", "error")
            #return

        query = "SELECT cod_qp, desc_qp, dt_end_qp, dt_completed_qp FROM enaplic_management.dbo.tb_end_qps"
        if cod_qp:
            query += f" AND cod_qp LIKE '%{cod_qp}%'"
        if desc_qp:
            query += f" AND desc_qp LIKE '%{desc_qp}%'"

        conn_str = f'DRIVER={driver};SERVER={server};UID={username};PWD={password};DATABASE={database}'
        engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            with engine.connect() as connection:
                result = connection.execute(query)
                rows = result.fetchall()

                if not rows:
                    exibir_mensagem("Consulta Vazia", "Nenhum resultado encontrado para os filtros fornecidos.", "warning")
                    return

                self.tree.setRowCount(0)
                self.tree.setColumnCount(len(result.keys()))
                self.tree.setHorizontalHeaderLabels(result.keys())

                for i, row in enumerate(rows):
                    self.tree.insertRow(i)
                    for j, value in enumerate(row):
                        item = QTableWidgetItem(str(value))
                        self.tree.setItem(i, j, item)

                self.label_line_number.setText(f"Total de linhas retornadas na consulta: {len(rows)}")
                self.tree.setEditTriggers(QTableWidget.NoEditTriggers)
                self.tree.setItemDelegateForColumn(3, self.date_delegate)

        except Exception as e:
            exibir_mensagem("Erro de Consulta", str(e), "error")

        finally:
            engine.dispose()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QpClosedApp()
    username, password, database, server = setup_mssql()
    driver = '{SQL Server}'

    window.showMaximized()

    sys.exit(app.exec_())
