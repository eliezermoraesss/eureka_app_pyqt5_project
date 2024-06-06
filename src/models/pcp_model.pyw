import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QToolButton, QStyle, QAction
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtCore import Qt, QCoreApplication, QSize
import pyodbc
import pyperclip
import pandas as pd
import ctypes
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
import os


class PcpApp(QWidget):
    def __init__(self):
        super().__init__()

        self.tree = QTableWidget(self)
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)

        self.setWindowTitle("EUREKA® PCP - v0.1")

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor('#363636'))
        self.setPalette(palette)

        self.setStyleSheet("""
            * {
                background-color: #373A40;
            }

            QLabel {
                color: #262626;
                font-size: 12px;
                padding: 5px;
                font-weight: bold;
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
                background-color: #DC5F00;
                color: #fff;
                padding: 15px;
                border: 2px;
                border-radius: 8px;
                font-size: 12px;
                height: 20px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0a79f8;
                color: #0a79f8
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
            }

            QTableWidget::item:selected {
                background-color: #000000;
                color: #EEEEEE;
                font-weight: bold;
            }
        """)

        self.campo_codigo = QLineEdit(self)
        self.campo_codigo.setFont(QFont("Segoe UI", 10))
        self.campo_codigo.setFixedWidth(200)
        self.campo_codigo.setPlaceholderText("Digite o código...")
        self.add_clear_button(self.campo_codigo)

        self.campo_qp = QLineEdit(self)
        self.campo_qp.setFont(QFont("Segoe UI", 10))
        self.campo_qp.setFixedWidth(300)
        self.campo_qp.setPlaceholderText("Digite o número da QP...")
        self.add_clear_button(self.campo_qp)

        self.campo_OP = QLineEdit(self)
        self.campo_OP.setFont(QFont("Segoe UI", 10))
        self.campo_OP.setFixedWidth(300)
        self.campo_OP.setPlaceholderText("Digite o número da OP...")
        self.add_clear_button(self.campo_OP)

        self.btn_consultar = QPushButton("Pesquisar", self)
        self.btn_consultar.clicked.connect(self.executar_consulta)
        self.btn_consultar.setMinimumWidth(100)

        self.btn_exportar_excel = QPushButton("Exportar Excel", self)
        self.btn_exportar_excel.clicked.connect(self.exportar_excel)
        self.btn_exportar_excel.setMinimumWidth(100)
        self.btn_exportar_excel.setEnabled(False)

        self.btn_fechar = QPushButton("Fechar", self)
        self.btn_fechar.clicked.connect(self.fechar_janela)
        self.btn_fechar.setMinimumWidth(100)

        self.campo_codigo.returnPressed.connect(self.executar_consulta)
        self.campo_qp.returnPressed.connect(self.executar_consulta)
        self.campo_OP.returnPressed.connect(self.executar_consulta)

        layout = QVBoxLayout()
        #layout_linha_01 = QHBoxLayout()
        layout_linha_02 = QHBoxLayout()
        layout_linha_03 = QHBoxLayout()

        layout_linha_02.addWidget(self.campo_codigo)
        layout_linha_02.addWidget(self.campo_qp)
        layout_linha_02.addWidget(self.campo_OP)
        layout_linha_02.addStretch()

        layout_linha_03.addWidget(self.btn_consultar)
        layout_linha_03.addWidget(self.btn_exportar_excel)
        layout_linha_03.addWidget(self.btn_fechar)
        layout_linha_03.addStretch()

        #layout.addLayout(layout_linha_01)
        layout.addLayout(layout_linha_02)
        layout.addLayout(layout_linha_03)
        layout.addWidget(self.tree)
        self.setLayout(layout)

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
                                                   f'{self.campo_codigo.text().upper().strip()}_MP.xlsx',
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
        fonte_tabela = QFont("Segoe UI", 10)
        self.tree.setFont(fonte_tabela)
        altura_linha = 40
        self.tree.verticalHeader().setDefaultSectionSize(altura_linha)
        self.tree.horizontalHeader().sectionClicked.connect(self.ordenar_tabela)
        self.tree.horizontalHeader().setStretchLastSection(True)

    def copiar_linha(self, item):
        if item is not None:
            valor_campo = item.text()
            pyperclip.copy(str(valor_campo))

    def ordenar_tabela(self, logicalIndex):
        # Obter o índice real da coluna (considerando a ordem de classificação)
        index = self.tree.horizontalHeader().sortIndicatorOrder()

        # Definir a ordem de classificação
        order = Qt.AscendingOrder if index == 0 else Qt.DescendingOrder

        # Ordenar a tabela pela coluna clicada
        self.tree.sortItems(logicalIndex, order)

    def limpar_campos(self):
        self.campo_codigo.clear()

    def bloquear_campos_pesquisa(self):
        self.campo_codigo.setEnabled(False)
        self.btn_consultar.setEnabled(False)
        self.btn_exportar_excel.setEnabled(False)

    def desbloquear_campos_pesquisa(self):
        self.campo_codigo.setEnabled(True)
        self.btn_consultar.setEnabled(True)
        self.btn_exportar_excel.setEnabled(True)

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

    def selecionar_query_conforme_filtro(self):
        codigo_produto = self.campo_codigo.text().upper().strip()
        numero_QP = self.campo_qp.text().upper().strip()
        numero_OP = self.campo_OP.text().upper().strip()

        if codigo_produto == '' and numero_QP == '' and numero_OP == '':
            self.btn_consultar.setEnabled(False)
            self.exibir_mensagem("ATENÇÃO!",
                                 "Os campos de pesquisa estão vazios.\nPreencha algum campo e tente "
                                 "novamente.\n\nツ\n\nSMARTPLIC®",
                                 "info")
            return True

        query = f"""
            SELECT C2_ZZNUMQP AS "NUM. QP", C2_NUM AS "NUM. OP", C2_PRODUTO AS "CÓDIGO",
            B1_DESC AS "DESCRIÇÃO", C2_QUANT AS "QUANT.", C2_UM AS "UNID. MED.", 
            C2_REVISAO AS "REV.", C2_SEQUEN AS "SEQ.", C2_DATPRI AS "DT. PREV. INÍCIO", C2_DATPRF AS "DT. PREV. ENTREGA", 
            C2_EMISSAO AS "DT. EMISSÃO OP", C2_DATRF AS "DT. REAL. FIM", C2_OBS AS "OBSERVAÇÃO",
            C2_QUJE AS "QTD. PRODUZIDA", C2_APRATU1 AS "VALOR APROP. ESTOQUE", C2_AGLUT AS "OP AGLUTINADA", C2_XMAQUIN AS "ABERTO POR:"
            FROM PROTHEUS12_R27.dbo.SC2010 op
            INNER JOIN SB1010 prod ON C2_PRODUTO = B1_COD
            WHERE C2_ZZNUMQP LIKE '%{numero_QP}'
            AND C2_PRODUTO LIKE '{codigo_produto}%'
            AND C2_NUM LIKE '{numero_OP}%'
            AND op.D_E_L_E_T_ <> '*'
            ORDER BY op.R_E_C_N_O_ DESC;
        """
        return query

    def executar_consulta(self):
        select_query = self.selecionar_query_conforme_filtro()
        
        if isinstance(select_query, bool) and select_query:
            self.btn_consultar.setEnabled(True)
            return
        
        self.bloquear_campos_pesquisa()

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe = pd.read_sql(select_query, engine)

            dataframe[''] = ''

            self.configurar_tabela(dataframe)

            self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
            self.tree.setRowCount(0)

            for i, row in dataframe.iterrows():
                self.tree.setSortingEnabled(False)
                self.tree.insertRow(i)
                for j, value in enumerate(row):
                    if j >= 8 and j <= 11 and not value.isspace():
                        data_obj = datetime.strptime(value, "%Y%m%d")
                        value = data_obj.strftime("%d/%m/%Y")

                    item = QTableWidgetItem(str(value).strip())

                    if j != 2 and j != 3:
                        item.setTextAlignment(Qt.AlignCenter)

                    self.tree.setItem(i, j, item)

                QCoreApplication.processEvents()

            self.tree.setSortingEnabled(True)
            self.desbloquear_campos_pesquisa()

        except pyodbc.Error as ex:
            self.exibir_mensagem('Erro ao consultar tabela', f'Erro: {str(ex)}', 'error')

        finally:
            # Fecha a conexão com o banco de dados se estiver aberta
            if 'engine' in locals():
                engine.dispose()

    def fechar_janela(self):
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PcpApp()
    username, password, database, server = PcpApp().setup_mssql()
    driver = '{SQL Server}'

    window.showMaximized()
    sys.exit(app.exec_())
