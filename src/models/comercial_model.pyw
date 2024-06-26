import locale
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QToolButton, QStyle
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize
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
import xlwings as xw


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


def copiar_linha(item):
    if item is not None:
        valor_campo = item.text()
        pyperclip.copy(str(valor_campo))


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
                                         "Erro ao ler credenciais de acesso ao banco de dados MSSQL.\n\nBase de "
                                         "dados ERP TOTVS PROTHEUS.\n\nPor favor, informe ao desenvolvedor/TI "
                                         "sobre o erro exibido.\n\nTenha um bom dia! ツ",
                                         "CADASTRO DE ESTRUTURA - TOTVS®", 16 | 0)
        sys.exit()

    except Exception as ex:
        ctypes.windll.user32.MessageBoxW(0, f"Ocorreu um erro ao ler o arquivo: {ex}", "CADASTRO DE ESTRUTURA - TOTVS®",
                                         16 | 0)
        sys.exit()


def recalculate_excel_formulas(file_path):
    app_excel = xw.App(visible=False)
    wb = xw.Book(file_path)
    wb.app.calculate()  # Recalcular todas as fórmulas
    wb.save()
    wb.close()
    app_excel.quit()


class ComercialApp(QWidget):
    def __init__(self):
        super().__init__()

        self.codigo = None
        self.file_path = None

        self.tree = QTableWidget(self)
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)

        self.setWindowTitle("EUREKA® COMERCIAL - v0.1")
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor('#C9C9C9'))
        self.setPalette(palette)

        self.setStyleSheet("""
            * {
                background-color: #C9C9C9;
            }

            QLabel {
                color: #262626;
                font-size: 18px;
                padding: 5px;
                font-weight: bold;
            }

            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #262626;
                padding: 5px 10px;
                border-radius: 20px;
                height: 40px;
                font-size: 22px;
            }

            QPushButton {
                background-color: #3f7c24;
                color: #fff;
                padding: 15px;
                border: 2px;
                border-radius: 20px;
                font-size: 12px;
                height: 14px;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 15px;
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

        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_enaplic_path = os.path.join(script_dir, '..', 'resources', 'images', 'LOGO.jpeg')
        self.logo_label = QLabel(self)
        self.logo_label.setObjectName('logo-enaplic')
        pixmap_logo = QPixmap(logo_enaplic_path).scaledToWidth(60)
        self.logo_label.setPixmap(pixmap_logo)
        self.logo_label.setAlignment(Qt.AlignLeft)

        self.campo_codigo = QLineEdit(self)
        self.campo_codigo.setFont(QFont("Segoe UI", 10))
        self.campo_codigo.setFixedWidth(500)
        self.campo_codigo.setPlaceholderText("Digite o código da máquina ou equipamento...")

        self.btn_consultar = QPushButton("Consultar MP", self)
        self.btn_consultar.clicked.connect(self.executar_consulta)
        self.btn_consultar.setMinimumWidth(100)

        self.btn_exportar_pdf = QPushButton("Exportar PDF", self)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        self.btn_exportar_pdf.setMinimumWidth(100)
        self.btn_exportar_pdf.setEnabled(False)

        self.btn_salvar_excel = QPushButton("Exportar Excel", self)
        self.btn_salvar_excel.clicked.connect(self.salvar_excel)
        self.btn_salvar_excel.setMinimumWidth(100)
        self.btn_salvar_excel.setEnabled(False)

        self.btn_fechar = QPushButton("Fechar", self)
        self.btn_fechar.clicked.connect(self.fechar_janela)
        self.btn_fechar.setMinimumWidth(100)

        self.campo_codigo.returnPressed.connect(self.executar_consulta)

        layout = QVBoxLayout()
        layout_linha_01 = QHBoxLayout()
        layout_footer = QHBoxLayout()
        layout_footer_logo = QHBoxLayout()

        layout_linha_01.addWidget(self.campo_codigo)
        layout_linha_01.addWidget(self.criar_botao_limpar())

        layout_linha_01.addWidget(self.btn_consultar)
        layout_linha_01.addWidget(self.btn_salvar_excel)
        layout_linha_01.addWidget(self.btn_exportar_pdf)
        layout_linha_01.addWidget(self.btn_fechar)
        layout_linha_01.addStretch()

        layout_footer_logo.addWidget(self.logo_label)

        layout.addLayout(layout_linha_01)
        layout.addWidget(self.tree)
        layout.addLayout(layout_footer)
        layout.addLayout(layout_footer_logo)

        self.setLayout(layout)

    def criar_botao_limpar(self):
        botao_limpar = QToolButton(self)
        botao_limpar.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))  # Ícone integrado do Qt
        botao_limpar.setCursor(Qt.PointingHandCursor)
        botao_limpar.clicked.connect(self.limpar_campos)
        botao_limpar.setIconSize(QSize(32, 32))

        # Estilizando o botão usando QSS
        botao_limpar.setStyleSheet("""
            QToolButton {
                border: none;
                background: #c9c9c9;
                padding: 2px;
                width: 40px;
                height: 40px;
                border-radius: 20px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
        """)

        return botao_limpar

    def salvar_excel(self):

        now = datetime.now()
        default_filename = f'{self.codigo}_report_mp_{now.strftime("%Y-%m-%d_%H%M%S")}.xlsx'

        desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
        self.file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar como',
                                                        os.path.join(desktop_path, default_filename),
                                                        'Arquivos Excel (*.xlsx);;Todos os arquivos (*)')

        if self.file_path:
            data = self.obter_dados_tabela()
            column_headers = [self.tree.horizontalHeaderItem(i).text() for i in range(self.tree.columnCount())]
            df = pd.DataFrame(data, columns=column_headers)

            # Converter as colunas 'QUANT.', 'VALOR UNIT. (R$)' e 'SUB-TOTAL (R$)' para números
            numeric_columns = ['QUANT.', 'VALOR UNIT. (R$)', 'SUB-TOTAL (R$)']
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

            writer = pd.ExcelWriter(self.file_path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Dados', index=False)

            workbook = writer.book
            worksheet_dados = writer.sheets['Dados']

            # Ajustar largura das colunas na planilha 'Dados'
            for i, col in enumerate(df.columns):
                max_len = df[col].astype(str).map(len).max()
                worksheet_dados.set_column(i, i, max_len + 2)

            # Calcular a última linha da planilha 'Dados'
            last_row = len(df) + 3  # +1 for header, +1 for the extra line we want to skip

            # Definindo um formato contábil
            accounting_format = workbook.add_format({'num_format': '[$R$-pt-BR] #,##0.00'})

            # Adicionar fórmulas na planilha 'Dados' na última linha + 1
            worksheet_dados.write(f'A{last_row}', 'TOTAL COMERCIAL')
            worksheet_dados.write_formula(f'B{last_row}',
                                          f'=SUMIF(G2:G{last_row - 2}, "COMERCIAL", I2:I{last_row - 2})',
                                          accounting_format)

            worksheet_dados.write(f'A{last_row + 1}', 'TOTAL MP')
            worksheet_dados.write_formula(f'B{last_row + 1}',
                                          f'=SUMIF(G2:G{last_row - 2}, "MATÉRIA-PRIMA", I2:I{last_row - 2})',
                                          accounting_format)

            worksheet_dados.write(f'A{last_row + 2}', 'TOTAL PROD. COMER. IMPORT. DIR.')
            worksheet_dados.write_formula(f'B{last_row + 2}',
                                          f'=SUMIF(G2:G{last_row - 2}, "PROD. COMER. IMPORT. DIRETO", I2:I{last_row - 2})',
                                          accounting_format)

            worksheet_dados.write(f'A{last_row + 3}', 'TOTAL MAT. PRIMA IMPORTADA')
            worksheet_dados.write_formula(f'B{last_row + 3}',
                                          f'=SUMIF(G2:G{last_row - 2}, "MAT. PRIMA IMPORT. DIRETO", I2:I{last_row - 2})',
                                          accounting_format)

            worksheet_dados.write(f'A{last_row + 4}', 'TOTAL TRAT. SUPERF.')
            worksheet_dados.write_formula(f'B{last_row + 4}',
                                          f'=SUMIF(G2:G{last_row - 2}, "TRAT. SUPERFICIAL", I2:I{last_row - 2})',
                                          accounting_format)

            worksheet_dados.write(f'C{last_row + 1}', 'TOTAL (kg)')
            worksheet_dados.write_formula(f'C{last_row + 1}', f'=SUMIF(D2:D{last_row - 2}, "KG", C2:C{last_row - 2})')

            worksheet_dados.write(f'A{last_row + 6}', 'TOTAL GERAL')
            worksheet_dados.write_formula(f'B{last_row + 6}', f'=SUBTOTAL(9, B{last_row}:B{last_row + 4})',
                                          accounting_format)

            writer.close()

            recalculate_excel_formulas(self.file_path)

            os.startfile(self.file_path)

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

    def exportar_pdf(self):

        if not self.file_path:
            return

        # Ler dados do Excel
        dataframe_tabela = pd.read_excel(self.file_path, sheet_name='Dados')

        # Caminho para salvar o PDF
        pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar como',
                                                  f'{self.campo_codigo.text().upper().strip()}_MP.pdf',
                                                  'Arquivos PDF (*.pdf);;Todos os arquivos (*)')

        if not pdf_path:
            return

        nan_row_index = dataframe_tabela.isna().all(axis=1).idmax()

        df_dados = dataframe_tabela.iloc[:nan_row_index].dropna(how='all')
        df_valores = dataframe_tabela.iloc[nan_row_index + 1:].dropna(how='all')

        # Criação do documento PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        elements = []

        # Adicionar logo
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_enaplic_path = os.path.join(script_dir, '..', 'resources', 'images', 'logo_enaplic.jpg')

        if os.path.exists(logo_enaplic_path):
            logo = Image(logo_enaplic_path, 2 * inch, 2 * inch)
            elements.append(logo)

        # Adicionar título e data/hora
        styles = getSampleStyleSheet()
        title = Paragraph("Relatório de Materiais", styles['Title'])
        date_time = Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles['Normal'])

        elements.append(title)
        elements.append(date_time)
        elements.append(Paragraph("<br/><br/>", styles['Normal']))  # Espaço entre título e tabela

        # Dados da tabela
        column_headers_dados = list(df_dados.columns)
        table_dados = [column_headers_dados] + df_dados.values.tolist()

        max_width = 540  # Largura máxima da tabela em pontos
        col_widths = [max_width / len(column_headers_dados)] * len(column_headers_dados)

        # Estilo da tabela
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])

        table = Table(table_dados, colWidths=col_widths)
        table.setStyle(style)
        elements.append(table)

        column_headers_part2 = list(df_valores.columns)
        table_valores = [column_headers_part2] + df_valores.values.tolist()

        summary_table = Table(table_valores, colWidths=column_headers_part2)

        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(Paragraph("<br/><br/>", styles['Normal']))  # Espaço entre tabela e sumário
        elements.append(summary_table)

        # Função para adicionar rodapé com paginação
        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            text = f"Página {page_num}"
            canvas.drawRightString(200 * mm, 15 * mm, text)

        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        os.startfile(pdf_path)

    def configurar_tabela(self, dataframe):
        self.tree.setColumnCount(len(dataframe.columns))
        self.tree.setHorizontalHeaderLabels(dataframe.columns)
        self.tree.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tree.setSelectionBehavior(QTableWidget.SelectRows)
        self.tree.setSelectionMode(QTableWidget.SingleSelection)
        self.tree.itemDoubleClicked.connect(copiar_linha)
        fonte_tabela = QFont("Segoe UI", 10)
        self.tree.setFont(fonte_tabela)
        altura_linha = 40
        self.tree.verticalHeader().setDefaultSectionSize(altura_linha)
        self.tree.horizontalHeader().sectionClicked.connect(self.ordenar_tabela)
        self.tree.horizontalHeader().setStretchLastSection(True)

    def ordenar_tabela(self, logical_index):
        # Obter o índice real da coluna (considerando a ordem de classificação)
        index = self.tree.horizontalHeader().sortIndicatorOrder()

        # Definir a ordem de classificação
        order = Qt.AscendingOrder if index == 0 else Qt.DescendingOrder

        # Ordenar a tabela pela coluna clicada
        self.tree.sortItems(logical_index, order)

    def limpar_campos(self):
        self.campo_codigo.clear()
        self.tree.setColumnCount(0)
        self.tree.setRowCount(0)

    def bloquear_campos_pesquisa(self):
        self.campo_codigo.setEnabled(False)
        self.btn_consultar.setEnabled(False)
        self.btn_salvar_excel.setEnabled(False)
        self.btn_exportar_pdf.setEnabled(False)

    def desbloquear_campos_pesquisa(self):
        self.campo_codigo.setEnabled(True)
        self.btn_consultar.setEnabled(True)
        self.btn_salvar_excel.setEnabled(True)
        self.btn_exportar_pdf.setEnabled(True)

    def verificar_query(self):
        codigo = self.campo_codigo.text().upper().strip()
        self.codigo = codigo

        if codigo == '':
            self.btn_consultar.setEnabled(False)
            exibir_mensagem("ATENÇÃO!",
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
            mat.G1_COD AS "CODIGO PAI",
            mat.G1_COMP AS "CÓDIGO", 
            prod.B1_DESC AS "DESCRIÇÃO", 
            mat.G1_QUANT AS "QUANT.", 
            mat.G1_XUM AS "UNID. MED.", 
            prod.B1_UCOM AS "ULT. ATUALIZ.",
            prod.B1_TIPO AS "TIPO", 
            prod.B1_LOCPAD AS "ARMAZÉM", 
            prod.B1_UPRC AS "VALOR UNIT. (R$)",
            (G1_QUANT * B1_UPRC) AS "SUB-TOTAL (R$)"
        FROM SG1010 AS mat
        INNER JOIN ListMP AS pai ON mat.G1_COD = pai."CÓDIGO"
        INNER JOIN SB1010 AS prod ON mat.G1_COMP = prod.B1_COD
        WHERE prod.B1_TIPO = 'MP'
        AND prod.B1_LOCPAD IN ('01','03', '11', '12', '97')
        AND mat.G1_REVFIM <> 'ZZZ' 
        AND mat.D_E_L_E_T_ <> '*'
        ORDER BY mat.G1_COMP ASC;
        """
        return query

    def executar_consulta(self):
        select_query = self.verificar_query()
        self.bloquear_campos_pesquisa()

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe = pd.read_sql(select_query, engine)
            consolidated_dataframe = dataframe.groupby('CÓDIGO').agg({
                'DESCRIÇÃO': 'first',
                'QUANT.': 'sum',
                'UNID. MED.': 'first',
                'ULT. ATUALIZ.': 'first',
                'TIPO': 'first',
                'ARMAZÉM': 'first',
                'VALOR UNIT. (R$)': 'first',
                'SUB-TOTAL (R$)': 'sum'
            }).reset_index()

            # Converter para float com duas casas decimais
            columns_to_convert = ['QUANT.', 'VALOR UNIT. (R$)', 'SUB-TOTAL (R$)']
            consolidated_dataframe[columns_to_convert] = (consolidated_dataframe[columns_to_convert]
                                                          .map(lambda x: round(float(x), 2)))
            consolidated_dataframe[''] = ''

            self.configurar_tabela(consolidated_dataframe)

            self.tree.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
            self.tree.setRowCount(0)

            for i, row in consolidated_dataframe.iterrows():
                self.tree.setSortingEnabled(False)
                self.tree.insertRow(i)
                for j, value in enumerate(row):
                    # if j in (2, 7, 8):
                    # value = locale.format_string("%.2f", value, grouping=True)
                    if j == 4 and not value.isspace():
                        data_obj = datetime.strptime(value, "%Y%m%d")
                        value = data_obj.strftime("%d/%m/%Y")
                    elif j == 6:
                        if value == '01':
                            value = 'MATÉRIA-PRIMA'
                        elif value == '03':
                            value = 'COMERCIAL'
                        elif value == '11':
                            value = 'PROD. COMER. IMPORT. DIRETO'
                        elif value == '12':
                            value = 'MAT. PRIMA IMPORT. DIRETO'
                        elif value == '97':
                            value = 'TRAT. SUPERFICIAL'

                    item = QTableWidgetItem(str(value).strip())

                    if 2 <= j < 7:
                        item.setTextAlignment(Qt.AlignCenter)
                    elif j == 7 or j == 8:
                        item.setTextAlignment(Qt.AlignRight)

                    self.tree.setItem(i, j, item)

                # QCoreApplication.processEvents()

            self.tree.setSortingEnabled(True)
            self.desbloquear_campos_pesquisa()

        except pyodbc.Error as ex:
            exibir_mensagem('Erro ao consultar tabela', f'Erro: {str(ex)}', 'error')

        finally:
            # Fecha a conexão com o banco de dados se estiver aberta
            if 'engine' in locals():
                engine.dispose()

    def fechar_janela(self):
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ComercialApp()
    username, password, database, server = setup_mssql()
    driver = '{SQL Server}'

    window.showMaximized()

    sys.exit(app.exec_())
