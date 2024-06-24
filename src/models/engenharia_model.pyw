import sys

from PyQt5.QtSql import QSqlDatabase, QSqlQueryModel
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, \
    QTableWidgetItem, QHeaderView, QSizePolicy, QSpacerItem, QMessageBox, QFileDialog, QTabWidget, \
    QItemDelegate, QAbstractItemView, QCheckBox, QMenu, QAction, QComboBox, QStyle, QDialog, QTableView
from PyQt5.QtGui import QFont, QIcon, QDesktopServices, QColor
from PyQt5.QtCore import Qt, QUrl, QCoreApplication, pyqtSignal, QProcess, pyqtSlot
import pyodbc
import pyperclip
import os
import time
import pandas as pd
import ctypes
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import locale
from sqlalchemy import create_engine


def abrir_tabela_pesos():
    os.startfile(r'\\192.175.175.4\f\INTEGRANTES\ELIEZER\DOCUMENTOS_UTEIS\TABELA_PESO.xlsx')


def setup_mssql():
    caminho_do_arquivo = (r"\\192.175.175.4\f\INTEGRANTES\ELIEZER\PROJETO SOLIDWORKS "
                          r"TOTVS\libs-python\user-password-mssql\USER_PASSWORD_MSSQL_PROD.txt")
    try:
        with open(caminho_do_arquivo, 'r') as arquivo:
            string_lida = arquivo.read()
            username_txt, password_txt, database_txt, server_txt = string_lida.split(';')
            return username_txt, password_txt, database_txt, server_txt

    except FileNotFoundError:
        ctypes.windll.user32.MessageBoxW(0,
                                         f"Erro ao ler credenciais de acesso ao banco de dados MSSQL.\n\nBase de "
                                         f"dados ERP TOTVS PROTHEUS.\n\nPor favor, informe ao desenvolvedor/TI "
                                         f"sobre o erro exibido.\n\nTenha um bom dia! ツ",
                                         "CADASTRO DE ESTRUTURA - TOTVS®", 16 | 0)
        sys.exit()

    except Exception as ex:
        ctypes.windll.user32.MessageBoxW(0, f"Ocorreu um erro ao ler o arquivo: {ex}", "CADASTRO DE ESTRUTURA - TOTVS®",
                                         16 | 0)
        sys.exit()


def copiar_linha(item):
    # Verificar se um item foi clicado
    if item is not None:
        valor_campo = item.text()
        pyperclip.copy(str(valor_campo))


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


def alterar_quantidade_estrutura(codigo_pai, codigo_filho, quantidade):
    query_alterar_quantidade_estrutura = f"""
            UPDATE {database}.dbo.SG1010 
            SET G1_QUANT = {quantidade} 
            WHERE G1_COD = '{codigo_pai}' 
            AND G1_COMP = '{codigo_filho}'
            AND G1_REVFIM <> 'ZZZ' AND D_E_L_E_T_ <> '*'
            AND G1_REVFIM = (SELECT MAX(G1_REVFIM) FROM {database}.dbo.SG1010 
            WHERE G1_COD = '{codigo_pai}' 
            AND G1_REVFIM <> 'ZZZ' 
            AND D_E_L_E_T_ <> '*');
        """
    try:
        with pyodbc.connect(
                f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}') as conn:
            cursor = conn.cursor()
            cursor.execute(query_alterar_quantidade_estrutura)
            conn.commit()

    except Exception as ex:
        ctypes.windll.user32.MessageBoxW(0, f"Falha na conexão com o TOTVS ou consulta. Erro: {str(ex)}",
                                         "Erro de execução", 16 | 0)


def handle_item_change(item, tree_estrutura, codigo_pai):
    if item.column() == 2:
        linha_selecionada = tree_estrutura.currentItem()

        codigo_filho = tree_estrutura.item(linha_selecionada.row(), 0).text()
        nova_quantidade = item.text()
        nova_quantidade = nova_quantidade.replace(',', '.')

        if nova_quantidade.replace('.', '', 1).isdigit():
            alterar_quantidade_estrutura(codigo_pai, codigo_filho, float(nova_quantidade))
        else:
            ctypes.windll.user32.MessageBoxW(
                0,
                "QUANTIDADE INVÁLIDA\n\nOs valores devem ser números, não nulos, sem espaços em branco e maiores "
                "que zero.\nPor favor, corrija tente novamente!",
                "SMARTPLIC®", 48 | 0)


def ajustar_largura_coluna_descricao(tree_widget):
    header = tree_widget.horizontalHeader()
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)


class EngenhariaApp(QWidget):
    # Adicione este sinal à classe
    guia_fechada = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.engine = None
        self.setWindowTitle("EUREKA® ENGENHARIA - v2.0")

        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

        self.nova_janela = None  # Adicione esta linha
        self.guias_abertas = []
        self.guias_abertas_onde_usado = []
        self.guias_abertas_saldo = []
        fonte = "Segoe UI"
        tamanho_fonte = 10

        self.altura_linha = 30
        self.tamanho_fonte_tabela = 10
        self.fonte_tabela = 'Segoe UI'

        self.interromper_consulta_sql = False
        self.tree = QTableWidget(self)
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)

        self.process = QProcess(self)

        self.tabWidget = QTabWidget(self)  # Adicione um QTabWidget ao layout principal
        self.tabWidget.setTabsClosable(True)  # Adicione essa linha para permitir o fechamento de guias
        self.tabWidget.tabCloseRequested.connect(self.fechar_guia)
        self.tabWidget.setVisible(False)  # Inicialmente, a guia está invisível

        self.combobox_armazem = QComboBox(self)
        self.combobox_armazem.setEditable(False)
        self.combobox_armazem.setObjectName('combobox-armazem')

        self.combobox_armazem.addItem("", None)

        armazens = {
            "01": "MATERIA PRIMA",
            "02": "PROD. INTERMEDIARIO",
            "03": "PROD. COMERCIAIS",
            "04": "PROD. ACABADOS",
            "05": "MAT.PRIMA IMP.INDIR.",
            "06": "PROD. ELETR.NACIONAL",
            "07": "PROD.ELETR.IMP.DIRET",
            "08": "SRV INDUSTRIALIZACAO",
            "09": "SRV TERCEIROS",
            "10": "PROD.COM.IMP.INDIR.",
            "11": "PROD.COM.IMP.DIRETO",
            "12": "MAT.PRIMA IMP.DIR.ME",
            "13": "E.P.I-MAT.SEGURANCA",
            "14": "PROD.ELETR.IMP.INDIR",
            "22": "ATIVOS",
            "60": "PROD-FERR CONSUMIVEI",
            "61": "EMBALAGENS",
            "70": "SERVICOS GERAIS",
            "71": "PRODUTOS AUTOMOTIVOS",
            "77": "OUTROS",
            "80": "SUCATAS",
            "85": "SERVICOS PRESTADOS",
            "96": "ARMAZ.NAO APLICAVEL",
            "97": "TRAT. SUPERFICIAL"
        }

        for key, value in armazens.items():
            self.combobox_armazem.addItem(key + ' - ' + value, key)

        self.campo_codigo = QLineEdit(self)
        self.campo_codigo.setFont(QFont(fonte, tamanho_fonte))
        self.add_clear_button(self.campo_codigo)

        self.campo_descricao = QLineEdit(self)
        self.campo_descricao.setFont(QFont(fonte, tamanho_fonte))
        self.add_clear_button(self.campo_descricao)

        self.campo_contem_descricao = QLineEdit(self)
        self.campo_contem_descricao.setFont(QFont(fonte, tamanho_fonte))
        self.add_clear_button(self.campo_contem_descricao)

        self.tipo_var = QLineEdit(self)
        self.tipo_var.setFont(QFont(fonte, tamanho_fonte))
        self.add_clear_button(self.tipo_var)

        self.um_var = QLineEdit(self)
        self.um_var.setFont(QFont(fonte, tamanho_fonte))
        self.add_clear_button(self.um_var)

        self.grupo_var = QLineEdit(self)
        self.grupo_var.setFont(QFont(fonte, tamanho_fonte))
        self.add_clear_button(self.grupo_var)

        self.btn_consultar = QPushButton("Pesquisar", self)
        self.btn_consultar.clicked.connect(self.executar_consulta)
        self.btn_consultar.setMinimumWidth(100)

        self.btn_abrir_pcp = QPushButton("PCP", self)
        self.btn_abrir_pcp.setObjectName("PCP")
        self.btn_abrir_pcp.clicked.connect(self.abrir_modulo_pcp)
        self.btn_abrir_pcp.setMinimumWidth(100)

        self.btn_abrir_compras = QPushButton("Compras", self)
        self.btn_abrir_compras.setObjectName("compras")
        self.btn_abrir_compras.clicked.connect(self.abrir_modulo_compras)
        self.btn_abrir_compras.setMinimumWidth(100)

        self.btn_consultar_estrutura = QPushButton("Consultar Estrutura", self)
        self.btn_consultar_estrutura.clicked.connect(lambda: self.executar_consulta_estrutura(self.tree))
        self.btn_consultar_estrutura.setMinimumWidth(150)
        self.btn_consultar_estrutura.setEnabled(False)

        self.btn_onde_e_usado = QPushButton("Onde é usado?", self)
        self.btn_onde_e_usado.clicked.connect(lambda: self.executar_consulta_onde_usado(self.tree))
        self.btn_onde_e_usado.setMinimumWidth(150)
        self.btn_onde_e_usado.setEnabled(False)

        self.btn_limpar = QPushButton("Limpar", self)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_limpar.setMinimumWidth(100)

        self.btn_nova_janela = QPushButton("Nova Janela", self)
        self.btn_nova_janela.clicked.connect(self.abrir_nova_janela)
        self.btn_nova_janela.setMinimumWidth(100)

        self.btn_abrir_desenho = QPushButton("Abrir Desenho", self)
        self.btn_abrir_desenho.clicked.connect(lambda: self.abrir_desenho(self.tree))
        self.btn_abrir_desenho.setMinimumWidth(100)

        self.btn_exportar_excel = QPushButton("Exportar Excel", self)
        self.btn_exportar_excel.clicked.connect(self.exportar_excel)
        self.btn_exportar_excel.setMinimumWidth(100)
        self.btn_exportar_excel.setEnabled(False)  # Desativar inicialmente

        self.btn_calculo_peso = QPushButton("Tabela de pesos", self)
        self.btn_calculo_peso.clicked.connect(abrir_tabela_pesos)
        self.btn_calculo_peso.setMinimumWidth(100)

        self.btn_fechar = QPushButton("Fechar", self)
        self.btn_fechar.clicked.connect(self.fechar_janela)
        self.btn_fechar.setMinimumWidth(100)

        # Conectar o evento returnPressed dos campos de entrada ao método executar_consulta
        self.campo_codigo.returnPressed.connect(self.executar_consulta)
        self.campo_descricao.returnPressed.connect(self.executar_consulta)
        self.campo_contem_descricao.returnPressed.connect(self.executar_consulta)
        self.tipo_var.returnPressed.connect(self.executar_consulta)
        self.um_var.returnPressed.connect(self.executar_consulta)
        self.grupo_var.returnPressed.connect(self.executar_consulta)

        layout = QVBoxLayout()
        layout_linha_01 = QHBoxLayout()
        layout_linha_02 = QHBoxLayout()
        layout_linha_03 = QHBoxLayout()

        layout_linha_01.addWidget(QLabel("Código:"))
        layout_linha_01.addWidget(self.campo_codigo)

        layout_linha_01.addWidget(QLabel("Descrição:"))
        layout_linha_01.addWidget(self.campo_descricao)

        layout_linha_01.addWidget(QLabel("Contém na Descrição:"))
        layout_linha_01.addWidget(self.campo_contem_descricao)

        layout_linha_02.addWidget(QLabel("Tipo:"))
        layout_linha_02.addWidget(self.tipo_var)

        layout_linha_02.addWidget(QLabel("Unid. Medida:"))
        layout_linha_02.addWidget(self.um_var)

        layout_linha_02.addWidget(QLabel("Armazém:"))
        layout_linha_02.addWidget(self.combobox_armazem)

        layout_linha_02.addWidget(QLabel("Grupo:"))
        layout_linha_02.addWidget(self.grupo_var)

        self.checkbox_bloqueado = QCheckBox("Bloqueado?", self)
        layout_linha_02.addWidget(self.checkbox_bloqueado)

        layout_linha_03.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout_linha_03.addWidget(self.btn_consultar)
        layout_linha_03.addWidget(self.btn_consultar_estrutura)
        layout_linha_03.addWidget(self.btn_onde_e_usado)
        layout_linha_03.addWidget(self.btn_limpar)
        layout_linha_03.addWidget(self.btn_nova_janela)
        layout_linha_03.addWidget(self.btn_abrir_desenho)
        layout_linha_03.addWidget(self.btn_exportar_excel)
        layout_linha_03.addWidget(self.btn_calculo_peso)
        layout_linha_03.addWidget(self.btn_abrir_pcp)
        layout_linha_03.addWidget(self.btn_abrir_compras)
        layout_linha_03.addWidget(self.btn_fechar)

        # Adicione um espaçador esticável para centralizar os botões
        layout_linha_03.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(layout_linha_01)
        layout.addLayout(layout_linha_02)
        layout.addLayout(layout_linha_03)

        layout.addWidget(self.tree)

        layout.addWidget(self.tabWidget)  # Adicione o QTabWidget ao layout principal

        self.setLayout(layout)

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
                        background-color: #EEEEEE;
                        border: 1px solid #262626;
                        padding: 5px;
                        border-radius: 8px;
                    }
                    
                    QDateEdit, QComboBox {
                        background-color: #EEEEEE;
                        border: 1px solid #262626;
                        padding: 5px 10px;
                        border-radius: 10px;
                        height: 20px;
                        font-size: 16px;
                    }
            
                    QDateEdit::drop-down, QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 30px;
                        border-left-width: 1px;
                        border-left-color: darkgray;
                        border-left-style: solid;
                        border-top-right-radius: 3px;
                        border-bottom-right-radius: 3px;
                    }
            
                    QDateEdit::down-arrow, QComboBox::down-arrow {
                        image: url(../resources/images/arrow.png);
                        width: 10px;
                        height: 10px;
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

                    QPushButton#PCP, QPushButton#compras {
                        background-color: #DC5F00;
                    }

                    QPushButton#compras {
                        background-color: #836FFF;
                    }

                    QPushButton:hover, QPushButton#PCP:hover, QPushButton#compras:hover {
                        background-color: #fff;
                        color: #0a79f8
                    }

                    QPushButton:pressed, QPushButton#PCP:pressed, QPushButton#compras:pressed {
                        background-color: #6703c5;
                        color: #fff;
                    }

                    QTableWidget {
                        border: 1px solid #000000;
                        background-color: #686D76;
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
                    }

                    QTableWidget::item:selected {
                        background-color: #000000;
                        color: #EEEEEE;
                        font-weight: bold;
                    }
                """)

    def abrir_modulo_pcp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'pcp_model.pyw')
        self.process.start("python", [script_path])

    def abrir_modulo_compras(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'compras_model.pyw')
        self.process.start("python", [script_path])

    def add_clear_button(self, line_edit):
        clear_icon = self.style().standardIcon(QStyle.SP_LineEditClearButton)

        line_edit_height = line_edit.height()
        pixmap = clear_icon.pixmap(line_edit_height - 4, line_edit_height - 4)
        larger_clear_icon = QIcon(pixmap)

        clear_action = QAction(larger_clear_icon, "Limpar", line_edit)
        clear_action.triggered.connect(line_edit.clear)
        line_edit.addAction(clear_action, QLineEdit.TrailingPosition)

    def exportar_excel(self):

        desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')

        now = datetime.now()
        default_filename = f'ENG-report_{now.today().strftime('%Y-%m-%d_%H%M%S')}.xlsx'

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
        self.tree.itemDoubleClicked.connect(copiar_linha)
        self.tree.setFont(QFont(self.fonte_tabela, self.tamanho_fonte_tabela))
        self.tree.verticalHeader().setDefaultSectionSize(self.altura_linha)
        self.tree.horizontalHeader().sectionClicked.connect(self.ordenar_tabela)
        self.tree.horizontalHeader().setStretchLastSection(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(lambda pos: self.showContextMenu(pos, self.tree))

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

    def configurar_tabela_tooltips(self, dataframe):
        tooltips = {
            "B1_COD": "Código do produto",
            "B1_DESC": "Descrição do produto",
            "B1_XDESC2": "Descrição completa do produto",
            "B1_TIPO": "Tipo de produto\n\nMC - Material de consumo\nMP - Matéria-prima\nPA - Produto Acabado\nPI - "
                       "Produto Intermediário\nSV - Serviço",
            "B1_UM": "Unidade de medida",
            "B1_LOCPAD": "Armazém padrão\n\n01 - Matéria-prima\n02 - Produto Intermediário\n03 - Produto "
                         "Comercial\n04 - Produto Acabado",
            "B1_GRUPO": "Grupo do produto",
            "B1_ZZNOGRP": "Descrição do grupo do produto",
            "B1_CC": "Centro de custo",
            "B1_MSBLQL": "Indica se o produto está bloqueado",
            "B1_REVATU": "Revisão atual do produto",
            "B1_DATREF": "Data de referência",
            "B1_UREV": "Unidade de revisão",
            "B1_ZZLOCAL": "Localização do produto"
        }

        headers = dataframe.columns

        # Adicione os cabeçalhos e os tooltips
        for i, header in enumerate(headers):
            item = QTableWidgetItem(header)
            tooltip = tooltips.get(header)
            item.setToolTip(tooltip)
            self.tree.setHorizontalHeaderItem(i, item)

    def ordenar_tabela(self, logical_index):
        # Obter o índice real da coluna (considerando a ordem de classificação)
        index = self.tree.horizontalHeader().sortIndicatorOrder()

        # Definir a ordem de classificação
        order = Qt.AscendingOrder if index == 0 else Qt.DescendingOrder

        # Ordenar a tabela pela coluna clicada
        self.tree.sortItems(logical_index, order)

    def limpar_campos(self):
        # Limpar os dados dos campos
        self.campo_codigo.clear()
        self.campo_descricao.clear()
        self.campo_contem_descricao.clear()
        self.tipo_var.clear()
        self.um_var.clear()
        self.combobox_armazem.clear()
        self.grupo_var.clear()
        self.checkbox_bloqueado.setChecked(False)

    def controle_campos_formulario(self, status):
        self.campo_codigo.setEnabled(status)
        self.campo_descricao.setEnabled(status)
        self.campo_contem_descricao.setEnabled(status)
        self.tipo_var.setEnabled(status)
        self.um_var.setEnabled(status)
        self.combobox_armazem.setEnabled(status)
        self.grupo_var.setEnabled(status)
        self.btn_consultar.setEnabled(status)
        self.btn_exportar_excel.setEnabled(status)
        self.btn_consultar_estrutura.setEnabled(status)
        self.btn_onde_e_usado.setEnabled(status)

    def query_consulta_tabela_produtos(self):

        codigo = self.campo_codigo.text().upper().strip()
        descricao = self.campo_descricao.text().upper().strip()
        descricao2 = self.campo_contem_descricao.text().upper().strip()
        tipo = self.tipo_var.text().upper().strip()
        um = self.um_var.text().upper().strip()
        armazem = self.combobox_armazem.currentData()
        grupo = self.grupo_var.text().upper().strip()
        status_checkbox = self.checkbox_bloqueado.isChecked()

        armazem = armazem if armazem is not None else ''

        lista_campos = [codigo, descricao, descricao2, tipo, um, armazem, grupo]

        if all(valor == '' for valor in lista_campos):
            self.btn_consultar.setEnabled(False)
            exibir_mensagem("ATENÇÃO!",
                            "Os campos de pesquisa estão vazios.\nPreencha algum campo e tente "
                            "novamente.\n\nツ\n\nSMARTPLIC®",
                            "info")
            return True

        # Dividir descricao2 em partes usando o delimitador *
        descricao2_parts = descricao2.split('*')
        # Construir cláusulas LIKE dinamicamente para descricao2
        descricao2_clauses = " AND ".join([f"B1_DESC LIKE '%{part}%'" for part in descricao2_parts])

        # Montar a query com base no status do checkbox
        status_bloqueado = '1' if status_checkbox else ''
        status_clause = f"AND B1_MSBLQL = '{status_bloqueado}'" if status_checkbox else ''

        query = f"""
        SELECT B1_COD AS "Código", 
            B1_DESC AS "Descrição", 
            B1_XDESC2 AS "Desc. Compl.", 
            B1_TIPO AS "Tipo", 
            B1_UM AS "Unid. Med", 
            B1_LOCPAD AS "Armazém", 
            B1_GRUPO AS "Grupo", 
            B1_ZZNOGRP AS "Desc. Grupo", 
            B1_CC AS "Centro Custo", 
            B1_MSBLQL AS "Bloqueado?", 
            B1_REVATU AS "Últ. Rev.", 
            B1_DATREF AS "Cadastrado em:", 
            B1_UREV AS "Data Últ. Rev.", 
            B1_ZZLOCAL AS "Endereço"
        FROM 
            {database}.dbo.SB1010
        WHERE 
            B1_COD LIKE '{codigo}%' 
            AND B1_DESC LIKE '{descricao}%' 
            AND {descricao2_clauses}
            AND B1_TIPO LIKE '{tipo}%' 
            AND B1_UM LIKE '{um}%' 
            AND B1_LOCPAD LIKE '{armazem}%' 
            AND B1_GRUPO LIKE '{grupo}%' {status_clause}
            AND D_E_L_E_T_ <> '*'
            ORDER BY B1_COD ASC
        """
        return query

    def executar_consulta(self):
        select_query = self.query_consulta_tabela_produtos()

        if isinstance(select_query, bool) and select_query:
            self.btn_consultar.setEnabled(True)
            return

        self.controle_campos_formulario(False)

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe = pd.read_sql(select_query, self.engine)
            dataframe[''] = ''

            if not dataframe.empty:

                self.configurar_tabela(dataframe)
                self.configurar_tabela_tooltips(dataframe)

                # Limpar a ordenação
                self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)

                # Limpar a tabela
                self.tree.setRowCount(0)

                time.sleep(0.1)
            else:
                exibir_mensagem("EUREKA® engenharia", 'Nada encontrado!', "info")
                self.controle_campos_formulario(True)
                return

            # Preencher a tabela com os resultados
            for i, row in dataframe.iterrows():

                self.tree.setSortingEnabled(False)  # Permitir ordenação
                # Inserir os valores formatados na tabela
                self.tree.insertRow(i)
                for j, value in enumerate(row):
                    if j == 9:  # Verifica se o valor é da coluna B1_MSBLQL
                        # Converte o valor 1 para 'Sim' e 2 para 'Não'
                        if value == '1':
                            value = 'Sim'
                        else:
                            value = 'Não'
                    elif j == 11 or j == 12:
                        if not value.isspace():
                            data_obj = datetime.strptime(value, "%Y%m%d")
                            value = data_obj.strftime("%d/%m/%Y")

                    item = QTableWidgetItem(str(value).strip())

                    if j != 0 and j != 1:
                        item.setTextAlignment(Qt.AlignCenter)

                    self.tree.setItem(i, j, item)

                # Permitir que a interface gráfica seja atualizada
                # QCoreApplication.processEvents()

            self.tree.setSortingEnabled(True)  # Permitir ordenação

            self.controle_campos_formulario(True)

        except pyodbc.Error as ex:
            print(f"Falha na consulta. Erro: {str(ex)}")

        finally:
            if hasattr(self, 'engine'):
                self.engine.dispose()
                self.engine = None
            self.interromper_consulta_sql = False

    def abrir_desenho(self, table):
        item_selecionado = table.currentItem()

        if item_selecionado:
            codigo = table.item(item_selecionado.row(), 0).text()
            pdf_path = os.path.join(r"\\192.175.175.4\dados\EMPRESA\PROJETOS\PDF-OFICIAL", f"{codigo}.PDF")
            pdf_path = os.path.normpath(pdf_path)

            if os.path.exists(pdf_path):
                QCoreApplication.processEvents()
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            else:
                mensagem = f"Desenho não encontrado!\n\n:-("
                QMessageBox.information(self, f"{codigo}", mensagem)

    def abrir_nova_janela(self):
        if not self.nova_janela or not self.nova_janela.isVisible():
            self.nova_janela = EngenhariaApp()
            self.nova_janela.setGeometry(self.x() + 50, self.y() + 50, self.width(), self.height())
            self.nova_janela.show()

    def fechar_janela(self):
        self.close()

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

    def executar_consulta_estrutura(self, table):
        item_selecionado = table.currentItem()

        if item_selecionado:
            codigo = table.item(item_selecionado.row(), 0).text()
            descricao = table.item(item_selecionado.row(), 1).text()

            if codigo not in self.guias_abertas:
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

                    # Permitir edição apenas na coluna "Quantidade" (assumindo que "Quantidade" é a terceira coluna,
                    # índice 2)
                    tree_estrutura.setEditTriggers(QAbstractItemView.DoubleClicked)
                    tree_estrutura.setItemDelegateForColumn(2, QItemDelegate(tree_estrutura))

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
                    tree_estrutura.itemChanged.connect(
                        lambda item: handle_item_change(item, tree_estrutura, codigo))
                    self.guias_abertas.append(codigo)
                    conn_estrutura.close()

    def executar_consulta_onde_usado(self, table):
        item_selecionado = table.currentItem()

        if item_selecionado:
            codigo = table.item(item_selecionado.row(), 0).text()
            descricao_onde_usado = table.item(item_selecionado.row(), 1).text()

            if codigo not in self.guias_abertas_onde_usado:
                query_onde_usado = f"""
                    SELECT STRUT.G1_COD AS "Código", PROD.B1_DESC "Descrição" 
                    FROM {database}.dbo.SG1010 STRUT 
                    INNER JOIN {database}.dbo.SB1010 PROD 
                    ON G1_COD = B1_COD WHERE G1_COMP = '{codigo}' 
                    AND STRUT.G1_REVFIM <> 'ZZZ' AND STRUT.D_E_L_E_T_ <> '*'
                    AND STRUT.G1_REVFIM = (SELECT MAX(G1_REVFIM) 
                                            FROM {database}.dbo.SG1010 
                                            WHERE 
                                                G1_COD = '{codigo}' 
                                                AND G1_REVFIM <> 'ZZZ' 
                                                AND STRUT.D_E_L_E_T_ <> '*');

                """
                self.guias_abertas_onde_usado.append(codigo)
                try:
                    conn_estrutura = pyodbc.connect(
                        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')

                    cursor_estrutura = conn_estrutura.cursor()
                    cursor_estrutura.execute(query_onde_usado)

                    nova_guia_estrutura = QWidget()
                    layout_nova_guia_estrutura = QVBoxLayout()
                    layout_cabecalho = QHBoxLayout()

                    tabela_onde_usado = QTableWidget(nova_guia_estrutura)

                    tabela_onde_usado.setContextMenuPolicy(Qt.CustomContextMenu)
                    tabela_onde_usado.customContextMenuRequested.connect(
                        lambda pos: self.showContextMenu(pos, tabela_onde_usado))

                    tabela_onde_usado.setColumnCount(len(cursor_estrutura.description))
                    tabela_onde_usado.setHorizontalHeaderLabels([desc[0] for desc in cursor_estrutura.description])

                    # Tornar a tabela somente leitura
                    tabela_onde_usado.setEditTriggers(QTableWidget.NoEditTriggers)

                    # Configurar a fonte da tabela
                    fonte_tabela = QFont("Segoe UI", 8)  # Substitua por sua fonte desejada e tamanho
                    tabela_onde_usado.setFont(fonte_tabela)

                    # Ajustar a altura das linhas
                    altura_linha = 22  # Substitua pelo valor desejado
                    tabela_onde_usado.verticalHeader().setDefaultSectionSize(altura_linha)

                    for i, row in enumerate(cursor_estrutura.fetchall()):
                        tabela_onde_usado.insertRow(i)
                        for j, value in enumerate(row):
                            valor_formatado = str(value).strip()

                            item = QTableWidgetItem(valor_formatado)
                            tabela_onde_usado.setItem(i, j, item)

                    tabela_onde_usado.setSortingEnabled(True)

                    # Ajustar automaticamente a largura da coluna "Descrição"
                    ajustar_largura_coluna_descricao(tabela_onde_usado)

                    layout_cabecalho.addWidget(QLabel(f'Onde é usado?\n\n{codigo} - {descricao_onde_usado}'),
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
                    tabela_onde_usado.itemDoubleClicked.connect(copiar_linha)

                except pyodbc.Error as ex:
                    print(f"Falha na consulta de estrutura. Erro: {str(ex)}")

                finally:
                    self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(nova_guia_estrutura))
                    conn_estrutura.close()

    def executar_saldo_em_estoque(self, table):
        item_selecionado = table.currentItem()

        if item_selecionado:
            codigo = table.item(item_selecionado.row(), 0).text()
            descricao = table.item(item_selecionado.row(), 1).text()

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

                    tabela_saldo_estoque.setContextMenuPolicy(Qt.CustomContextMenu)
                    tabela_saldo_estoque.customContextMenuRequested.connect(
                        lambda pos: self.showContextMenu(pos, tabela_saldo_estoque))

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
                    tabela_saldo_estoque.itemDoubleClicked.connect(copiar_linha)

                except pyodbc.Error as ex:
                    print(f"Falha na consulta de estrutura. Erro: {str(ex)}")

                finally:
                    self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(nova_guia_saldo))
                    conn_saldo.close()


class SearchWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Search Results')
        self.setGeometry(300, 300, 600, 400)

        # Conectando ao banco de dados
        self.db = QSqlDatabase.addDatabase('QODBC')
        self.db.setDatabaseName('DRIVER={SQL Server};SERVER=server;DATABASE=database;UID=username;PWD=password')

        if not self.db.open():
            print("Failed to connect to database")
            return

        # Executando a query e exibindo os resultados
        self.model = QSqlQueryModel()
        self.model.setQuery(
            "SELECT BM_GRUPO, BM_DESC FROM PROTHEUS12_R27.dbo.SBM010 WHERE D_E_L_E_T_ <> '*' ORDER BY BM_DESC ASC;")

        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EngenhariaApp()
    username, password, database, server = setup_mssql()
    driver = '{SQL Server}'

    largura_janela = 1400  # Substitua pelo valor desejado
    altura_janela = 700  # Substitua pelo valor desejado

    largura_tela = app.primaryScreen().size().width()
    altura_tela = app.primaryScreen().size().height()

    pos_x = (largura_tela - largura_janela) // 2
    pos_y = (altura_tela - altura_janela) // 2

    window.setGeometry(pos_x, pos_y, largura_janela, altura_janela)

    window.show()
    sys.exit(app.exec_())
