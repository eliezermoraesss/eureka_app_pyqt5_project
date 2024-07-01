import locale
import sys

import pyodbc
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QStyle, QAction, QDateEdit, QLabel, QMessageBox, \
    QSizePolicy, QTabWidget, QMenu
from PyQt5.QtGui import QFont, QColor, QIcon, QDesktopServices, QPixmap
from PyQt5.QtCore import Qt, QCoreApplication, QDate, QUrl, QProcess, pyqtSignal
import pyperclip
import pandas as pd
import ctypes
from datetime import date, datetime
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
import os


def ajustar_largura_coluna_descricao(tree_widget):
    header = tree_widget.horizontalHeader()
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)


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


def validar_campos(codigo_produto, numero_qp, numero_op):

    if len(codigo_produto) != 13 and not codigo_produto == '':
        exibir_mensagem("ATENÇÃO!",
                             "Produto não encontrado!\n\nCorrija e tente "
                             f"novamente.\n\nツ\n\nSMARTPLIC®",
                             "info")
        return True

    if len(numero_op) != 6 and not numero_op == '':
        exibir_mensagem("ATENÇÃO!",
                             "Ordem de Produção não encontrada!\n\nCorrija e tente "
                             f"novamente.\n\nツ\n\nSMARTPLIC®",
                             "info")
        return True

    if len(numero_qp.zfill(6)) != 6 and not numero_qp == '':
        exibir_mensagem("ATENÇÃO!",
                             "QP não encontrada!\n\nCorrija e tente "
                             f"novamente.\n\nツ\n\nSMARTPLIC®",
                             "info")
        return True


def numero_linhas_consulta(query_consulta):

    order_by_a_remover = "ORDER BY op.R_E_C_N_O_ DESC;"
    query_sem_order_by = query_consulta.replace(order_by_a_remover, "")

    query = f"""
                SELECT 
                    COUNT(*) AS total_records
                FROM ({query_sem_order_by}) AS combined_results;
            """
    return query


class PcpApp(QWidget):
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
        self.nova_janela = None

        self.tabWidget = QTabWidget(self)  # Adicione um QTabWidget ao layout principal
        self.tabWidget.setTabsClosable(True)  # Adicione essa linha para permitir o fechamento de guias
        self.tabWidget.tabCloseRequested.connect(self.fechar_guia)
        self.tabWidget.setVisible(False)  # Inicialmente, a guia está invisível

        self.guias_abertas = []
        self.guias_abertas_onde_usado = []
        self.guias_abertas_saldo = []

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
                font-size: 14px;
                font-weight: regular;
            }
            
            QDateEdit {
                background-color: #DFE0E2;
                border: 1px solid #262626;
                margin-bottom: 20px;
                padding: 5px 10px;
                border-radius: 10px;
                height: 24px;
                font-size: 16px;
            }
            
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            
            QDateEdit::down-arrow {
                image: url(../resources/images/arrow.png);
                width: 10px;
                height: 10px;
            }

            QLineEdit {
                background-color: #DFE0E2;
                border: 1px solid #262626;
                padding: 5px 10px;
                border-radius: 10px;
                height: 24px;
                font-size: 16px;
            }

            QPushButton {
                background-color: #DC5F00;
                color: #EEEEEE;
                padding: 7px 10px;
                border: 2px;
                border-radius: 8px;
                font-size: 12px;
                height: 20px;
                font-weight: bold;
                margin: 0px 5px 10px 5px;
            }
            
            QPushButton#btn_engenharia {
                background-color: #0a79f8;
            }
            
            QPushButton#btn_compras {
                background-color: #836FFF;
            }

            QPushButton:hover, QPushButton:hover#btn_engenharia, QPushButton:hover#btn_compras {
                background-color: #E84545;
                color: #fff
            }
    
            QPushButton:pressed, QPushButton:pressed#btn_engenharia, QPushButton:pressed#btn_compras {
                background-color: #6703c5;
                color: #fff;
            }

            QTableWidget {
                border: 1px solid #000000;
                background-color: #686D76;
                padding-left: 10px;
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
        """)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_enaplic_path = os.path.join(script_dir, '..', 'resources', 'images', 'LOGO.jpeg')
        self.logo_label = QLabel(self)
        self.logo_label.setObjectName('logo-enaplic')
        pixmap_logo = QPixmap(logo_enaplic_path).scaledToWidth(60)
        self.logo_label.setPixmap(pixmap_logo)
        self.logo_label.setAlignment(Qt.AlignRight)

        self.label_codigo = QLabel("Código:", self)
        self.label_descricao_prod = QLabel("Descrição:", self)
        self.label_contem_descricao_prod = QLabel("Contém na descrição:", self)
        self.label_contem_descricao_prod.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.label_OP = QLabel("Número OP:", self)
        self.label_qp = QLabel("Número QP:", self)
        self.label_data_inicio = QLabel("Data inicial:", self)
        self.label_data_inicio.setObjectName("data-inicio")
        self.label_data_fim = QLabel("Data final:", self)
        self.label_data_fim.setObjectName("data-fim")
        self.label_campo_observacao = QLabel("Observação:", self)
        self.label_line_number = QLabel("", self)
        self.label_line_number.setVisible(False)

        self.campo_codigo = QLineEdit(self)
        self.campo_codigo.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_codigo.setMaxLength(13)
        self.campo_codigo.setFixedWidth(170)
        self.add_clear_button(self.campo_codigo)

        self.campo_descricao_prod = QLineEdit(self)
        self.campo_descricao_prod.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_descricao_prod.setMaxLength(60)
        self.campo_descricao_prod.setFixedWidth(280)
        self.add_clear_button(self.campo_descricao_prod)

        self.campo_contem_descricao_prod = QLineEdit(self)
        self.campo_contem_descricao_prod.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_contem_descricao_prod.setMaxLength(60)
        self.campo_contem_descricao_prod.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_clear_button(self.campo_contem_descricao_prod)

        self.campo_qp = QLineEdit(self)
        self.campo_qp.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_qp.setMaxLength(6)
        self.campo_qp.setFixedWidth(110)
        self.add_clear_button(self.campo_qp)

        self.campo_OP = QLineEdit(self)
        self.campo_OP.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_OP.setMaxLength(6)
        self.campo_OP.setFixedWidth(110)
        self.add_clear_button(self.campo_OP)

        self.campo_data_inicio = QDateEdit(self)
        self.campo_data_inicio.setFont(QFont(fonte_campos, 10))
        self.campo_data_inicio.setFixedWidth(150)
        self.campo_data_inicio.setCalendarPopup(True)
        self.campo_data_inicio.setDisplayFormat("dd/MM/yyyy")

        data_atual = QDate.currentDate()
        intervalo_meses = 12
        data_inicio = data_atual.addMonths(-intervalo_meses)

        self.campo_data_inicio.setDate(data_inicio)
        self.add_today_button(self.campo_data_inicio)

        self.campo_data_fim = QDateEdit(self)
        self.campo_data_fim.setFont(QFont(fonte_campos, 10))
        self.campo_data_fim.setFixedWidth(150)
        self.campo_data_fim.setCalendarPopup(True)
        self.campo_data_fim.setDisplayFormat("dd/MM/yyyy")
        self.campo_data_fim.setDate(QDate().currentDate())
        self.add_today_button(self.campo_data_fim)

        self.campo_observacao = QLineEdit(self)
        self.campo_observacao.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_observacao.setMaxLength(60)
        self.campo_observacao.setFixedWidth(400)
        self.add_clear_button(self.campo_observacao)

        self.btn_consultar = QPushButton("Pesquisar", self)
        self.btn_consultar.clicked.connect(self.executar_consulta)
        self.btn_consultar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_consultar_estrutura = QPushButton("Consultar Estrutura", self)
        self.btn_consultar_estrutura.clicked.connect(lambda: self.executar_consulta_estrutura(self.tree))
        self.btn_consultar_estrutura.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_consultar_estrutura.setEnabled(False)

        self.btn_abrir_compras = QPushButton("Compras", self)
        self.btn_abrir_compras.setObjectName("btn_compras")
        self.btn_abrir_compras.clicked.connect(self.abrir_modulo_compras)
        self.btn_abrir_compras.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_abrir_engenharia = QPushButton("Engenharia", self)
        self.btn_abrir_engenharia.setObjectName("btn_engenharia")
        self.btn_abrir_engenharia.clicked.connect(self.abrir_modulo_engenharia)
        self.btn_abrir_engenharia.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_onde_e_usado = QPushButton("Onde é usado?", self)
        self.btn_onde_e_usado.clicked.connect(lambda: self.executar_consulta_onde_usado(self.tree))
        self.btn_onde_e_usado.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_onde_e_usado.setEnabled(False)

        self.btn_saldo_estoque = QPushButton("Saldos em Estoque", self)
        self.btn_saldo_estoque.clicked.connect(lambda: self.executar_saldo_em_estoque(self.tree))
        self.btn_saldo_estoque.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_saldo_estoque.setEnabled(False)

        self.btn_limpar = QPushButton("Limpar", self)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_limpar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_nova_janela = QPushButton("Nova Janela", self)
        self.btn_nova_janela.clicked.connect(self.abrir_nova_janela)
        self.btn_nova_janela.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_abrir_desenho = QPushButton("Abrir Desenho", self)
        self.btn_abrir_desenho.clicked.connect(lambda: self.abrir_desenho(self.tree))
        self.btn_abrir_desenho.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_abrir_desenho.setEnabled(False)

        self.btn_exportar_excel = QPushButton("Exportar Excel", self)
        self.btn_exportar_excel.clicked.connect(self.exportar_excel)
        self.btn_exportar_excel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_exportar_excel.setEnabled(False)

        self.btn_fechar = QPushButton("Fechar", self)
        self.btn_fechar.clicked.connect(self.fechar_janela)
        self.btn_fechar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.campo_codigo.returnPressed.connect(self.executar_consulta)
        self.campo_qp.returnPressed.connect(self.executar_consulta)
        self.campo_OP.returnPressed.connect(self.executar_consulta)
        self.campo_descricao_prod.returnPressed.connect(self.executar_consulta)
        self.campo_contem_descricao_prod.returnPressed.connect(self.executar_consulta)
        self.campo_observacao.returnPressed.connect(self.executar_consulta)

        layout = QVBoxLayout()
        layout_campos_01 = QHBoxLayout()
        layout_campos_02 = QHBoxLayout()
        self.layout_buttons = QHBoxLayout()
        self.layout_footer_label = QHBoxLayout()
        layout_footer_logo = QHBoxLayout()

        container_codigo = QVBoxLayout()
        container_codigo.addWidget(self.label_codigo)
        container_codigo.addWidget(self.campo_codigo)

        container_descricao_prod = QVBoxLayout()
        container_descricao_prod.addWidget(self.label_descricao_prod)
        container_descricao_prod.addWidget(self.campo_descricao_prod)

        container_contem_descricao_prod = QVBoxLayout()
        container_contem_descricao_prod.addWidget(self.label_contem_descricao_prod)
        container_contem_descricao_prod.addWidget(self.campo_contem_descricao_prod)

        container_op = QVBoxLayout()
        container_op.addWidget(self.label_OP)
        container_op.addWidget(self.campo_OP)

        container_qp = QVBoxLayout()
        container_qp.addWidget(self.label_qp)
        container_qp.addWidget(self.campo_qp)

        container_data_ini = QVBoxLayout()
        container_data_ini.addWidget(self.label_data_inicio)
        container_data_ini.addWidget(self.campo_data_inicio)

        container_data_fim = QVBoxLayout()
        container_data_fim.addWidget(self.label_data_fim)
        container_data_fim.addWidget(self.campo_data_fim)

        container_observacao = QVBoxLayout()
        container_observacao.addWidget(self.label_campo_observacao)
        container_observacao.addWidget(self.campo_observacao)

        layout_campos_01.addLayout(container_codigo)
        layout_campos_01.addLayout(container_descricao_prod)
        layout_campos_01.addLayout(container_contem_descricao_prod)
        layout_campos_01.addLayout(container_op)
        layout_campos_01.addLayout(container_qp)
        layout_campos_01.addLayout(container_observacao)
        layout_campos_02.addLayout(container_data_ini)
        layout_campos_02.addLayout(container_data_fim)
        layout_campos_01.addStretch()
        layout_campos_02.addStretch()

        self.layout_buttons.addWidget(self.btn_consultar)
        self.layout_buttons.addWidget(self.btn_consultar_estrutura)
        self.layout_buttons.addWidget(self.btn_onde_e_usado)
        self.layout_buttons.addWidget(self.btn_saldo_estoque)
        self.layout_buttons.addWidget(self.btn_nova_janela)
        self.layout_buttons.addWidget(self.btn_limpar)
        self.layout_buttons.addWidget(self.btn_abrir_desenho)
        self.layout_buttons.addWidget(self.btn_exportar_excel)
        self.layout_buttons.addWidget(self.btn_abrir_compras)
        self.layout_buttons.addWidget(self.btn_abrir_engenharia)
        self.layout_buttons.addWidget(self.btn_fechar)
        self.layout_buttons.addStretch()

        self.layout_footer_label.addStretch(1)
        self.layout_footer_label.addWidget(self.label_line_number)
        self.layout_footer_label.addStretch(1)

        layout_footer_logo.addWidget(self.logo_label)

        layout.addLayout(layout_campos_01)
        layout.addLayout(layout_campos_02)
        layout.addLayout(self.layout_buttons)
        layout.addWidget(self.tree)
        layout.addLayout(self.layout_footer_label)
        layout.addLayout(layout_footer_logo)
        self.setLayout(layout)

    def fechar_guia(self, index):
        if index >= 0:
            try:
                codigo_guia_fechada = self.tabWidget.tabText(index)
                self.guias_abertas.remove(codigo_guia_fechada)

            # Por ter duas listas de controle de abas abertas, 'guias_abertas = []' e 'guias_abertas_onde_usado = []',
            # ao fechar uma guia ocorre uma exceção (ValueError) se o código não for encontrado em uma das listas.
            # Utilize try/except para contornar esse problema.
            except ValueError:
                codigo_guia_fechada = self.tabWidget.tabText(index).split(' - ')[1]
                try:
                    self.guias_abertas_onde_usado.remove(codigo_guia_fechada)
                except ValueError:
                    self.guias_abertas_saldo.remove(codigo_guia_fechada)

            finally:
                self.tabWidget.removeTab(index)

                if not self.existe_guias_abertas():
                    # Se não houver mais guias abertas, remova a guia do layout principal
                    self.tabWidget.setVisible(False)
                    self.guia_fechada.emit()

    def existe_guias_abertas(self):
        return self.tabWidget.count() > 0

    def showContextMenu(self, position, table):
        indexes = table.selectedIndexes()
        if indexes:
            # Obtém o índice do item clicado
            index = table.indexAt(position)
            if not index.isValid():
                return

            # Seleciona a linha inteira
            table.selectRow(index.row())

            menu = QMenu()

            context_menu_abrir_desenho = QAction('Abrir desenho', self)
            context_menu_abrir_desenho.triggered.connect(lambda: self.abrir_desenho(table))

            context_menu_consultar_estrutura = QAction('Consultar estrutura', self)
            context_menu_consultar_estrutura.triggered.connect(lambda: self.executar_consulta_estrutura(table))

            context_menu_consultar_onde_usado = QAction('Onde é usado?', self)
            context_menu_consultar_onde_usado.triggered.connect(lambda: self.executar_consulta_onde_usado(table))

            context_menu_saldo_estoque = QAction('Saldo em estoque', self)
            context_menu_saldo_estoque.triggered.connect(lambda: self.executar_saldo_em_estoque(table))

            context_menu_nova_janela = QAction('Nova janela', self)
            context_menu_nova_janela.triggered.connect(lambda: self.abrir_nova_janela())

            menu.addAction(context_menu_abrir_desenho)
            menu.addAction(context_menu_consultar_estrutura)
            menu.addAction(context_menu_consultar_onde_usado)
            menu.addAction(context_menu_saldo_estoque)
            menu.addAction(context_menu_nova_janela)

            menu.exec_(table.viewport().mapToGlobal(position))

    def limpar_campos(self):
        self.campo_codigo.clear()
        self.campo_qp.clear()
        self.campo_OP.clear()
        self.campo_descricao_prod.clear()
        self.campo_contem_descricao_prod.clear()
        self.campo_observacao.clear()
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)
        self.label_line_number.hide()

    def abrir_desenho(self, table):
        item_selecionado = table.currentItem()
        header = table.horizontalHeader()
        codigo_col = None
        codigo = None

        for col in range(header.count()):
            header_text = table.horizontalHeaderItem(col).text()
            if header_text == 'Código':
                codigo_col = col

            if codigo_col is not None:
                codigo = table.item(item_selecionado.row(), codigo_col).text()

        if item_selecionado:
            pdf_path = os.path.join(r"\\192.175.175.4\dados\EMPRESA\PROJETOS\PDF-OFICIAL", f"{codigo}.PDF")
            pdf_path = os.path.normpath(pdf_path)

            if os.path.exists(pdf_path):
                QCoreApplication.processEvents()
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            else:
                mensagem = f"Desenho não encontrado!\n\n:-("
                QMessageBox.information(self, f"{codigo}", mensagem)

    def abrir_modulo_engenharia(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'engenharia_model.pyw')
        self.process.start("python", [script_path])

    def abrir_modulo_compras(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'compras_model.pyw')
        self.process.start("python", [script_path])

    def abrir_nova_janela(self):
        if not self.nova_janela or not self.nova_janela.isVisible():
            self.nova_janela = PcpApp()
            self.nova_janela.setGeometry(self.x() + 50, self.y() + 50, self.width(), self.height())
            self.nova_janela.show()

    def add_today_button(self, date_edit):
        calendar = date_edit.calendarWidget()
        calendar.setGeometry(10, 10, 600, 400)
        btn_today = QPushButton("Hoje", calendar)
        largura = 50
        altura = 20
        btn_today.setGeometry(20, 5, largura, altura)
        btn_today.clicked.connect(lambda: date_edit.setDate(QDate.currentDate()))

    def add_clear_button(self, line_edit):
        clear_icon = self.style().standardIcon(QStyle.SP_LineEditClearButton)
        pixmap = clear_icon.pixmap(40, 40)  # Redimensionar o ícone para 20x20 pixels
        larger_clear_icon = QIcon(pixmap)
        clear_action = QAction(larger_clear_icon, "Clear", line_edit)
        clear_action.triggered.connect(line_edit.clear)
        line_edit.addAction(clear_action, QLineEdit.TrailingPosition)

    def setup_mssql(self):
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

    def exportar_excel(self):
        desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')

        now = datetime.now()
        default_filename = f'PCP-report_{now.today().strftime('%Y-%m-%d_%H%M%S')}.xlsx'

        file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar como', os.path.join(desktop_path, default_filename),
                                                   'Arquivos Excel (*.xlsx);;Todos os arquivos (*)')

        if file_path:
            data = self.obter_dados_tabela()
            column_headers = [self.tree.horizontalHeaderItem(i).text() for i in range(self.tree.columnCount())]
            df = pd.DataFrame(data, columns=column_headers)

            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Dados', index=False)

            workbook = writer.book
            worksheet = writer.sheets['Dados']

            for i, col in enumerate(df.columns):
                max_len = df[col].astype(str).map(len).max()
                worksheet.set_column(i, i, max_len + 2)

            writer.close()

            os.startfile(file_path)

    def obter_dados_tabela(self):
        # Obter os dados da tabela
        data = []
        for i in range(self.tree.rowCount()):
            row_data = []
            for j in range(self.tree.columnCount()):
                item = self.tree.item(i, j)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            data.append(row_data)
        return data

    def configurar_tabela(self, dataframe):
        self.tree.setColumnCount(len(dataframe.columns))
        self.tree.setHorizontalHeaderLabels(dataframe.columns)
        self.tree.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tree.setSelectionBehavior(QTableWidget.SelectRows)
        self.tree.setSelectionMode(QTableWidget.SingleSelection)
        self.tree.itemDoubleClicked.connect(self.copiar_linha)
        self.tree.setFont(QFont(self.fonte_tabela, self.tamanho_fonte_tabela))
        self.tree.verticalHeader().setDefaultSectionSize(self.altura_linha)
        self.tree.horizontalHeader().sectionClicked.connect(self.ordenar_tabela)
        self.tree.horizontalHeader().setStretchLastSection(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(lambda pos: self.showContextMenu(pos, self.tree))

    def copiar_linha(self, item):
        if item is not None:
            valor_campo = item.text()
            pyperclip.copy(str(valor_campo))

    def ordenar_tabela(self, logical_index):
        # Obter o índice real da coluna (considerando a ordem de classificação)
        index = self.tree.horizontalHeader().sortIndicatorOrder()

        # Definir a ordem de classificação
        order = Qt.AscendingOrder if index == 0 else Qt.DescendingOrder

        # Ordenar a tabela pela coluna clicada
        self.tree.sortItems(logical_index, order)

    def controle_campos_formulario(self, status):
        self.campo_codigo.setEnabled(status)
        self.campo_qp.setEnabled(status)
        self.campo_OP.setEnabled(status)
        self.campo_observacao.setEnabled(status)
        self.campo_data_inicio.setEnabled(status)
        self.campo_data_fim.setEnabled(status)
        self.btn_consultar.setEnabled(status)
        self.btn_exportar_excel.setEnabled(status)
        self.btn_abrir_desenho.setEnabled(status)
        self.btn_onde_e_usado.setEnabled(status)
        self.btn_saldo_estoque.setEnabled(status)
        self.btn_consultar_estrutura.setEnabled(status)

    def query_consulta_ordem_producao(self):

        numero_qp = self.campo_qp.text().upper().strip()
        numero_op = self.campo_OP.text().upper().strip()
        codigo_produto = self.campo_codigo.text().upper().strip()
        descricao_produto = self.campo_descricao_prod.text().upper().strip()
        contem_descricao = self.campo_contem_descricao_prod.text().upper().strip()
        observacao = self.campo_observacao.text().upper().strip()

        if validar_campos(codigo_produto, numero_qp, numero_op):
            self.btn_consultar.setEnabled(True)
            return

        numero_qp = numero_qp.zfill(6) if numero_qp != '' else numero_qp

        palavras_contem_descricao = contem_descricao.split('*')
        clausulas_contem_descricao = " AND ".join(
            [f"prod.B1_DESC LIKE '%{palavra}%'" for palavra in palavras_contem_descricao])
        data_inicio_formatada = self.campo_data_inicio.date().toString("yyyyMMdd")
        data_fim_formatada = self.campo_data_fim.date().toString("yyyyMMdd")

        filtro_data = f"AND C2_EMISSAO >= '{data_inicio_formatada}' AND C2_EMISSAO <= '{data_fim_formatada}'" if data_fim_formatada != '' and data_fim_formatada != '' else ''

        query = f"""
            SELECT 
                C2_ZZNUMQP AS "QP", 
                C2_NUM AS "OP", 
                C2_ITEM AS "Item", 
                C2_SEQUEN AS "Seq.",
                C2_PRODUTO AS "Código", 
                B1_DESC AS "Descrição", 
                C2_QUANT AS "Quant.", 
                C2_UM AS "UM", 
                C2_EMISSAO AS "Emissão", 
                C2_DATPRF AS "Prev. Entrega",
                C2_DATRF AS "Fechamento", 
                C2_OBS AS "Observação",
                C2_QUJE AS "Quant. Produzida", 
                C2_AGLUT AS "Aglutinada?",
                users.USR_NOME AS "Aberto por:" 
            FROM 
                {database}.dbo.SC2010 op
            LEFT JOIN 
                SB1010 prod ON C2_PRODUTO = B1_COD
            LEFT JOIN 
                {database}.dbo.SYS_USR users
            ON 
                users.USR_CNLOGON = op.C2_XMAQUIN 
                AND users.D_E_L_E_T_ <> '*'
                AND users.USR_ID = (
                    SELECT MAX(users.USR_ID) 
                    FROM {database}.dbo.SYS_USR users
                    WHERE users.USR_CNLOGON = op.C2_XMAQUIN 
                AND users.D_E_L_E_T_ <> '*')
            WHERE 
                C2_ZZNUMQP LIKE '%{numero_qp}'
                AND C2_PRODUTO LIKE '{codigo_produto}%'
                AND prod.B1_DESC LIKE '{descricao_produto}%'
                AND {clausulas_contem_descricao}
                AND C2_OBS LIKE '%{observacao}%'
                AND C2_NUM LIKE '{numero_op}%' {filtro_data}
                AND op.D_E_L_E_T_ <> '*'
            ORDER BY op.R_E_C_N_O_ DESC;
        """
        return query

    def configurar_tabela_tooltips(self, dataframe):
        # Mapa de tooltips correspondentes às colunas da consulta SQL
        tooltip_map = {
            "Status OP": "VERMELHO -> OP ABERTA\nVERDE -> OP FINALIZADA"
        }

        # Obtenha os cabeçalhos das colunas do dataframe
        headers = dataframe.columns

        # Adicione os cabeçalhos e os tooltips
        for i, header in enumerate(headers):
            item = QTableWidgetItem(header)
            tooltip = tooltip_map.get(header)
            item.setToolTip(tooltip)
            self.tree.setHorizontalHeaderItem(i, item)

    def executar_consulta(self):
        query_consulta_op = self.query_consulta_ordem_producao()
        query_contagem_linhas = numero_linhas_consulta(query_consulta_op)

        self.label_line_number.hide()
        self.controle_campos_formulario(False)

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe_line_number = pd.read_sql(query_contagem_linhas, self.engine)
            line_number = dataframe_line_number.iloc[0, 0]

            if line_number >= 1:

                if line_number > 1:
                    message = f"Foram encontrados {line_number} resultados!"
                else:
                    message = f"Foi encontrado {line_number} resultado!"

                self.label_line_number.setText(f"{message}")
                self.label_line_number.show()

            else:
                exibir_mensagem("EUREKA® PCP", 'Nada encontrado!', "info")
                self.controle_campos_formulario(True)
                return

            dataframe = pd.read_sql(query_consulta_op, self.engine)
            dataframe.insert(0, 'Status OP', '')
            dataframe[''] = ''

            self.configurar_tabela(dataframe)
            self.configurar_tabela_tooltips(dataframe)

            self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
            self.tree.setRowCount(0)

            # Construir caminhos relativos
            script_dir = os.path.dirname(os.path.abspath(__file__))
            open_icon_path = os.path.join(script_dir, '..', 'resources', 'images', 'red.png')
            closed_icon_path = os.path.join(script_dir, '..', 'resources', 'images', 'green.png')

            open_icon = QIcon(open_icon_path)
            closed_icon = QIcon(closed_icon_path)

            for i, row in dataframe.iterrows():
                if self.interromper_consulta_sql:
                    break

                self.tree.setSortingEnabled(False)
                self.tree.insertRow(i)
                for j, value in enumerate(row):
                    if value is not None:
                        if j == 0:
                            item = QTableWidgetItem()
                            if row['Fechamento'].strip() == '':
                                item.setIcon(open_icon)
                            else:
                                item.setIcon(closed_icon)
                            item.setTextAlignment(Qt.AlignCenter)
                        else:
                            if j == 14 and value == 'S':
                                value = 'Sim'
                            elif j == 14 and value != 'S':
                                value = 'Não'
                            if 9 <= j <= 11 and not value.isspace():
                                data_obj = datetime.strptime(value, "%Y%m%d")
                                value = data_obj.strftime("%d/%m/%Y")

                            item = QTableWidgetItem(str(value).strip())

                            if j not in (6, 12, 15):
                                item.setTextAlignment(Qt.AlignCenter)

                    else:
                        item = QTableWidgetItem('')

                    self.tree.setItem(i, j, item)

                # QCoreApplication.processEvents()

            self.tree.setSortingEnabled(True)
            self.controle_campos_formulario(True)

        except Exception as ex:
            exibir_mensagem('Erro ao consultar tabela', f'Erro: {str(ex)}', 'error')

        finally:
            # Fecha a conexão com o banco de dados se estiver aberta
            if hasattr(self, 'engine'):
                self.engine.dispose()
                self.engine = None
            self.interromper_consulta_sql = False

    def fechar_janela(self):
        self.close()

    def executar_consulta_estrutura(self, table):
        item_selecionado = table.currentItem()
        header = table.horizontalHeader()
        codigo_col, descricao_col = None, None
        codigo = None
        descricao = None

        for col in range(header.count()):
            header_text = table.horizontalHeaderItem(col).text()
            if header_text == 'Código':
                codigo_col = col
            elif header_text == 'Descrição':
                descricao_col = col

            if codigo_col is not None and descricao_col is not None:
                codigo = table.item(item_selecionado.row(), codigo_col).text()
                descricao = table.item(item_selecionado.row(), descricao_col).text()

            if codigo not in self.guias_abertas and codigo is not None:
                select_query_estrutura = f"""
                    SELECT struct.G1_COMP AS "Código", prod.B1_DESC AS "Descrição", struct.G1_QUANT AS "QTD.", 
                    struct.G1_XUM AS "UNID.", struct.G1_REVFIM AS "REVISÃO", 
                    struct.G1_INI AS "INSERIDO EM:"
                    FROM {database}.dbo.SG1010 struct
                    INNER JOIN {database}.dbo.SB1010 prod
                    ON struct.G1_COMP = prod.B1_COD AND prod.D_E_L_E_T_ <> '*'
                    WHERE G1_COD = '{codigo}' 
                    AND G1_REVFIM <> 'ZZZ' AND struct.D_E_L_E_T_ <> '*' 
                    AND G1_REVFIM = (SELECT MAX(G1_REVFIM) FROM {database}.dbo.SG1010 WHERE G1_COD = '{codigo}' 
                    AND G1_REVFIM <> 'ZZZ' AND D_E_L_E_T_ <> '*')
                    ORDER BY B1_DESC ASC;
                """

                try:
                    conn_estrutura = pyodbc.connect(
                        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')

                    cursor_estrutura = conn_estrutura.cursor()
                    resultado = cursor_estrutura.execute(select_query_estrutura)

                    nova_guia_estrutura = QWidget()
                    layout_nova_guia_estrutura = QVBoxLayout()
                    layout_cabecalho = QHBoxLayout()

                    tree_estrutura = QTableWidget(nova_guia_estrutura)

                    tree_estrutura.setContextMenuPolicy(Qt.CustomContextMenu)
                    tree_estrutura.customContextMenuRequested.connect(
                        lambda pos: self.showContextMenu(pos, tree_estrutura))

                    tree_estrutura.setColumnCount(len(cursor_estrutura.description))
                    tree_estrutura.setHorizontalHeaderLabels([desc[0] for desc in cursor_estrutura.description])

                    # Tornar a tabela somente leitura
                    tree_estrutura.setEditTriggers(QTableWidget.NoEditTriggers)

                    # Configurar a fonte da tabela
                    fonte_tabela = QFont("Segoe UI", 8)  # Substitua por sua fonte desejada e tamanho
                    tree_estrutura.setFont(fonte_tabela)

                    # Ajustar a altura das linhas
                    altura_linha = 22  # Substitua pelo valor desejado
                    tree_estrutura.verticalHeader().setDefaultSectionSize(altura_linha)

                    for i, row in enumerate(resultado.fetchall()):
                        tree_estrutura.insertRow(i)
                        for j, value in enumerate(row):
                            if j == 2:
                                valor_formatado = "{:.2f}".format(float(value))
                            elif j == 5:
                                data_obj = datetime.strptime(value, "%Y%m%d")
                                valor_formatado = data_obj.strftime("%d/%m/%Y")
                            else:
                                valor_formatado = str(value).strip()

                            item = QTableWidgetItem(valor_formatado)
                            item.setForeground(QColor("#EEEEEE"))  # Definir cor do texto da coluna quantidade

                            if j != 0 and j != 1:
                                item.setTextAlignment(Qt.AlignCenter)

                            tree_estrutura.setItem(i, j, item)

                    tree_estrutura.setSortingEnabled(True)

                    # Ajustar automaticamente a largura da coluna "Descrição"
                    ajustar_largura_coluna_descricao(tree_estrutura)

                    layout_cabecalho.addWidget(QLabel(f"CONSULTA DE ESTRUTURA\n\n{codigo} - {descricao}"),
                                               alignment=Qt.AlignLeft)
                    layout_nova_guia_estrutura.addLayout(layout_cabecalho)
                    layout_nova_guia_estrutura.addWidget(tree_estrutura)
                    nova_guia_estrutura.setLayout(layout_nova_guia_estrutura)

                    nova_guia_estrutura.setStyleSheet("""                                           
                        * {
                            background-color: #262626;
                        }

                        QLabel {
                            color: #A7A6A6;
                            font-size: 18px;
                            font-weight: bold;
                        }

                        QTableWidget {
                            border: 1px solid #000000;
                        }

                        QTableWidget QHeaderView::section {
                            background-color: #575a5f;
                            color: #fff;
                            padding: 5px;
                            height: 18px;
                        }

                        QTableWidget QHeaderView::section:horizontal {
                            border-top: 1px solid #333;
                        }

                        QTableWidget::item:selected {
                            background-color: #0066ff;
                            color: #fff;
                            font-weight: bold;
                        }        
                    """)

                    if not self.existe_guias_abertas():
                        # Se não houver guias abertas, adicione a guia ao layout principal
                        self.layout().addWidget(self.tabWidget)
                        self.tabWidget.setVisible(True)

                    self.tabWidget.addTab(nova_guia_estrutura, f"{codigo}")

                except pyodbc.Error as ex:
                    print(f"Falha na consulta de estrutura. Erro: {str(ex)}")

                finally:
                    self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(nova_guia_estrutura))
                    self.guias_abertas.append(codigo)
                    conn_estrutura.close()

    def executar_consulta_onde_usado(self, table):
        item_selecionado = table.currentItem()
        codigo, descricao = None, None

        if item_selecionado:
            header = table.horizontalHeader()
            codigo_col = None
            descricao_col = None

            for col in range(header.count()):
                header_text = table.horizontalHeaderItem(col).text()
                if header_text == 'Código':
                    codigo_col = col
                elif header_text == 'Descrição':
                    descricao_col = col

            if codigo_col is not None and descricao_col is not None:
                codigo = table.item(item_selecionado.row(), codigo_col).text()
                descricao = table.item(item_selecionado.row(), descricao_col).text()

            if codigo not in self.guias_abertas_onde_usado:
                query_onde_usado = f"""
                    SELECT 
                        STRUT.G1_COD AS "Código", 
                        PROD.B1_DESC "Descrição"
                    FROM 
                        {database}.dbo.SG1010 STRUT 
                    INNER JOIN 
                        {database}.dbo.SB1010 PROD 
                    ON 
                        G1_COD = B1_COD 
                    WHERE G1_COMP = '{codigo}' 
                        AND STRUT.G1_REVFIM <> 'ZZZ' 
                        AND STRUT.D_E_L_E_T_ <> '*'
                    ORDER BY B1_DESC ASC;
                """
                self.guias_abertas_onde_usado.append(codigo)
                try:
                    conn = pyodbc.connect(
                        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')

                    cursor_tabela = conn.cursor()
                    cursor_tabela.execute(query_onde_usado)

                    nova_guia_estrutura = QWidget()
                    layout_nova_guia_estrutura = QVBoxLayout()
                    layout_cabecalho = QHBoxLayout()

                    tabela_onde_usado = QTableWidget(nova_guia_estrutura)

                    tabela_onde_usado.setContextMenuPolicy(Qt.CustomContextMenu)
                    tabela_onde_usado.customContextMenuRequested.connect(
                        lambda pos: self.showContextMenu(pos, tabela_onde_usado))

                    tabela_onde_usado.setColumnCount(len(cursor_tabela.description))
                    tabela_onde_usado.setHorizontalHeaderLabels([desc[0] for desc in cursor_tabela.description])

                    # Tornar a tabela somente leitura
                    tabela_onde_usado.setEditTriggers(QTableWidget.NoEditTriggers)

                    # Configurar a fonte da tabela
                    fonte_tabela = QFont("Segoe UI", 8)  # Substitua por sua fonte desejada e tamanho
                    tabela_onde_usado.setFont(fonte_tabela)

                    # Ajustar a altura das linhas
                    altura_linha = 22  # Substitua pelo valor desejado
                    tabela_onde_usado.verticalHeader().setDefaultSectionSize(altura_linha)

                    for i, row in enumerate(cursor_tabela.fetchall()):
                        tabela_onde_usado.insertRow(i)
                        for j, value in enumerate(row):
                            valor_formatado = str(value).strip()

                            item = QTableWidgetItem(valor_formatado)
                            tabela_onde_usado.setItem(i, j, item)

                    tabela_onde_usado.setSortingEnabled(True)

                    # Ajustar automaticamente a largura da coluna "Descrição"
                    ajustar_largura_coluna_descricao(tabela_onde_usado)

                    layout_cabecalho.addWidget(QLabel(f'Onde é usado?\n\n{codigo} - {descricao}'),
                                               alignment=Qt.AlignLeft)
                    layout_nova_guia_estrutura.addLayout(layout_cabecalho)
                    layout_nova_guia_estrutura.addWidget(tabela_onde_usado)
                    nova_guia_estrutura.setLayout(layout_nova_guia_estrutura)

                    nova_guia_estrutura.setStyleSheet("""                                           
                        * {
                            background-color: #262626;
                        }

                        QLabel {
                            color: #A7A6A6;
                            font-size: 18px;
                            font-weight: bold;
                        }

                        QTableWidget {
                            border: 1px solid #000000;
                        }

                        QTableWidget QHeaderView::section {
                            background-color: #575a5f;
                            color: #fff;
                            padding: 5px;
                            height: 18px;
                        }

                        QTableWidget QHeaderView::section:horizontal {
                            border-top: 1px solid #333;
                        }

                        QTableWidget::item:selected {
                            background-color: #0066ff;
                            color: #fff;
                            font-weight: bold;
                        }        
                    """)

                    if not self.existe_guias_abertas():
                        # Se não houver guias abertas, adicione a guia ao layout principal
                        self.layout().addWidget(self.tabWidget)
                        self.tabWidget.setVisible(True)

                    self.tabWidget.addTab(nova_guia_estrutura, f"Onde é usado? - {codigo}")
                    tabela_onde_usado.itemDoubleClicked.connect(self.copiar_linha)

                except pyodbc.Error as ex:
                    print(f"Falha na consulta de estrutura. Erro: {str(ex)}")

                finally:
                    self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(nova_guia_estrutura))
                    conn.close()

    def executar_saldo_em_estoque(self, table):
        item_selecionado = table.currentItem()
        codigo, descricao = None, None

        if item_selecionado:
            header = table.horizontalHeader()
            codigo_col = None
            descricao_col = None

            for col in range(header.count()):
                header_text = table.horizontalHeaderItem(col).text()
                if header_text == 'Código':
                    codigo_col = col
                elif header_text == 'Descrição':
                    descricao_col = col

            if codigo_col is not None and descricao_col is not None:
                codigo = table.item(item_selecionado.row(), codigo_col).text()
                descricao = table.item(item_selecionado.row(), descricao_col).text()

            if codigo not in self.guias_abertas_saldo:
                query_saldo = f"""
                    SELECT 
                        B2_QATU AS "Saldo Atual",
                        EST.B2_QATU - EST.B2_QEMP AS "Qtd. Disponível",
                        B2_QEMP AS "Qtd. Empenhada",
                        B2_SALPEDI AS "Qtd. Prev. Entrada",
                        PROD.B1_UM AS "Unid. Med.",
                        B2_VATU1 AS "Valor Saldo Atual (R$)", 
                        B2_CM1 AS "Custo Unit. (R$)",
                        B2_DMOV AS "Dt. Últ. Mov.", 
                        B2_HMOV AS "Hora Últ. Mov.",
                        B2_DINVENT AS "Dt. Últ. Inventário"
                    FROM 
                        {database}.dbo.SB2010 EST
                    INNER JOIN
                        {database}.dbo.SB1010 PROD
                    ON
                        PROD.B1_COD = EST.B2_COD 
                    WHERE 
                        B2_COD = '{codigo}';
                """
                self.guias_abertas_saldo.append(codigo)
                try:
                    conn_saldo = pyodbc.connect(
                        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')

                    cursor_saldo_estoque = conn_saldo.cursor()
                    cursor_saldo_estoque.execute(query_saldo)

                    nova_guia_saldo = QWidget()
                    layout_nova_guia_saldo = QVBoxLayout()
                    layout_cabecalho = QHBoxLayout()

                    tabela_saldo_estoque = QTableWidget(nova_guia_saldo)

                    tabela_saldo_estoque.setColumnCount(len(cursor_saldo_estoque.description))
                    tabela_saldo_estoque.setHorizontalHeaderLabels(
                        [desc[0] for desc in cursor_saldo_estoque.description])

                    tabela_saldo_estoque.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

                    # Tornar a tabela somente leitura
                    tabela_saldo_estoque.setEditTriggers(QTableWidget.NoEditTriggers)

                    # Configurar a fonte da tabela1
                    fonte_tabela = QFont("Segoe UI", 10)  # Substitua por sua fonte desejada e tamanho
                    tabela_saldo_estoque.setFont(fonte_tabela)

                    # Ajustar a altura das linhas
                    altura_linha = 20  # Substitua pelo valor desejado
                    tabela_saldo_estoque.verticalHeader().setDefaultSectionSize(altura_linha)

                    for i, row in enumerate(cursor_saldo_estoque.fetchall()):
                        tabela_saldo_estoque.insertRow(i)
                        for j, value in enumerate(row):

                            if j in (0, 1, 2, 3, 5, 6):
                                value = locale.format_string("%.2f", value, grouping=True)

                            elif j in (7, 9) and not value.isspace():
                                data_obj = datetime.strptime(value, "%Y%m%d")
                                value = data_obj.strftime("%d/%m/%Y")

                            valor_formatado = str(value).strip()
                            item = QTableWidgetItem(valor_formatado)
                            item.setTextAlignment(Qt.AlignCenter)
                            tabela_saldo_estoque.setItem(i, j, item)

                    tabela_saldo_estoque.setSortingEnabled(True)

                    layout_cabecalho.addWidget(QLabel(f'Saldos em Estoque\n\n{codigo} - {descricao}'),
                                               alignment=Qt.AlignLeft)
                    layout_nova_guia_saldo.addLayout(layout_cabecalho)
                    layout_nova_guia_saldo.addWidget(tabela_saldo_estoque)
                    nova_guia_saldo.setLayout(layout_nova_guia_saldo)

                    nova_guia_saldo.setStyleSheet("""                                           
                        * {
                            background-color: #262626;
                        }

                        QLabel {
                            color: #A7A6A6;
                            font-size: 18px;
                            font-weight: bold;
                        }

                        QTableWidget {
                            border: 1px solid #000000;
                        }

                        QTableWidget QHeaderView::section {
                            background-color: #575a5f;
                            color: #fff;
                            padding: 5px;
                            height: 18px;
                        }

                        QTableWidget QHeaderView::section:horizontal {
                            border-top: 1px solid #333;
                        }

                        QTableWidget::item:selected {
                            background-color: #0066ff;
                            color: #fff;
                            font-weight: bold;
                        }        
                    """)

                    if not self.existe_guias_abertas():
                        # Se não houver guias abertas, adicione a guia ao layout principal
                        self.layout().addWidget(self.tabWidget)
                        self.tabWidget.setVisible(True)

                    self.tabWidget.addTab(nova_guia_saldo, f"Saldos em Estoque - {codigo}")
                    tabela_saldo_estoque.itemDoubleClicked.connect(self.copiar_linha)

                except pyodbc.Error as ex:
                    print(f"Falha na consulta de estrutura. Erro: {str(ex)}")

                finally:
                    self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(nova_guia_saldo))
                    conn_saldo.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PcpApp()
    username, password, database, server = PcpApp().setup_mssql()
    driver = '{SQL Server}'

    window.showMaximized()

    sys.exit(app.exec_())
