import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QSpacerItem, QMessageBox, QFileDialog, QToolButton
from PyQt5.QtGui import QFont, QIcon, QDesktopServices, QColor
from PyQt5.QtCore import Qt, QUrl, QCoreApplication
import pyodbc
import pyperclip
import os
import time
import pandas as pd
import ctypes
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


class ComercialApp(QWidget):
    def __init__(self):
        super().__init__()

        self.tree = QTableWidget(self)
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)

        self.setWindowTitle("EUREKA® Comercial")

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor('#363636'))
        self.setPalette(palette)

        self.setStyleSheet("""
            * {
                background-color: #363636;
            }

            QLabel {
                color: #EEEEEE;
                font-size: 14px;
                padding: 5px;
                font-weight: bold;
            }

            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #262626;
                padding: 5px 25px;
                border-radius: 20px;
                height: 40px;
                font-size: 18px;
            }

            QPushButton {
                background-color: #3f7c24;
                color: #fff;
                padding: 5px 15px;
                border: 2px;
                border-radius: 20px;
                font-size: 14px;
                height: 40px;
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

            QTableWidget {
                border: 1px solid #000000;
                background-color: #363636;
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
        self.campo_codigo.setMinimumWidth(200)

        self.btn_consultar = QPushButton("Gerar relatório de MP", self)
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

        layout = QVBoxLayout()
        layout_linha_01 = QHBoxLayout()
        layout_linha_02 = QHBoxLayout()
        layout_linha_03 = QHBoxLayout()
        layout_linha_01.addWidget(QLabel("Digite o código da máquina/equipamento: "))
        layout_linha_02.addWidget(self.campo_codigo)
        layout_linha_02.addWidget(self.criar_botao_limpar(self.campo_codigo))

        # Adicione um espaçador esticável para centralizar os botões
        layout_linha_03.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout_linha_03.addWidget(self.btn_consultar)
        layout_linha_03.addWidget(self.btn_exportar_excel)
        layout_linha_03.addWidget(self.btn_fechar)
        # Adicione um espaçador esticável para centralizar os botões
        layout_linha_03.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(layout_linha_01)
        layout.addLayout(layout_linha_02)
        layout.addLayout(layout_linha_03)
        layout.addWidget(self.tree)
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

    def criar_botao_limpar(self, campo):
        botao_limpar = QToolButton(self)
        botao_limpar.setIcon(QIcon('clear_icon.png'))
        botao_limpar.setCursor(Qt.PointingHandCursor)
        botao_limpar.clicked.connect(lambda: campo.clear())
        return botao_limpar

    def exportar_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar como', '',
                                                   'Arquivos Excel (*.xlsx);;Todos os arquivos (*)')
        if file_path:
            # Obter os dados da tabela
            data = self.obter_dados_tabela()
            # Obter o nome das colunas da tabela
            column_headers = [self.tree.horizontalHeaderItem(i).text() for i in range(self.tree.columnCount())]
            # Criar um DataFrame pandas
            df = pd.DataFrame(data, columns=column_headers)
            # Salvar o DataFrame como um arquivo Excel
            df.to_excel(file_path, index=False)

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

    def configurar_tabela(self, cursor):
        self.tree.setColumnCount(len(cursor.description))
        self.tree.setHorizontalHeaderLabels([desc[0] for desc in cursor.description])
        self.tree.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tree.setSelectionBehavior(QTableWidget.SelectRows)
        self.tree.setSelectionMode(QTableWidget.SingleSelection)
        self.tree.itemDoubleClicked.connect(self.copiar_linha)
        fonte_tabela = QFont("Segoe UI", 10)
        self.tree.setFont(fonte_tabela)
        altura_linha = 34
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

    def verificar_query(self):
        codigo = self.campo_codigo.text().upper().strip()

        if codigo == '':
            self.btn_consultar.setEnabled(False)
            self.exibir_mensagem("ATENÇÃO!",
                                 "Os campos de pesquisa estão vazios.\nPreencha algum campo e tente "
                                 "novamente.\n\nツ\n\nSMARTPLIC®",
                                 "info")
            return True

        query = f"""
        DECLARE @CodigoPai VARCHAR(50) = '{codigo}'; -- Substitua pelo código pai que deseja consultar

        -- CTE para selecionar os itens pai e seus subitens recursivamente
        WITH ListMP AS (
            -- Selecionar o item pai inicialmente
            SELECT G1_COD AS "CÓDIGO", G1_COMP AS "COMPONENTE", 0 AS Nivel
            FROM SG1010
            WHERE G1_COD = @CodigoPai AND G1_REVFIM = (
                SELECT MAX(G1_REVFIM) 
                FROM SG1010 
                WHERE G1_COD = @CodigoPai AND G1_REVFIM <> 'ZZZ' AND D_E_L_E_T_ <> '*'
            ) AND G1_REVFIM <> 'ZZZ' AND D_E_L_E_T_ <> '*'

            UNION ALL

            -- Selecione os subitens de cada item pai
            SELECT sub.G1_COD, sub.G1_COMP, pai.Nivel + 1
            FROM SG1010 AS sub
            INNER JOIN ListMP AS pai ON sub.G1_COD = pai."COMPONENTE"
            WHERE pai.Nivel < 100 -- Defina o limite máximo de recursão aqui
            AND sub.G1_REVFIM <> 'ZZZ' AND sub.D_E_L_E_T_ <> '*'
        )

        -- Selecione todas as matérias-primas (tipo = 'MP') que correspondem aos itens encontrados
        SELECT DISTINCT 
            mat.G1_COMP AS "CÓDIGO", 
            prod.B1_DESC AS "DESCRIÇÃO", 
            mat.G1_QUANT AS "QUANT.", 
            mat.G1_XUM AS "UNID. MED.", 
            prod.B1_UCOM AS "ULT. ATUALIZ.",
            prod.B1_TIPO AS "TIPO", 
            prod.B1_LOCPAD AS "ARMAZÉM", 
            prod.B1_UPRC AS "VALOR UNIT. (R$)",
            (G1_QUANT * B1_UPRC) AS "VALOR TOTAL (R$)"
        FROM SG1010 AS mat
        INNER JOIN ListMP AS pai ON mat.G1_COD = pai."CÓDIGO"
        INNER JOIN SB1010 AS prod ON mat.G1_COMP = prod.B1_COD
        WHERE prod.B1_TIPO = 'MP' 
        AND mat.G1_REVFIM <> 'ZZZ' 
        AND mat.D_E_L_E_T_ <> '*'
        ORDER BY mat.G1_COMP ASC;
        """
        return query

    def executar_consulta(self):
        select_query = self.verificar_query()
        self.bloquear_campos_pesquisa()

        conn = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')

        try:
            cursor = conn.cursor()
            cursor.execute(select_query)
            self.configurar_tabela(cursor)
            self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
            self.tree.setRowCount(0)
            time.sleep(0.1)

            for i, row in enumerate(cursor.fetchall()):

                self.tree.setSortingEnabled(False)
                self.tree.insertRow(i)
                for j, value in enumerate(row):
                    if j == 4:
                        if not value.isspace():
                            data_obj = datetime.strptime(value, "%Y%m%d")
                            value = data_obj.strftime("%d/%m/%Y")

                    item = QTableWidgetItem(str(value).strip())

                    if j != 0 and j != 1:
                        item.setTextAlignment(Qt.AlignCenter)

                    self.tree.setItem(i, j, item)

                QCoreApplication.processEvents()

            self.tree.setSortingEnabled(True)
            self.desbloquear_campos_pesquisa()

        except pyodbc.Error as ex:
            self.exibir_mensagem('Erro ao consultar tabela', f'Erro: {str(ex)}', 'error')

        finally:
            conn.close()

    def fechar_janela(self):
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ComercialApp()
    username, password, database, server = ComercialApp().setup_mssql()
    driver = '{ODBC Driver 17 for SQL Server}'

    largura_janela = 1400  # Substitua pelo valor desejado
    altura_janela = 700  # Substitua pelo valor desejado

    largura_tela = app.primaryScreen().size().width()
    altura_tela = app.primaryScreen().size().height()

    pos_x = (largura_tela - largura_janela) // 2
    pos_y = (altura_tela - altura_janela) // 2

    window.setGeometry(pos_x, pos_y, largura_janela, altura_janela)

    window.show()
    sys.exit(app.exec_())
