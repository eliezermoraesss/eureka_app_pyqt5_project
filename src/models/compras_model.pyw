import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QStyle, QAction, QDateEdit, QLabel, QMessageBox, \
    QComboBox, QProgressBar
from PyQt5.QtGui import QFont, QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QCoreApplication, QDate, QUrl
import pyperclip
import pandas as pd
import ctypes
from datetime import date, datetime
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine, select, MetaData, Table
import os


class ComprasApp(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = None
        self.metadata = MetaData()
        self.nnr_table = Table('NNR010', self.metadata, autoload_with=self.engine, schema='dbo')
        self.combobox_armazem = QComboBox(self)
        self.combobox_armazem.setEditable(False)

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

        self.altura_linha = 30
        self.tamanho_fonte_tabela = 10
        self.fonte_tabela = 'Segoe UI'
        fonte_campos = "Segoe UI"
        tamanho_fonte_campos = 16

        self.interromper_consulta_sql = False
        self.tree = QTableWidget(self)
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)

        self.nova_janela = None

        self.setWindowTitle("EUREKA® Compras - v0.1")

        self.setStyleSheet("""
            * {
                background-color: #373A40;
            }

            QLabel {
                color: #EEEEEE;
                font-size: 14px;
                margin-top: 20px;
            }
            
            QLabel#descricao-produto, QLabel#fornecedor {
                color: #EEEEEE;
                font-size: 14px;
            }
            
            QDateEdit, QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #262626;
                margin-bottom: 20px;
                padding: 5px 10px;
                border-radius: 10px;
                height: 24px;
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

            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #262626;
                margin-top: 20px;
                margin-bottom: 20px;
                padding: 5px 10px;
                border-radius: 10px;
                height: 24px;
                font-size: 16px;
            }

            QPushButton {
                background-color: #836FFF;
                color: #EEEEEE;
                padding: 10px;
                border-radius: 8px;
                font-size: 12px;
                height: 15px;
                font-weight: bold;
                margin-bottom: 8px;
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
                color: #EEEEEE;
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

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximumWidth(400)

        self.label_sc = QLabel("Solic. Compra:", self)
        self.label_pedido = QLabel("Ped. de Compra:", self)
        self.label_codigo = QLabel("Código produto:", self)

        self.label_descricao_prod = QLabel("Descrição produto:", self)
        # self.label_descricao_prod.setObjectName("descricao-produto")

        self.label_qp = QLabel("Número QP:", self)
        self.label_OP = QLabel("Número OP:", self)
        self.label_data_inicio = QLabel("Data inicial SC:", self)
        self.label_data_fim = QLabel("Data final SC:", self)
        self.label_armazem = QLabel("Armazém:", self)

        self.label_fornecedor = QLabel("Fornecedor:", self)
        # self.label_fornecedor.setObjectName("fornecedor")

        self.campo_sc = QLineEdit(self)
        self.campo_sc.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_sc.setMaxLength(6)
        self.campo_sc.setFixedWidth(110)
        self.add_clear_button(self.campo_sc)

        self.campo_pedido = QLineEdit(self)
        self.campo_pedido.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_pedido.setMaxLength(6)
        self.campo_pedido.setFixedWidth(110)
        self.add_clear_button(self.campo_pedido)

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

        self.campo_fornecedor = QLineEdit(self)
        self.campo_fornecedor.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_fornecedor.setMaxLength(40)
        self.campo_fornecedor.setFixedWidth(200)
        self.add_clear_button(self.campo_fornecedor)

        self.campo_data_inicio = QDateEdit(self)
        self.campo_data_inicio.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_data_inicio.setFixedWidth(150)
        self.campo_data_inicio.setCalendarPopup(True)
        self.campo_data_inicio.setDisplayFormat("dd/MM/yyyy")

        data_atual = QDate.currentDate()
        intervalo_meses = 6
        data_inicio = data_atual.addMonths(-intervalo_meses)
        self.campo_data_inicio.setDate(data_inicio)
        self.add_today_button(self.campo_data_inicio)

        self.campo_data_fim = QDateEdit(self)
        self.campo_data_fim.setFont(QFont("Segoe UI", 10))
        self.campo_data_fim.setFixedWidth(150)
        self.campo_data_fim.setCalendarPopup(True)
        self.campo_data_fim.setDisplayFormat("dd/MM/yyyy")
        self.campo_data_fim.setDate(QDate().currentDate())
        self.add_today_button(self.campo_data_fim)

        self.btn_consultar = QPushButton("Pesquisar", self)
        self.btn_consultar.clicked.connect(self.executar_consulta)
        self.btn_consultar.setMinimumWidth(100)

        self.btn_limpar = QPushButton("Limpar", self)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_limpar.setMinimumWidth(100)

        self.btn_parar_consulta = QPushButton("Parar consulta")
        self.btn_parar_consulta.clicked.connect(self.parar_consulta)
        self.btn_parar_consulta.setMinimumWidth(100)

        self.btn_nova_janela = QPushButton("Nova Janela", self)
        self.btn_nova_janela.clicked.connect(self.abrir_nova_janela)
        self.btn_nova_janela.setMinimumWidth(100)

        self.btn_exportar_excel = QPushButton("Exportar Excel", self)
        self.btn_exportar_excel.clicked.connect(self.exportar_excel)
        self.btn_exportar_excel.setMinimumWidth(100)
        self.btn_exportar_excel.setEnabled(False)

        self.btn_fechar = QPushButton("Fechar", self)
        self.btn_fechar.clicked.connect(self.fechar_janela)
        self.btn_fechar.setMinimumWidth(100)

        self.campo_sc.returnPressed.connect(self.executar_consulta)
        self.campo_pedido.returnPressed.connect(self.executar_consulta)
        self.campo_codigo.returnPressed.connect(self.executar_consulta)
        self.campo_descricao_prod.returnPressed.connect(self.executar_consulta)
        self.campo_qp.returnPressed.connect(self.executar_consulta)
        self.campo_OP.returnPressed.connect(self.executar_consulta)
        self.campo_fornecedor.returnPressed.connect(self.executar_consulta)

        layout = QVBoxLayout()
        layout_campos_linha_01 = QHBoxLayout()
        self.layout_buttons = QHBoxLayout()
        self.layout_footer = QHBoxLayout()

        container_sc = QVBoxLayout()
        container_sc.addWidget(self.label_sc)
        container_sc.addWidget(self.campo_sc)

        container_pedido = QVBoxLayout()
        container_pedido.addWidget(self.label_pedido)
        container_pedido.addWidget(self.campo_pedido)

        container_codigo = QVBoxLayout()
        container_codigo.addWidget(self.label_codigo)
        container_codigo.addWidget(self.campo_codigo)

        container_descricao_prod = QVBoxLayout()
        container_descricao_prod.addWidget(self.label_descricao_prod)
        container_descricao_prod.addWidget(self.campo_descricao_prod)

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

        container_combobox_armazem = QVBoxLayout()
        container_combobox_armazem.addWidget(self.label_armazem)
        container_combobox_armazem.addWidget(self.combobox_armazem)

        container_fornecedor = QVBoxLayout()
        container_fornecedor.addWidget(self.label_fornecedor)
        container_fornecedor.addWidget(self.campo_fornecedor)

        layout_campos_linha_01.addLayout(container_sc)
        layout_campos_linha_01.addLayout(container_pedido)
        layout_campos_linha_01.addLayout(container_codigo)
        layout_campos_linha_01.addLayout(container_descricao_prod)
        layout_campos_linha_01.addLayout(container_fornecedor)
        layout_campos_linha_01.addLayout(container_qp)
        layout_campos_linha_01.addLayout(container_op)
        layout_campos_linha_01.addLayout(container_data_ini)
        layout_campos_linha_01.addLayout(container_data_fim)
        layout_campos_linha_01.addLayout(container_combobox_armazem)
        layout_campos_linha_01.addStretch()

        self.layout_buttons.addWidget(self.btn_consultar)
        self.layout_buttons.addWidget(self.btn_nova_janela)
        self.layout_buttons.addWidget(self.btn_limpar)
        self.layout_buttons.addWidget(self.btn_exportar_excel)
        self.layout_buttons.addWidget(self.btn_fechar)
        self.layout_buttons.addStretch()

        layout.addLayout(layout_campos_linha_01)
        layout.addLayout(self.layout_buttons)
        layout.addWidget(self.tree)
        layout.addLayout(self.layout_footer)
        self.setLayout(layout)

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

    def abrir_nova_janela(self):
        if not self.nova_janela or not self.nova_janela.isVisible():
            self.nova_janela = ComprasApp()
            self.nova_janela.setGeometry(self.x() + 50, self.y() + 50, self.width(), self.height())
            self.nova_janela.show()

    def add_today_button(self, date_edit):
        calendar = date_edit.calendarWidget()
        calendar.setGeometry(10, 10, 600, 400)
        btn_today = QPushButton("Hoje", calendar)
        largura, altura = 50, 20
        btn_today.setGeometry(20, 5, largura, altura)
        btn_today.clicked.connect(lambda: date_edit.setDate(QDate.currentDate()))

    def add_clear_button(self, line_edit):
        clear_icon = self.style().standardIcon(QStyle.SP_LineEditClearButton)

        line_edit_height = line_edit.height()
        pixmap = clear_icon.pixmap(line_edit_height - 4, line_edit_height - 4)
        larger_clear_icon = QIcon(pixmap)

        clear_action = QAction(larger_clear_icon, "Limpar", line_edit)
        clear_action.triggered.connect(line_edit.clear)
        line_edit.addAction(clear_action, QLineEdit.TrailingPosition)

    def exportar_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar como',
                                                   f'report_{date.today().strftime('%Y-%m-%d')}',
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

    def limpar_campos(self):
        self.campo_sc.clear()
        self.campo_pedido.clear()
        self.campo_codigo.clear()
        self.campo_descricao_prod.clear()
        self.campo_fornecedor.clear()
        self.campo_qp.clear()
        self.campo_OP.clear()

    def controle_campos_formulario(self, status):
        self.campo_sc.setEnabled(status)
        self.campo_codigo.setEnabled(status)
        self.campo_descricao_prod.setEnabled(status)
        self.campo_fornecedor.setEnabled(status)
        self.campo_qp.setEnabled(status)
        self.campo_OP.setEnabled(status)
        self.campo_data_inicio.setEnabled(status)
        self.campo_data_fim.setEnabled(status)
        self.combobox_armazem.setEnabled(status)
        self.btn_consultar.setEnabled(status)
        self.btn_exportar_excel.setEnabled(status)

    def exibir_mensagem(self, title, message, icon_type):
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

    def numero_linhas_consulta(self, numero_sc, numero_pedido, codigo_produto, numero_qp, numero_op, fornecedor,
                               descricao_produto, cod_armazem):

        data_inicio_formatada = self.campo_data_inicio.date().toString("yyyyMMdd")
        data_fim_formatada = self.campo_data_fim.date().toString("yyyyMMdd")

        if data_fim_formatada != '' and data_fim_formatada != '':
            filtro_data = f"AND C1_EMISSAO >= '{data_inicio_formatada}' AND C1_EMISSAO <= '{data_fim_formatada}'"
        else:
            filtro_data = ''

        query = f"""
            SELECT 
                COUNT(*)
            FROM 
                {database}.dbo.SC1010 SC
            LEFT JOIN 
                {database}.dbo.SD1010 ITEM_NF
            ON 
                SC.C1_PEDIDO = ITEM_NF.D1_PEDIDO AND SC.C1_ITEMPED = ITEM_NF.D1_ITEMPC
            LEFT JOIN
                {database}.dbo.SC7010 PC
            ON 
                SC.C1_PEDIDO = PC.C7_NUM AND SC.C1_ITEMPED = PC.C7_ITEM AND SC.C1_ZZNUMQP = PC.C7_ZZNUMQP
            LEFT JOIN
            {database}.dbo.SA2010 FORN
            ON
            FORN.A2_COD = SC.C1_FORNECE
            LEFT JOIN
            {database}.dbo.NNR010 ARM
            ON
            SC.C1_LOCAL = ARM.NNR_CODIGO
            LEFT JOIN 
            {database}.dbo.SYS_USR US
            ON
            SC.C1_SOLICIT = US.USR_CODIGO 
            WHERE 
                SC.C1_PEDIDO LIKE '{numero_pedido}%'
                AND SC.C1_NUM LIKE '%{numero_sc}'
                AND PC.C7_ZZNUMQP LIKE '%{numero_qp}'
                AND SC.C1_PRODUTO LIKE '{codigo_produto}%'
                AND SC.C1_DESCRI LIKE '%{descricao_produto}%'
                AND SC.C1_OP LIKE '{numero_op}%'
                AND FORN.A2_NOME LIKE '%{fornecedor}%' 
                AND SC.C1_LOCAL LIKE '{cod_armazem}%' {filtro_data}
        """
        return query

    def query_consulta_followup(self, numero_sc, numero_pedido, codigo_produto, numero_qp, numero_op,
                                fornecedor, descricao_produto, cod_armazem):

        data_inicio_formatada = self.campo_data_inicio.date().toString("yyyyMMdd")
        data_fim_formatada = self.campo_data_fim.date().toString("yyyyMMdd")

        if data_fim_formatada != '' and data_fim_formatada != '':
            filtro_data = f"AND C1_EMISSAO >= '{data_inicio_formatada}' AND C1_EMISSAO <= '{data_fim_formatada}'"
        else:
            filtro_data = ''

        query = f"""
            SELECT 
                SC.C1_ZZNUMQP AS "QP",
                SC.C1_OP AS "OP",
                SC.C1_NUM AS "SC",
                SC.C1_ITEM AS "Item SC",
                SC.C1_QUANT AS "Quant. SC",
                SC.C1_PEDIDO AS "Ped. Compra",
                SC.C1_ITEMPED AS "Item Ped.",
                SC.C1_QUJE AS "Quant. Ped.",
                ITEM_NF.D1_DOC AS "Nota Fiscal",
                ITEM_NF.D1_QUANT AS "Quant. Entregue",
                CASE WHEN ITEM_NF.D1_QUANT IS NULL THEN SC.C1_QUJE ELSE SC.C1_QUJE - ITEM_NF.D1_QUANT END AS "Quant. Pendente",
                ITEM_NF.D1_DTDIGIT AS "Data Entrega",
                PC.C7_ENCER AS "Status Ped. Compra",
                SC.C1_PRODUTO AS "Código",
                SC.C1_DESCRI AS "Descrição",
                SC.C1_UM AS "UM",
                SC.C1_EMISSAO AS "Emissão SC",
                PC.C7_EMISSAO AS "Emissão PC",
                ITEM_NF.D1_EMISSAO AS "Emissão NF",
                SC.C1_ORIGEM AS "Origem",
                SC.C1_OBS AS "Observação",
                SC.C1_LOCAL AS "Cod. Armazém",
                ARM.NNR_DESCRI AS "Desc. Armazém",
                SC.C1_IMPORT AS "Importado?",
                PC.C7_OBS AS "Observações",
                PC.C7_OBSM AS "Observações item",
                FORN.A2_NOME AS "Fornecedor",
                US.USR_NOME AS "Solicitante"
            FROM 
                {database}.dbo.SC1010 SC
            LEFT JOIN 
                {database}.dbo.SD1010 ITEM_NF
            ON 
                SC.C1_PEDIDO = ITEM_NF.D1_PEDIDO AND SC.C1_ITEMPED = ITEM_NF.D1_ITEMPC
            LEFT JOIN
                {database}.dbo.SC7010 PC
            ON 
                SC.C1_PEDIDO = PC.C7_NUM AND SC.C1_ITEMPED = PC.C7_ITEM AND SC.C1_ZZNUMQP = PC.C7_ZZNUMQP
            LEFT JOIN
            {database}.dbo.SA2010 FORN
            ON
            FORN.A2_COD = SC.C1_FORNECE
            LEFT JOIN
            {database}.dbo.NNR010 ARM
            ON
            SC.C1_LOCAL = ARM.NNR_CODIGO
            LEFT JOIN 
            {database}.dbo.SYS_USR US
            ON
            SC.C1_SOLICIT = US.USR_CODIGO 
            WHERE 
                SC.C1_PEDIDO LIKE '{numero_pedido}%'
                AND SC.C1_NUM LIKE '%{numero_sc}'
                AND PC.C7_ZZNUMQP LIKE '%{numero_qp}'
                AND SC.C1_PRODUTO LIKE '{codigo_produto}%'
                AND SC.C1_DESCRI LIKE '%{descricao_produto}%'
                AND SC.C1_OP LIKE '{numero_op}%' 
                AND FORN.A2_NOME LIKE '%{fornecedor}%'
                AND SC.C1_LOCAL LIKE '{cod_armazem}%' {filtro_data}
            ORDER BY 
                PC.R_E_C_N_O_ DESC;
        """
        return query

    def executar_consulta(self):

        numero_sc = self.campo_sc.text().upper().strip()
        numero_pedido = self.campo_pedido.text().upper().strip()
        numero_qp = self.campo_qp.text().upper().strip()
        numero_op = self.campo_OP.text().upper().strip()
        codigo_produto = self.campo_codigo.text().upper().strip()
        fornecedor = self.campo_fornecedor.text().upper().strip()
        descricao_produto = self.campo_descricao_prod.text().upper().strip()

        cod_armazem = self.combobox_armazem.currentData()
        if cod_armazem is None:
            cod_armazem = ''

        query_consulta_filtro = self.query_consulta_followup(numero_sc, numero_pedido, codigo_produto,
                                                             numero_qp, numero_op, fornecedor, descricao_produto, cod_armazem)

        query_contagem_linhas = self.numero_linhas_consulta(numero_sc, numero_pedido, codigo_produto, numero_qp,
                                                            numero_op, fornecedor, descricao_produto, cod_armazem)

        self.controle_campos_formulario(False)
        line_number = None
        label_line_number = QLabel(f"{line_number} itens localizados.", self)
        self.layout_footer.removeItem(self.layout_footer)

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe_line_number = pd.read_sql(query_contagem_linhas, self.engine)
            line_number = dataframe_line_number.iloc[0, 0]
            dataframe = pd.read_sql(query_consulta_filtro, self.engine)

            if not dataframe.empty:

                self.layout_footer.addWidget(label_line_number)
                self.progress_bar.setMaximum(line_number)
                self.layout_footer.addWidget(self.progress_bar)
                self.layout_buttons.addWidget(self.btn_parar_consulta)

                dataframe.insert(0, 'Status PC', '')
                dataframe[''] = ''

                self.configurar_tabela(dataframe)
                self.configurar_tabela_tooltips(dataframe)

                self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
                self.tree.setRowCount(0)
            else:
                self.exibir_mensagem("EUREKA® Compras", 'Nada encontrado!', "info")
                self.controle_campos_formulario(True)
                return

            # Construir caminhos relativos
            script_dir = os.path.dirname(os.path.abspath(__file__))
            no_order_path = os.path.join(script_dir, '..', 'resources', 'images', 'red.png')
            wait_order_path = os.path.join(script_dir, '..', 'resources', 'images', 'wait.png')
            end_order_path = os.path.join(script_dir, '..', 'resources', 'images', 'green.png')

            no_order = QIcon(no_order_path)
            wait_delivery = QIcon(wait_order_path)
            end_order = QIcon(end_order_path)

            for i, row in dataframe.iterrows():
                if self.interromper_consulta_sql:
                    break

                self.tree.setSortingEnabled(False)
                self.tree.insertRow(i)
                self.tree.setColumnHidden(13, True)

                for j, value in enumerate(row):
                    if value is not None:
                        if j == 0:
                            item = QTableWidgetItem()
                            if row['Status Ped. Compra'].strip() == '' and row['Nota Fiscal'] is None:
                                item.setIcon(no_order)
                            elif row['Status Ped. Compra'].strip() == '' and row['Nota Fiscal'] is not None:
                                item.setIcon(wait_delivery)
                            elif row['Status Ped. Compra'] == 'E':
                                item.setIcon(end_order)
                        else:
                            if j == 10 and pd.isna(value):
                                value = '-'
                            if j == 11 and value:
                                value = round(value, 2)
                            if j == 20 and value.strip() == 'MATA650':  # Indica na coluna 'Origem' se o item foi
                                # empenhado ou será comprado
                                value = 'Empenho'
                            elif j == 20 and value.strip() == '':
                                value = 'Compras'

                            if j == 24 and value.strip() == 'N':  # Escreve sim ou não na coluna 'Importado?'
                                value = 'Não'
                            elif j == 24 and value.strip() == '':
                                value = 'Sim'

                            if j in (12, 17, 18, 19) and not value.isspace():  # Formatação das datas no formato
                                # dd/mm/YYYY
                                data_obj = datetime.strptime(value, "%Y%m%d")
                                value = data_obj.strftime("%d/%m/%Y")

                            item = QTableWidgetItem(str(value).strip())

                            if j not in (14, 15, 21, 25, 26, 27, 28):  # Alinhamento a esquerda de colunas
                                item.setTextAlignment(Qt.AlignCenter)

                    self.tree.setItem(i, j, item)

                self.progress_bar.setValue(i + 1)
                QCoreApplication.processEvents()

            self.layout_buttons.removeWidget(self.btn_parar_consulta)
            self.btn_parar_consulta.setParent(None)
            self.tree.setSortingEnabled(True)
            self.controle_campos_formulario(True)

        except Exception as ex:
            self.exibir_mensagem('Erro ao consultar TOTVS', f'Erro: {str(ex)}', 'error')

        finally:
            # Fecha a conexão com o banco de dados se estiver aberta
            if hasattr(self, 'engine'):
                self.engine.dispose()
                self.engine = None
            self.interromper_consulta_sql = False

    def configurar_tabela_tooltips(self, dataframe):
        # Mapa de tooltips correspondentes às colunas da consulta SQL
        tooltip_map = {
            "Status PC": "VERMELHO -> AGUARDANDO ENTREGA\n\nAZUL -> ENTREGA PARCIAL\n\nVERDE -> PEDIDO DE COMPRA "
                         "ENCERRADO",
            "QP": "Número do Quadro de Produção (QP)",
            "OP": "Número da Ordem de Produção (OP)",
            "SC": "Número da Solicitação de Compras (SC)",
            "Item SC": "Número do item na Solicitação de Compras",
            "Quant. SC": "Quantidade solicitada na SC",
            "Ped. Compra": "Número do Pedido de Compra",
            "Item Ped.": "Número do item no Pedido de Compra",
            "Quant. Ped.": "Quantidade solicitada no Pedido de Compra",
            "Nota Fiscal": "Número da Nota Fiscal",
            "Quant. Entregue": "Quantidade entregue conforme a Nota Fiscal",
            "Quant. Pendente": "Quantidade pendente de entrega",
            "Data Entrega": "Data da entrega",
            "Status Ped. Compra": "Status do Pedido de Compra",
            "Código": "Código do produto",
            "Descrição": "Descrição do produto",
            "UM": "Unidade de medida",
            "Emissão SC": "Data de emissão da SC",
            "Emissão PC": "Data de emissão do Pedido de Compra",
            "Emissão NF": "Data de emissão da Nota Fiscal",
            "Origem": "Origem do item",
            "Observação": "Observações gerais sobre o item",
            "Cod. Armazém": "Código do armazém",
            "Desc. Armazém": "Descrição do armazém",
            "Importado?": "Indica se o produto é importado",
            "Observações": "Observações gerais",
            "Observações item": "Observações específicas do item",
            "Fornecedor": "Nome do fornecedor",
            "Solicitante": "Nome do solicitante"
        }

        # Obtenha os cabeçalhos das colunas do dataframe
        headers = dataframe.columns

        # Adicione os cabeçalhos e os tooltips
        for i, header in enumerate(headers):
            item = QTableWidgetItem(header)
            tooltip = tooltip_map.get(header, "Tooltip não definido")
            item.setToolTip(tooltip)
            self.tree.setHorizontalHeaderItem(i, item)

    def fechar_janela(self):
        self.close()

    def parar_consulta(self):
        self.interromper_consulta_sql = True
        if hasattr(self, 'engine') and self.engine is not None:
            self.engine.dispose()
        self.controle_campos_formulario(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ComprasApp()
    username, password, database, server = ComprasApp().setup_mssql()
    driver = '{SQL Server}'
    window.showMaximized()
    sys.exit(app.exec_())
