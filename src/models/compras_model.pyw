import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QStyle, QAction, QDateEdit, QLabel
from PyQt5.QtGui import QFont, QIcon
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
                margin-bottom: 20px;
                padding: 5px 10px;
                border-radius: 10px;
                height: 24px;
                font-size: 16px;
            }

            QPushButton {
                background-color: #00ADB5;
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

        fonte_campos = "Segoe UI"
        tamanho_fonte_campos = 10

        self.label_sc = QLabel("Solicitação:", self)
        self.label_sc.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.label_pedido = QLabel("Pedido:", self)
        self.label_pedido.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.label_codigo = QLabel("Código:", self)
        self.label_codigo.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.label_qp = QLabel("QP:", self)
        self.label_qp.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.label_OP = QLabel("OP:", self)
        self.label_OP.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.label_data_inicio = QLabel("Dt. Emissão Inicial:", self)
        self.label_data_inicio.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.label_data_fim = QLabel("Dt. Emissão Final:", self)
        self.label_data_fim.setFont(QFont(fonte_campos, tamanho_fonte_campos))

        self.campo_sc = QLineEdit(self)
        self.campo_sc.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_sc.setMaxLength(6)
        self.campo_sc.setFocus()
        self.campo_sc.setFixedWidth(200)
        self.campo_sc.setPlaceholderText("Número SC...")
        self.add_clear_button(self.campo_sc)

        self.campo_pedido = QLineEdit(self)
        self.campo_pedido.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_pedido.setMaxLength(6)
        self.campo_pedido.setFocus()
        self.campo_pedido.setFixedWidth(200)
        self.campo_pedido.setPlaceholderText("Número Pedido...")
        self.add_clear_button(self.campo_pedido)

        self.campo_codigo = QLineEdit(self)
        self.campo_codigo.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_codigo.setMaxLength(13)
        self.campo_codigo.setFixedWidth(200)
        self.campo_codigo.setPlaceholderText("Código produto...")
        self.add_clear_button(self.campo_codigo)

        self.campo_qp = QLineEdit(self)
        self.campo_qp.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_qp.setMaxLength(6)
        self.campo_qp.setFixedWidth(200)
        self.campo_qp.setPlaceholderText("Número QP...")
        self.add_clear_button(self.campo_qp)

        self.campo_OP = QLineEdit(self)
        self.campo_OP.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_OP.setMaxLength(6)
        self.campo_OP.setFixedWidth(200)
        self.campo_OP.setPlaceholderText("Número OP...")
        self.add_clear_button(self.campo_OP)

        self.campo_data_inicio = QDateEdit(self)
        self.campo_data_inicio.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_data_inicio.setFixedWidth(150)
        self.campo_data_inicio.setCalendarPopup(True)
        self.campo_data_inicio.setDisplayFormat("dd/MM/yyyy")

        data_atual = QDate.currentDate()
        meses_a_remover = 4
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

        self.campo_sc.returnPressed.connect(self.executar_consulta)
        self.campo_codigo.returnPressed.connect(self.executar_consulta)
        self.campo_qp.returnPressed.connect(self.executar_consulta)
        self.campo_OP.returnPressed.connect(self.executar_consulta)

        layout = QVBoxLayout()
        layout_linha_01 = QHBoxLayout()
        self.layout_linha_02 = QHBoxLayout()

        container_sc = QVBoxLayout()
        container_sc.addWidget(self.label_sc)
        container_sc.addWidget(self.campo_sc)

        container_pedido = QVBoxLayout()
        container_pedido.addWidget(self.label_pedido)
        container_pedido.addWidget(self.campo_pedido)

        container_codigo = QVBoxLayout()
        container_codigo.addWidget(self.label_codigo)
        container_codigo.addWidget(self.campo_codigo)

        container_qp = QVBoxLayout()
        container_qp.addWidget(self.label_qp)
        container_qp.addWidget(self.campo_qp)

        container_op = QVBoxLayout()
        container_op.addWidget(self.label_OP)
        container_op.addWidget(self.campo_OP)

        container_data_ini = QVBoxLayout()
        container_data_ini.addWidget(self.label_data_inicio)
        container_data_ini.addWidget(self.campo_data_inicio)

        container_data_fim = QVBoxLayout()
        container_data_fim.addWidget(self.label_data_fim)
        container_data_fim.addWidget(self.campo_data_fim)

        layout_linha_01.addLayout(container_sc)
        layout_linha_01.addLayout(container_pedido)
        layout_linha_01.addLayout(container_codigo)
        layout_linha_01.addLayout(container_qp)
        layout_linha_01.addLayout(container_op)
        layout_linha_01.addLayout(container_data_ini)
        layout_linha_01.addLayout(container_data_fim)
        layout_linha_01.addStretch()

        self.layout_linha_02.addWidget(self.btn_consultar)
        self.layout_linha_02.addWidget(self.btn_nova_janela)
        self.layout_linha_02.addWidget(self.btn_exportar_excel)
        self.layout_linha_02.addWidget(self.btn_fechar)
        self.layout_linha_02.addStretch()

        layout.addLayout(layout_linha_01)
        layout.addLayout(self.layout_linha_02)
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
        largura, altura = 50, 20
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

    def controle_campos_formulario(self, status):
        self.campo_sc.setEnabled(status)
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

    def selecionar_query_conforme_filtro(self, numero_sc, numero_pedido, codigo_produto, numero_qp, numero_op):

        data_inicio_formatada = self.campo_data_inicio.date().toString("yyyyMMdd")
        data_fim_formatada = self.campo_data_fim.date().toString("yyyyMMdd")

        if data_fim_formatada != '' and data_fim_formatada != '':
            filtro_data = f"AND C1_EMISSAO >= '{data_inicio_formatada}' AND C1_EMISSAO <= '{data_fim_formatada}'"
        else:
            filtro_data = ''

        query = f"""
            SELECT C1_ZZNUMQP AS "QP", C1_OP AS "OP", C1_NUM "N°. SC", C1_ITEM AS "Item",
                C1_PEDIDO AS "N°. Pedido", C1_ITEMPED AS "Item Pedido", C1_PRODUTO AS "Código", 
                C1_DESCRI AS "Descrição", C1_UM AS "UM", C1_QUANT AS "Quant.", C1_QUJE AS "Quant. Pedido",
                C1_EMISSAO AS "Emissão", C1_DATPRF AS "Necessidade", C1_ORIGEM AS "Origem", C1_OBS AS "OBS.",
                C1_LOCAL AS "Armazém", C1_IMPORT AS "Importado?", C1_FORNECE AS "Fornecedor",
                C1_SOLICIT AS "Solicitante", C1_XSOL AS "Requisitante"
            FROM PROTHEUS12_R27.dbo.SC1010
                WHERE C1_PEDIDO LIKE '{numero_pedido}%'
                AND C1_NUM LIKE '%{numero_sc}'
                AND C1_ZZNUMQP LIKE '%{numero_qp}'
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

        numero_sc = self.campo_sc.text().upper().strip()
        numero_pedido = self.campo_pedido.text().upper().strip()
        numero_qp = self.campo_qp.text().upper().strip()
        numero_op = self.campo_OP.text().upper().strip()
        codigo_produto = self.campo_codigo.text().upper().strip()

        if self.validar_campos(codigo_produto, numero_qp, numero_op):
            self.btn_consultar.setEnabled(True)
            return

        numero_qp = numero_qp.zfill(6) if numero_qp != '' else numero_qp

        select_query = self.selecionar_query_conforme_filtro(numero_sc, numero_pedido, codigo_produto, numero_qp, numero_op)

        self.controle_campos_formulario(False)

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe = pd.read_sql(select_query, self.engine)

            if not dataframe.empty:
                self.layout_linha_02.addWidget(self.btn_parar_consulta)
                dataframe.insert(0, 'Status', '')
                dataframe[''] = ''

                self.configurar_tabela(dataframe)

                self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
                self.tree.setRowCount(0)
            else:
                self.exibir_mensagem("EUREKA® Compras", 'Nada encontrado!', "info")
                self.controle_campos_formulario(True)
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
                        if j == 14 and value.strip() == 'MATA650':
                            value = 'Empenho'
                        elif j == 14 and value.strip() == '':
                            value = 'Compras'

                        if j == 17 and value.strip() == 'N':
                            value = 'Não'
                        elif j == 17 and value.strip() == '':
                            value = 'Sim'

                        if j in (12, 13) and not value.isspace():
                            data_obj = datetime.strptime(value, "%Y%m%d")
                            value = data_obj.strftime("%d/%m/%Y")

                        item = QTableWidgetItem(str(value).strip())

                        if j not in (7, 8):
                            item.setTextAlignment(Qt.AlignCenter)

                    self.tree.setItem(i, j, item)

                QCoreApplication.processEvents()

            self.layout_linha_02.removeWidget(self.btn_parar_consulta)
            self.btn_parar_consulta.setParent(None)
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
