import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QStyle, QAction, QDateEdit, QLabel
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtCore import Qt, QCoreApplication, QDate
import pyperclip
import pandas as pd
import ctypes
from datetime import date, datetime
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
import os


class ComprasApp(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = None
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
                font-size: 12px;
                padding: 5px;
                font-weight: bold;
            }
            
            QDateEdit {
                background-color: #FFFFFF;
                border: 1px solid #262626;
                margin-top: 20px;
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
                margin-top: 20px;
                margin-bottom: 20px;
                padding: 5px 10px;
                border-radius: 10px;
                height: 24px;
                font-size: 16px;
            }

            QPushButton {
                background-color: #52D3D8;
                color: #EEEEEE;
                padding: 10px;
                border: 2px;
                border-radius: 8px;
                font-size: 12px;
                height: 15px;
                font-weight: bold;
                margin-bottom: 8px;
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

        self.campo_codigo = QLineEdit(self)
        self.campo_codigo.setFont(QFont("Segoe UI", 10))
        self.campo_codigo.setFixedWidth(200)
        self.campo_codigo.setPlaceholderText("Código produto...")
        self.add_clear_button(self.campo_codigo)

        self.campo_qp = QLineEdit(self)
        self.campo_qp.setFont(QFont("Segoe UI", 10))
        self.campo_qp.setFixedWidth(200)
        self.campo_qp.setPlaceholderText("Número QP...")
        self.add_clear_button(self.campo_qp)

        self.campo_OP = QLineEdit(self)
        self.campo_OP.setFont(QFont("Segoe UI", 10))
        self.campo_OP.setFixedWidth(200)
        self.campo_OP.setPlaceholderText("Número OP...")
        self.add_clear_button(self.campo_OP)

        self.campo_data_inicio = QDateEdit(self)
        self.campo_data_inicio.setFont(QFont("Segoe UI", 10))
        self.campo_data_inicio.setFixedWidth(150)
        self.campo_data_inicio.setCalendarPopup(True)
        self.campo_data_inicio.setDisplayFormat("dd/MM/yyyy")

        data_atual = QDate.currentDate()
        meses_a_remover = 2
        data_inicio = data_atual.addMonths(-meses_a_remover)
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

        self.campo_codigo.returnPressed.connect(self.executar_consulta)
        self.campo_qp.returnPressed.connect(self.executar_consulta)
        self.campo_OP.returnPressed.connect(self.executar_consulta)

        layout = QVBoxLayout()
        #layout_linha_01 = QHBoxLayout()
        layout_linha_02 = QHBoxLayout()
        self.layout_linha_03 = QHBoxLayout()

        layout_linha_02.addWidget(self.campo_codigo)
        layout_linha_02.addWidget(self.campo_qp)
        layout_linha_02.addWidget(self.campo_OP)
        layout_linha_02.addWidget(QLabel("Dt. Emissão Inicial:"))
        layout_linha_02.addWidget(self.campo_data_inicio)
        layout_linha_02.addWidget(QLabel("Dt. Emissão Final:"))
        layout_linha_02.addWidget(self.campo_data_fim)
        layout_linha_02.addStretch()

        self.layout_linha_03.addWidget(self.btn_consultar)
        self.layout_linha_03.addWidget(self.btn_nova_janela)
        self.layout_linha_03.addWidget(self.btn_exportar_excel)
        self.layout_linha_03.addWidget(self.btn_fechar)
        self.layout_linha_03.addStretch()

        #layout.addLayout(layout_linha_01)
        layout.addLayout(layout_linha_02)
        layout.addLayout(self.layout_linha_03)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def abrir_nova_janela(self):
        if not self.nova_janela or not self.nova_janela.isVisible():
            self.nova_janela = ComprasApp()
            self.nova_janela.setGeometry(self.x() + 50, self.y() + 50, self.width(), self.height())
            self.nova_janela.show()

    def add_today_button(self, date_edit):
        calendar = date_edit.calendarWidget()
        calendar.setGeometry(10, 10, 600, 400)
        btn_today = QPushButton("Hoje", calendar)
        pos_x = 20
        pos_y = 5
        largura = 50
        altura = 20
        btn_today.setGeometry(pos_x, pos_y, largura, altura)
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

    def bloquear_campos(self):
        self.campo_codigo.setEnabled(False)
        self.btn_consultar.setEnabled(False)
        self.btn_exportar_excel.setEnabled(False)

    def desbloquear_campos(self):
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

    def selecionar_query_conforme_filtro(self, codigo_produto, numero_qp, numero_op):

        data_inicio_formatada = self.campo_data_inicio.date().toString("yyyyMMdd")
        data_fim_formatada = self.campo_data_fim.date().toString("yyyyMMdd")

        filtro_data = f"AND C1_EMISSAO >= '{data_inicio_formatada}' AND C1_EMISSAO <= '{data_fim_formatada}'" if data_fim_formatada != '' and data_fim_formatada != '' else ''

        query = f"""
            SELECT C1_ZZNUMQP AS "QP", C1_OP AS "OP", C1_NUM "N°. SC", C1_ITEM AS "Item", C1_CODORCA AS "Orçamento",
                C1_PEDIDO AS "N°. Pedido", C1_ITEMPED AS "Item Pedido", C1_PRODUTO AS "Código", 
                C1_DESCRI AS "Descrição", C1_UM AS "UM", C1_QUANT AS "Quant.", C1_QUJE AS "Quant. Pedido",
                C1_EMISSAO AS "Emissão", C1_DATPRF AS "Necessidade", C1_ORIGEM AS "Origem", C1_OBS AS "OBS.",
                C1_LOCAL AS "Armazém", C1_IMPORT AS "Importado?", C1_COTACAO AS "Tem cotação?", C1_FORNECE AS "Fornecedor",
                C1_SOLICIT AS "Solicitante", C1_XSOL AS "Requisitante", C1_TIPOEMP AS "Tipo Empenho"
            FROM PROTHEUS12_R27.dbo.SC1010
                WHERE C1_ZZNUMQP LIKE '%{numero_qp}'
                AND C1_PRODUTO LIKE '{codigo_produto}%'
                AND C1_OP LIKE '%{numero_op}%' {filtro_data}
            ORDER BY R_E_C_N_O_ DESC;
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

    def executar_consulta(self):

        numero_qp = self.campo_qp.text().upper().strip()
        numero_op = self.campo_OP.text().upper().strip()
        codigo_produto = self.campo_codigo.text().upper().strip()

        if self.validar_campos(codigo_produto, numero_qp, numero_op):
            self.btn_consultar.setEnabled(True)
            return

        numero_qp = numero_qp.zfill(6) if numero_qp != '' else numero_qp

        select_query = self.selecionar_query_conforme_filtro(codigo_produto, numero_qp, numero_op)

        if isinstance(select_query, bool) and select_query:
            self.btn_consultar.setEnabled(True)
            return

        self.bloquear_campos()

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe = pd.read_sql(select_query, self.engine)

            if not dataframe.empty:
                self.layout_linha_03.addWidget(self.btn_parar_consulta)
                dataframe.insert(0, 'Status', '')
                dataframe[''] = ''

                self.configurar_tabela(dataframe)

                self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
                self.tree.setRowCount(0)
            else:
                self.exibir_mensagem("EUREKA® Compras", 'Nada encontrado!', "info")
                self.desbloquear_campos()
                return

            # Construir caminhos relativos
            script_dir = os.path.dirname(os.path.abspath(__file__))
            open_icon_path = os.path.join(script_dir, '..', 'resources', 'images', 'open_status_panel.png')
            closed_icon_path = os.path.join(script_dir, '..', 'resources', 'images', 'close_status_panel.png')

            open_solic = QIcon(open_icon_path)
            closed_solic = QIcon(closed_icon_path)

            for i, row in dataframe.iterrows():
                if self.interromper_consulta_sql:
                    break

                self.tree.setSortingEnabled(False)
                self.tree.insertRow(i)
                for j, value in enumerate(row):
                    if j == 0:
                        item = QTableWidgetItem()
                        if row['N°. Pedido'].strip() == '' and row['Origem'].strip() == '':
                            item.setIcon(open_solic)
                        elif row['N°. Pedido'].strip() != '' and row['Origem'].strip() == '':
                            item.setIcon(closed_solic)
                        elif row['Origem'].strip() == 'MATA650':
                            item.setIcon(closed_solic)
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        if j == 15 and value.strip() == 'MATA650':
                            value = 'OP INTERNA'
                        elif j == 15 and value.strip() == '':
                            value = 'COMERCIAL'

                        if j == 18 and value.strip() == 'N':
                            value = 'Não'
                        elif j == 18 and value.strip() == '':
                            value = 'Sim'

                        if j in (13, 14) and not value.isspace():
                            data_obj = datetime.strptime(value, "%Y%m%d")
                            value = data_obj.strftime("%d/%m/%Y")

                        item = QTableWidgetItem(str(value).strip())

                        if j not in (8, 9):
                            item.setTextAlignment(Qt.AlignCenter)

                    self.tree.setItem(i, j, item)

                QCoreApplication.processEvents()

            self.layout_linha_03.removeWidget(self.btn_parar_consulta)
            self.btn_parar_consulta.setParent(None)
            self.tree.setSortingEnabled(True)
            self.desbloquear_campos()

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
        self.desbloquear_campos()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ComprasApp()
    username, password, database, server = ComprasApp().setup_mssql()
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