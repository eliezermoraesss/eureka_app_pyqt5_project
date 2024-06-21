import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QStyle, QAction, QDateEdit, QLabel, QMessageBox, \
    QProgressBar, QSizePolicy, QTabWidget
from PyQt5.QtGui import QFont, QColor, QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QCoreApplication, QDate, QUrl, QProcess, pyqtSignal
import pyperclip
import pandas as pd
import ctypes
from datetime import date, datetime
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
import os


class PcpApp(QWidget):
    guia_fechada = pyqtSignal()
    def __init__(self):
        super().__init__()

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

        self.altura_linha = 30
        self.tamanho_fonte_tabela = 10

        self.fonte_tabela = 'Segoe UI'
        fonte_campos = "Segoe UI"
        tamanho_fonte_campos = 16

        self.setWindowTitle("EUREKA® PCP - v0.1")

        self.setStyleSheet("""
            * {
                background-color: #373A40;
            }

            QLabel {
                color: #EEEEEE;
                font-size: 12px;
                font-weight: bold;
                padding-left: 3px;
            }
            
            QDateEdit {
                background-color: #FFFFFF;
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
                background-color: #FFFFFF;
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
                margin: 0px 5px 10px 5px;
            }

            QPushButton:hover {
                background-color: #0a79f8;
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

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximumWidth(400)

        self.label_codigo = QLabel("Código produto:", self)
        self.label_descricao_prod = QLabel("Descrição produto:", self)
        self.label_OP = QLabel("Número OP:", self)
        self.label_qp = QLabel("Número QP:", self)
        self.label_data_inicio = QLabel("Data inicial:", self)
        self.label_data_inicio.setObjectName("data-inicio")
        self.label_data_fim = QLabel("Data final:", self)
        self.label_data_fim.setObjectName("data-fim")

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

        self.campo_data_inicio = QDateEdit(self)
        self.campo_data_inicio.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_data_inicio.setFixedWidth(150)
        self.campo_data_inicio.setCalendarPopup(True)
        self.campo_data_inicio.setDisplayFormat("dd/MM/yyyy")

        data_atual = QDate.currentDate()
        intervalo_meses = 12
        data_inicio = data_atual.addMonths(-intervalo_meses)
        self.campo_data_inicio.setDate(data_inicio)
        self.add_today_button(self.campo_data_inicio)

        self.campo_data_fim = QDateEdit(self)
        self.campo_data_fim.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_data_fim.setFixedWidth(150)
        self.campo_data_fim.setCalendarPopup(True)
        self.campo_data_fim.setDisplayFormat("dd/MM/yyyy")
        self.campo_data_fim.setDate(QDate().currentDate())
        self.add_today_button(self.campo_data_fim)

        self.btn_consultar = QPushButton("Pesquisar", self)
        self.btn_consultar.clicked.connect(self.executar_consulta)
        self.btn_consultar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_abrir_compras = QPushButton("Follow-up Compras", self)
        self.btn_abrir_compras.clicked.connect(self.abrir_modulo_compras)
        self.btn_abrir_compras.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_limpar = QPushButton("Limpar", self)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_limpar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_parar_consulta = QPushButton("Parar consulta")
        self.btn_parar_consulta.clicked.connect(self.parar_consulta)
        self.btn_parar_consulta.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_nova_janela = QPushButton("Nova Janela", self)
        self.btn_nova_janela.clicked.connect(self.abrir_nova_janela)
        self.btn_nova_janela.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_abrir_desenho = QPushButton("Abrir Desenho", self)
        self.btn_abrir_desenho.clicked.connect(self.abrir_desenho)
        self.btn_abrir_desenho.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

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

        layout = QVBoxLayout()
        layout_campos_linha_01 = QHBoxLayout()
        layout_campos_linha_02 = QHBoxLayout()
        self.layout_buttons = QHBoxLayout()
        self.layout_footer = QHBoxLayout()

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

        layout_campos_linha_01.addLayout(container_codigo)
        layout_campos_linha_01.addLayout(container_descricao_prod)
        layout_campos_linha_01.addLayout(container_op)
        layout_campos_linha_01.addLayout(container_qp)
        layout_campos_linha_02.addLayout(container_data_ini)
        layout_campos_linha_02.addLayout(container_data_fim)
        layout_campos_linha_01.addStretch()
        layout_campos_linha_02.addStretch()

        self.layout_buttons.addWidget(self.btn_consultar)
        self.layout_buttons.addWidget(self.btn_abrir_compras)
        self.layout_buttons.addWidget(self.btn_nova_janela)
        self.layout_buttons.addWidget(self.btn_limpar)
        self.layout_buttons.addWidget(self.btn_abrir_desenho)
        self.layout_buttons.addWidget(self.btn_exportar_excel)
        self.layout_buttons.addWidget(self.btn_fechar)
        self.layout_buttons.addStretch()

        layout.addLayout(layout_campos_linha_01)
        layout.addLayout(layout_campos_linha_02)
        layout.addLayout(self.layout_buttons)
        layout.addWidget(self.tree)
        layout.addLayout(self.layout_footer)
        self.setLayout(layout)

    def limpar_campos(self):
        self.campo_codigo.clear()
        self.campo_qp.clear()
        self.campo_OP.clear()
        self.campo_descricao_prod.clear()

    def abrir_desenho(self):
        item_selecionado = self.tree.currentItem()

        if item_selecionado:
            codigo = self.tree.item(item_selecionado.row(), 5).text()
            pdf_path = os.path.join(r"\\192.175.175.4\dados\EMPRESA\PROJETOS\PDF-OFICIAL", f"{codigo}.PDF")
            pdf_path = os.path.normpath(pdf_path)

            if os.path.exists(pdf_path):
                QCoreApplication.processEvents()
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            else:
                mensagem = f"Desenho não encontrado!\n\n:-("
                QMessageBox.information(self, f"{codigo}", mensagem)

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

    def controle_campos_formulario(self, status):
        self.campo_codigo.setEnabled(status)
        self.campo_qp.setEnabled(status)
        self.campo_OP.setEnabled(status)
        self.campo_data_inicio.setEnabled(status)
        self.campo_data_fim.setEnabled(status)
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

    def numero_linhas_consulta(self, codigo_produto, numero_qp, numero_op, descricao_produto):

        data_inicio_formatada = self.campo_data_inicio.date().toString("yyyyMMdd")
        data_fim_formatada = self.campo_data_fim.date().toString("yyyyMMdd")

        filtro_data = f"AND C2_EMISSAO >= '{data_inicio_formatada}' AND C2_EMISSAO <= '{data_fim_formatada}'" if data_fim_formatada != '' and data_fim_formatada != '' else ''

        query = f"""
                    SELECT 
                        COUNT(*)
                    FROM 
                        {database}.dbo.SC2010 op
                    LEFT JOIN 
                        SB1010 prod ON C2_PRODUTO = B1_COD
                    LEFT JOIN 
                        {database}.dbo.SYS_USR users
                    ON 
                        users.USR_CNLOGON = op.C2_XMAQUIN AND users.D_E_L_E_T_ <> '*'
                    WHERE 
                        C2_ZZNUMQP LIKE '%{numero_qp}'
                        AND C2_PRODUTO LIKE '{codigo_produto}%'
                        AND prod.B1_DESC LIKE '{descricao_produto}%'
                        AND C2_NUM LIKE '{numero_op}%' {filtro_data}
                        AND op.D_E_L_E_T_ <> '*'
                """
        return query

    def query_consulta_ordem_producao(self, codigo_produto, numero_qp, numero_op, descricao_produto):

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
                users.USR_CNLOGON = op.C2_XMAQUIN AND users.D_E_L_E_T_ <> '*'
            WHERE 
                C2_ZZNUMQP LIKE '%{numero_qp}'
                AND C2_PRODUTO LIKE '{codigo_produto}%'
                AND prod.B1_DESC LIKE '{descricao_produto}%'
                AND C2_NUM LIKE '{numero_op}%' {filtro_data}
                AND op.D_E_L_E_T_ <> '*'
            ORDER BY 
                op.R_E_C_N_O_ DESC;
        """
        return query

    def validar_campos(self, codigo_produto, numero_qp, numero_op):

        if len(codigo_produto) != 13 and not codigo_produto == '':
            self.exibir_mensagem("ATENÇÃO!",
                                 "Produto não encontrado!\n\nCorrija e tente "
                                 f"novamente.\n\nツ\n\nSMARTPLIC®",
                                 "info")
            return True

        if len(numero_op) != 6 and not numero_op == '':
            self.exibir_mensagem("ATENÇÃO!",
                                 "Ordem de Produção não encontrada!\n\nCorrija e tente "
                                 f"novamente.\n\nツ\n\nSMARTPLIC®",
                                 "info")
            return True

        if len(numero_qp.zfill(6)) != 6 and not numero_qp == '':
            self.exibir_mensagem("ATENÇÃO!",
                                 "QP não encontrada!\n\nCorrija e tente "
                                 f"novamente.\n\nツ\n\nSMARTPLIC®",
                                 "info")
            return True

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

        numero_qp = self.campo_qp.text().upper().strip()
        numero_op = self.campo_OP.text().upper().strip()
        codigo_produto = self.campo_codigo.text().upper().strip()
        descricao_produto = self.campo_descricao_prod.text().upper().strip()

        if self.validar_campos(codigo_produto, numero_qp, numero_op):
            self.btn_consultar.setEnabled(True)
            return

        numero_qp = numero_qp.zfill(6) if numero_qp != '' else numero_qp

        query_consulta_op = self.query_consulta_ordem_producao(codigo_produto, numero_qp, numero_op, descricao_produto)
        query_contagem_linhas = self.numero_linhas_consulta(codigo_produto, numero_qp, numero_op, descricao_produto)

        self.controle_campos_formulario(False)
        line_number = None
        label_line_number = QLabel(f"{line_number} itens localizados.", self)
        self.layout_footer.removeWidget(label_line_number)
        self.layout_footer.removeItem(self.layout_footer)

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe_line_number = pd.read_sql(query_contagem_linhas, self.engine)
            line_number = dataframe_line_number.iloc[0, 0]
            dataframe = pd.read_sql(query_consulta_op, self.engine)

            if not dataframe.empty:

                self.layout_footer.addWidget(label_line_number)
                self.progress_bar.setMaximum(line_number)
                self.layout_footer.addWidget(self.progress_bar)
                # self.layout_buttons.addWidget(self.btn_parar_consulta)

                dataframe.insert(0, 'Status OP', '')
                dataframe[''] = ''

                self.configurar_tabela(dataframe)
                self.configurar_tabela_tooltips(dataframe)

                self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
                self.tree.setRowCount(0)
            else:
                self.exibir_mensagem("EUREKA® PCP", 'Nada encontrado!', "info")
                self.controle_campos_formulario(True)
                return

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

                    self.tree.setItem(i, j, item)

                self.progress_bar.setValue(i + 1)
                # QCoreApplication.processEvents()

            # self.layout_buttons.removeWidget(self.btn_parar_consulta)
            # self.btn_parar_consulta.setParent(None)
            self.tree.setSortingEnabled(True)
            self.controle_campos_formulario(True)

        except Exception as ex:
            self.exibir_mensagem('Erro ao consultar tabela', f'Erro: {str(ex)}', 'error')

        finally:
            # Fecha a conexão com o banco de dados se estiver aberta
            if hasattr(self, 'engine'):
                self.engine.dispose()
                self.engine = None
            self.interromper_consulta_sql = False

    def fechar_janela(self):
        self.close()

    def parar_consulta(self):
        self.interromper_consulta_sql = True
        if hasattr(self, 'engine') and self.engine is not None:
            self.engine.dispose()
        self.controle_campos_formulario(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PcpApp()
    username, password, database, server = PcpApp().setup_mssql()
    driver = '{SQL Server}'

    window.showMaximized()

    sys.exit(app.exec_())
