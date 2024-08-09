import ctypes
import locale
import os
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import pyperclip
import sys
from PyQt5.QtCore import Qt, QProcess, pyqtSignal, QDate, QCoreApplication, QEvent
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QStyle, QAction, QLabel, QSizePolicy, QTabWidget, QMenu, QFrame, \
    QCalendarWidget
from sqlalchemy import create_engine, text


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


class QpClosedApp(QWidget):
    guia_fechada = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("EUREKA® PCP - v2.0")
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

        self.engine = None
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
                font-size: 30px;
                font-weight: bold;
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
                background-color: #EB5B00;
                color: #EEEEEE;
                padding: 10px;
                border: 2px;
                border-radius: 8px;
                font-size: 12px;
                height: 20px;
                font-weight: bold;
                margin: 10px 5px;
            }
            
            QPushButton#btn_qps_finalizadas {
                background-color: #C5EBAA;
                color: #294B29;
            }
            
            QPushButton#btn_qps_abertas {
                background-color: #FFC94A;
                color: #3E3232;
            }

            QPushButton:hover, QPushButton:hover#btn_qps_finalizadas, QPushButton:hover#btn_qps_abertas {
                background-color: #E84545;
                color: #fff
            }
    
            QPushButton:pressed, QPushButton:pressed#btn_qps_finalizadas, QPushButton:pressed#btn_qps_abertas {
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
                margin-bottom: 3px;
            }
        """)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_enaplic_path = os.path.join(script_dir, '..', 'resources', 'images', 'LOGO.jpeg')
        self.logo_label = QLabel(self)
        self.logo_label.setObjectName('logo-enaplic')
        pixmap_logo = QPixmap(logo_enaplic_path).scaledToWidth(50)
        self.logo_label.setPixmap(pixmap_logo)
        self.logo_label.setAlignment(Qt.AlignRight)

        self.label_title = QLabel("CONSULTA DE QP", self)
        self.label_title.setObjectName('label-title')

        self.line = QFrame(self)
        self.line.setObjectName('line')
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.label_descricao_prod = QLabel("Descrição:", self)
        self.label_contem_descricao_prod = QLabel("Contém na descrição:", self)
        self.label_contem_descricao_prod.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.label_qp = QLabel("QP:", self)
        self.label_line_number = QLabel("", self)
        self.label_line_number.setVisible(False)

        self.campo_descricao_prod = QLineEdit(self)
        self.campo_descricao_prod.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_descricao_prod.setMaxLength(60)
        self.campo_descricao_prod.setFixedWidth(400)
        self.add_clear_button(self.campo_descricao_prod)

        self.campo_contem_descricao_prod = QLineEdit(self)
        self.campo_contem_descricao_prod.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_contem_descricao_prod.setMaxLength(60)
        self.campo_contem_descricao_prod.setFixedWidth(400)
        self.add_clear_button(self.campo_contem_descricao_prod)

        self.campo_qp = QLineEdit(self)
        self.campo_qp.setFont(QFont(fonte_campos, tamanho_fonte_campos))
        self.campo_qp.setMaxLength(6)
        self.campo_qp.setFixedWidth(110)
        self.add_clear_button(self.campo_qp)

        self.btn_qps_finalizadas = QPushButton("QPS CONCLUÍDAS", self)
        self.btn_qps_finalizadas.clicked.connect(self.consultar_qps_finalizadas)
        self.btn_qps_finalizadas.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.btn_qps_finalizadas.setObjectName("btn_qps_finalizadas")
        
        self.btn_qps_abertas = QPushButton("QPS ABERTAS", self)
        self.btn_qps_abertas.clicked.connect(self.consultar_qps_abertas)
        self.btn_qps_abertas.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.btn_qps_abertas.setObjectName("btn_qps_abertas")

        self.btn_limpar = QPushButton("Limpar", self)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_limpar.setFixedWidth(110)

        self.btn_fechar = QPushButton("Fechar", self)
        self.btn_fechar.clicked.connect(self.fechar_janela)
        self.btn_fechar.setFixedWidth(110)

        self.campo_qp.returnPressed.connect(self.consultar_qps_finalizadas)
        self.campo_descricao_prod.returnPressed.connect(self.consultar_qps_finalizadas)
        self.campo_contem_descricao_prod.returnPressed.connect(self.consultar_qps_finalizadas)

        layout = QVBoxLayout()
        layout_title = QHBoxLayout()
        layout_campos_01 = QHBoxLayout()
        self.layout_buttons = QHBoxLayout()
        self.layout_footer_label = QHBoxLayout()

        layout_title.addStretch(1)
        layout_title.addWidget(self.logo_label)
        layout_title.addWidget(self.label_title)
        layout_title.addStretch(1)

        container_descricao_prod = QVBoxLayout()
        container_descricao_prod.addWidget(self.label_descricao_prod)
        container_descricao_prod.addWidget(self.campo_descricao_prod)

        container_contem_descricao_prod = QVBoxLayout()
        container_contem_descricao_prod.addWidget(self.label_contem_descricao_prod)
        container_contem_descricao_prod.addWidget(self.campo_contem_descricao_prod)

        container_qp = QVBoxLayout()
        container_qp.addWidget(self.label_qp)
        container_qp.addWidget(self.campo_qp)

        layout_campos_01.addLayout(container_qp)
        layout_campos_01.addLayout(container_descricao_prod)
        layout_campos_01.addLayout(container_contem_descricao_prod)
        layout_campos_01.addStretch()

        self.layout_buttons.addWidget(self.btn_qps_finalizadas)
        self.layout_buttons.addWidget(self.btn_qps_abertas)
        self.layout_buttons.addWidget(self.btn_limpar)
        self.layout_buttons.addWidget(self.btn_fechar)
        self.layout_buttons.addStretch()

        self.layout_footer_label.addStretch(1)
        self.layout_footer_label.addWidget(self.label_line_number)
        self.layout_footer_label.addStretch(1)

        layout.addLayout(layout_title)
        layout.addWidget(self.line)
        layout.addLayout(layout_campos_01)
        layout.addLayout(self.layout_buttons)
        layout.addWidget(self.tree)
        layout.addLayout(self.layout_footer_label)
        self.setLayout(layout)

        self.calendar = QCalendarWidget(self)
        self.calendar.setFixedSize(350, 200)
        self.calendar.setGridVisible(True)
        self.calendar.hide()
        self.calendar.clicked.connect(self.date_selected)

        self.tree.cellDoubleClicked.connect(self.cell_clicked_open_calendar)
        self.selected_row = None
        self.selected_column = None
        self.tree.installEventFilter(self)
        self.installEventFilter(self)

    def show_context_menu(self, position, table):
        indexes = table.selectedIndexes()
        if indexes:
            # Obtém o índice do item clicado
            index = table.indexAt(position)
            if not index.isValid():
                return
            # Seleciona a linha inteira
            table.selectRow(index.row())
            menu = QMenu()
            context_menu_nova_janela = QAction('Nova janela', self)
            context_menu_nova_janela.triggered.connect(lambda: self.abrir_nova_janela())
            menu.addAction(context_menu_nova_janela)
            menu.exec_(table.viewport().mapToGlobal(position))

    def limpar_campos(self):
        self.campo_qp.clear()
        self.campo_descricao_prod.clear()
        self.campo_contem_descricao_prod.clear()
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)
        self.label_line_number.hide()

    def abrir_nova_janela(self):
        if not self.nova_janela or not self.nova_janela.isVisible():
            self.nova_janela = QpClosedApp()
            self.nova_janela.setGeometry(self.x() + 50, self.y() + 50, self.width(), self.height())
            self.nova_janela.show()

    def add_clear_button(self, line_edit):
        clear_icon = self.style().standardIcon(QStyle.SP_LineEditClearButton)
        pixmap = clear_icon.pixmap(40, 40)  # Redimensionar o ícone para 20x20 pixels
        larger_clear_icon = QIcon(pixmap)
        clear_action = QAction(larger_clear_icon, "Clear", line_edit)
        clear_action.triggered.connect(line_edit.clear)
        line_edit.addAction(clear_action, QLineEdit.TrailingPosition)

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
        self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.tree.horizontalHeader().sectionClicked.connect(self.ordenar_tabela)
        self.tree.horizontalHeader().setStretchLastSection(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, self.tree))

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
        self.campo_qp.setEnabled(status)

    def fechar_janela(self):
        self.close()

    def query_consulta_qps_finalizadas(self):
        numero_qp = self.campo_qp.text().upper().strip()
        descricao = self.campo_descricao_prod.text().upper().strip()
        contem_descricao = self.campo_contem_descricao_prod.text().upper().strip()

        palavras_contem_descricao = contem_descricao.split('*')
        clausulas_contem_descricao = " AND ".join(
            [f"des_qp LIKE '%{palavra}%'" for palavra in palavras_contem_descricao])

        query = f"""
            SELECT
                cod_qp AS "QP",
                des_qp AS "NOME DO PROJETO",
                dt_open_qp AS "DATA DE EMISSÃO",
                dt_end_qp AS "PRAZO DE ENTREGA",
                dt_completed_qp AS "DATA DE CONCLUSÃO",
                vl_delay AS "DIAS EM ATRASO",
                status_delivery AS "STATUS ENTREGA"
            FROM 
                enaplic_management.dbo.tb_end_qps
            WHERE 
                cod_qp LIKE '%{numero_qp}'
                AND des_qp LIKE '{descricao}%'
                AND {clausulas_contem_descricao}
                ORDER BY id DESC
            """

        return query
    
    def query_consulta_qps_abertas(self):
        numero_qp = self.campo_qp.text().upper().strip()
        descricao = self.campo_descricao_prod.text().upper().strip()
        contem_descricao = self.campo_contem_descricao_prod.text().upper().strip()

        palavras_contem_descricao = contem_descricao.split('*')
        clausulas_contem_descricao = " AND ".join(
            [f"des_qp LIKE '%{palavra}%'" for palavra in palavras_contem_descricao])

        query = f"""
            SELECT
                cod_qp AS "QP",
                des_qp AS "NOME DO PROJETO",
                dt_open_qp AS "DATA DE EMISSÃO",
                dt_end_qp AS "PRAZO DE ENTREGA"
            FROM 
                enaplic_management.dbo.tb_open_qps
            WHERE 
                cod_qp LIKE '%{numero_qp}'
                AND des_qp LIKE '{descricao}%'
                AND {clausulas_contem_descricao}
                ORDER BY id DESC
            """

        return query

    def consultar_qps_finalizadas(self):
        query = self.query_consulta_qps_finalizadas()
        line_number = f"""
            SELECT
                COUNT(*) AS count
            FROM ({query.replace("ORDER BY id DESC", "")}) AS results
        """

        conn_str = f'DRIVER={driver};SERVER={server};UID={username};PWD={password}'
        self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe_line_number = pd.read_sql(line_number, self.engine)
            line_number = dataframe_line_number.iloc[0, 0]

            if line_number >= 1:
                if line_number > 1:
                    message = f"Foram encontrados {line_number} resultados"
                else:
                    message = f"Foi encontrado {line_number} resultado"

                self.label_line_number.setText(f"{message}")
                self.label_line_number.show()

            else:
                exibir_mensagem("EUREKA® PCP", 'Nenhuma QP encontrada!', "info")
                self.controle_campos_formulario(True)
                return

            dataframe = pd.read_sql(query, self.engine)
            dataframe.insert(0, '', '')
            dataframe[''] = ''

            self.configurar_tabela(dataframe)
            self.tree.setRowCount(0)

            # Construir caminhos relativos
            script_dir = os.path.dirname(os.path.abspath(__file__))
            open_icon_path = os.path.join(script_dir, '..', 'resources', 'images', 'red.png')
            closed_icon_path = os.path.join(script_dir, '..', 'resources', 'images', 'green.png')

            open_icon = QIcon(open_icon_path)
            closed_icon = QIcon(closed_icon_path)

            for i, row in dataframe.iterrows():

                self.tree.setSortingEnabled(False)
                self.tree.insertRow(i)
                for j, value in enumerate(row):
                    if value is not None:
                        if j == 0:
                            item = QTableWidgetItem()
                            if row['DATA DE CONCLUSÃO'] in (None, ''):
                                item.setIcon(open_icon)
                            else:
                                item.setIcon(closed_icon)
                            item.setTextAlignment(Qt.AlignCenter)
                        else:
                            item = QTableWidgetItem(str(value).strip())
                            if j != 2:
                                item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item = QTableWidgetItem('')

                    self.tree.setItem(i, j, item)

            self.tree.setSortingEnabled(True)
            self.controle_campos_formulario(True)

        except Exception as ex:
            exibir_mensagem('Erro ao consultar tabela', f'Erro: {str(ex)}', 'error')

        finally:
            # Fecha a conexão com o banco de dados se estiver aberta
            if hasattr(self, 'engine'):
                self.engine.dispose()
                self.engine = None
                
    def consultar_qps_abertas(self):
        query = self.query_consulta_qps_abertas()
        line_number = f"""
            SELECT
                COUNT(*) AS count
            FROM ({query.replace("ORDER BY id DESC", "")}) AS results
        """

        conn_str = f'DRIVER={driver};SERVER={server};UID={username};PWD={password}'
        self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe_line_number = pd.read_sql(line_number, self.engine)
            line_number = dataframe_line_number.iloc[0, 0]

            if line_number >= 1:
                if line_number > 1:
                    message = f"Foram encontrados {line_number} resultados"
                else:
                    message = f"Foi encontrado {line_number} resultado"

                self.label_line_number.setText(f"{message}")
                self.label_line_number.show()

            else:
                exibir_mensagem("EUREKA® PCP", 'Nenhuma QP encontrada!', "info")
                self.controle_campos_formulario(True)
                return

            dataframe = pd.read_sql(query, self.engine)
            dataframe[''] = ''

            self.configurar_tabela(dataframe)
            self.tree.setRowCount(0)

            for i, row in dataframe.iterrows():

                self.tree.setSortingEnabled(False)
                self.tree.insertRow(i)
                for j, value in enumerate(row):
                    if value is not None:
                        item = QTableWidgetItem(str(value).strip())
                        if j != 1:
                            item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item = QTableWidgetItem('')

                    self.tree.setItem(i, j, item)

            self.tree.setSortingEnabled(True)
            self.controle_campos_formulario(True)

        except Exception as ex:
            exibir_mensagem('Erro ao consultar tabela', f'Erro: {str(ex)}', 'error')

        finally:
            # Fecha a conexão com o banco de dados se estiver aberta
            if hasattr(self, 'engine'):
                self.engine.dispose()
                self.engine = None

    def cell_clicked_open_calendar(self, row, column):
        if self.tree.horizontalHeaderItem(column).text() == "DATA DE CONCLUSÃO":
            self.selected_row = row
            self.selected_column = column
            self.calendar.setGeometry(self.tree.visualItemRect(self.tree.item(row, column)))
            self.calendar.show()
        else:
            self.calendar.hide()

    def date_selected(self, date):
        if self.selected_row is not None:
            date_str = date.toString("dd/MM/yyyy")
            cod_qp = self.tree.item(self.selected_row, 1).text()  # Assuming QP is in the second column

            update_query = text("""
                UPDATE enaplic_management.dbo.tb_end_qps
                SET dt_completed_qp = :selected_date
                WHERE cod_qp = :cod_qp
            """)

            try:
                conn_str = f'DRIVER={driver};SERVER={server};UID={username};PWD={password}'
                self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

                with self.engine.begin() as connection:
                    connection.execute(update_query, {'selected_date': date_str, 'cod_qp': cod_qp})

                item = QTableWidgetItem(date_str)
                item.setTextAlignment(Qt.AlignCenter)
                self.tree.setItem(self.selected_row, 5, item)
                self.calendar.hide()
                self.consultar_qps_finalizadas()
            except Exception as ex:
                exibir_mensagem('Erro ao atualizar tabela', f'Erro: {str(ex)}', 'error')

    def eventFilter(self, obj, event):
        if obj == self.tree:
            if event.type() == QEvent.MouseButtonRelease or event.type() == QEvent.KeyPress:
                if self.calendar.isVisible():
                    self.calendar.hide()
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.calendar.isVisible():
            self.calendar.hide()
        elif event.key() == Qt.Key_Delete:
            current_item = self.tree.currentItem()
            if current_item is not None or current_item != '':
                current_row = self.tree.currentRow()
                current_column = self.tree.currentColumn()
                if self.tree.horizontalHeaderItem(current_column).text() == "DATA DE CONCLUSÃO":
                    cell_value = current_item.text()
                    if cell_value:
                        cod_qp = self.tree.item(current_row, 1).text()

                        delete_query = text("""
                            UPDATE enaplic_management.dbo.tb_end_qps
                            SET dt_completed_qp = ''
                            WHERE cod_qp = :cod_qp
                        """)

                        try:
                            conn_str = f'DRIVER={driver};SERVER={server};UID={username};PWD={password}'
                            self.engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

                            with self.engine.begin() as connection:
                                connection.execute(delete_query, {'cod_qp': cod_qp})
                            self.tree.setItem(current_row, current_column, QTableWidgetItem(''))
                            self.consultar_qps_finalizadas()
                        except Exception as ex:
                            exibir_mensagem('Erro ao remover data da tabela', f'Erro: {str(ex)}', 'error')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QpClosedApp()
    username, password, database, server = setup_mssql()
    driver = '{SQL Server}'
    window.showMaximized()
    sys.exit(app.exec_())
