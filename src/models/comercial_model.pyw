import ctypes
import io
import locale
import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import pandas as pd
import pyodbc
import pyperclip
import xlwings as xw
from PyPDF2 import PdfReader
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QToolButton, QStyle, QAction
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from sqlalchemy import create_engine


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


class Communicate(QObject):
    sinal = pyqtSignal()


class ComercialApp(QWidget):
    def __init__(self):
        super().__init__()

        self.c = Communicate()

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
                font-size: 14px;
                font-weight: bold;
                padding-left: 5px;
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
                margin-top: 20px;
                margin-left: 10px;
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
                margin-top: 15px;
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
        self.logo_label.setAlignment(Qt.AlignRight)

        self.label_codigo = QLabel("Código:", self)

        self.campo_codigo = QLineEdit(self)
        self.campo_codigo.setFont(QFont("Segoe UI", 10))
        self.campo_codigo.setFixedWidth(210)
        self.campo_codigo.setMaxLength(13)
        self.add_clear_button(self.campo_codigo)

        self.btn_consultar = QPushButton("Custo MP ($)", self)
        self.btn_consultar.clicked.connect(self.executar_consulta)
        self.btn_consultar.setMinimumWidth(100)

        self.btn_limpar = QPushButton("Limpar", self)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_limpar.setMinimumWidth(100)

        self.btn_exportar_pdf = QPushButton("Exportar PDF", self)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        self.btn_exportar_pdf.setMinimumWidth(100)
        self.btn_exportar_pdf.setEnabled(False)

        self.btn_exportar_excel = QPushButton("Exportar Excel", self)
        self.btn_exportar_excel.clicked.connect(lambda: self.exportar_excel('excel'))
        self.btn_exportar_excel.setMinimumWidth(100)
        self.btn_exportar_excel.setEnabled(False)

        self.btn_fechar = QPushButton("Fechar", self)
        self.btn_fechar.clicked.connect(self.fechar_janela)
        self.btn_fechar.setMinimumWidth(100)

        self.campo_codigo.returnPressed.connect(self.executar_consulta)

        layout = QVBoxLayout()
        container_codigo = QVBoxLayout()
        layout_header = QHBoxLayout()
        layout_footer = QHBoxLayout()
        layout_footer_logo = QHBoxLayout()

        container_codigo.addWidget(self.label_codigo)
        container_codigo.addWidget(self.campo_codigo)

        layout_header.addLayout(container_codigo)
        layout_header.addWidget(self.btn_consultar)
        layout_header.addWidget(self.btn_limpar)
        layout_header.addWidget(self.btn_exportar_excel)
        layout_header.addWidget(self.btn_exportar_pdf)
        layout_header.addWidget(self.btn_fechar)
        layout_header.addStretch()

        layout_footer_logo.addWidget(self.logo_label)

        layout.addLayout(layout_header)
        layout.addWidget(self.tree)
        layout.addLayout(layout_footer)
        layout.addLayout(layout_footer_logo)

        self.setLayout(layout)

    def add_clear_button(self, line_edit):
        clear_icon = self.style().standardIcon(QStyle.SP_LineEditClearButton)
        pixmap = clear_icon.pixmap(40, 40)  # Redimensionar o ícone para 20x20 pixels
        larger_clear_icon = QIcon(pixmap)
        clear_action = QAction(larger_clear_icon, "Clear", line_edit)
        clear_action.triggered.connect(line_edit.clear)
        line_edit.addAction(clear_action, QLineEdit.TrailingPosition)

    def exportar_excel(self, tipo_exportacao):

        now = datetime.now()
        default_filename = f'{self.codigo}_report_mp_{now.strftime("%Y-%m-%d_%H%M%S")}.xlsx'
        desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')

        if tipo_exportacao == 'excel':
            self.file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar como', os.path.join(
                                                        desktop_path, default_filename),
                                                        'Arquivos Excel (*.xlsx);;Todos os arquivos (*)')
        elif tipo_exportacao == 'pdf':
            self.file_path = os.path.join(desktop_path, default_filename)

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

            if tipo_exportacao == 'excel':
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
        self.exportar_excel('pdf')

        # Ler dados do Excel
        dataframe_tabela = pd.read_excel(self.file_path, sheet_name='Dados')

        # Caminho para salvar o PDF
        pdf_path, _ = QFileDialog.getSaveFileName(self, 'Salvar como', self.file_path.replace('.xlsx', '.pdf'),
                                                  'Arquivos PDF (*.pdf);;Todos os arquivos (*)')

        if not pdf_path:
            return

        nan_row_index = dataframe_tabela.isna().all(axis=1).idxmax()

        df_dados = dataframe_tabela.iloc[:nan_row_index].dropna(how='all')
        df_valores = dataframe_tabela.iloc[nan_row_index + 1:].dropna(how='all')

        df_valores = df_valores.dropna(axis=1, how='all').fillna('')

        def format_decimal(value):
            return f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

        if 'QUANT.' in df_dados.columns:
            df_dados['QUANT.'] = df_dados['QUANT.'].apply(format_decimal)
        if 'VALOR UNIT. (R$)' in df_dados.columns:
            df_dados['VALOR UNIT. (R$)'] = df_dados['VALOR UNIT. (R$)'].apply(format_decimal)
        if 'SUB-TOTAL (R$)' in df_dados.columns:
            df_dados['SUB-TOTAL (R$)'] = df_dados['SUB-TOTAL (R$)'].apply(format_decimal)

        if 'TIPO' in df_dados.columns:
            df_dados = df_dados.drop(columns='TIPO')

        if 'UNID. MED.' in df_dados.columns:
            df_dados = df_dados.rename(columns={'UNID. MED.': 'UNID.\nMED.'})

        if 'ARMAZÉM' in df_dados.columns:
            df_dados['ARMAZÉM'] = df_dados['ARMAZÉM'].replace({'COMERCIAL': 'COM.', 'MATÉRIA-PRIMA': 'MP'})

        if 'ULT. ATUALIZ.' in df_dados.columns:
            df_dados = df_dados.rename(columns={'ULT. ATUALIZ.': 'ÚLT.\nATUALIZ.'})

        if 'VALOR UNIT. (R$)' in df_dados.columns:
            df_dados = df_dados.rename(columns={'VALOR UNIT. (R$)': 'VALOR\nUNIT. (R$)'})

        if 'SUB-TOTAL (R$)' in df_dados.columns:
            df_dados = df_dados.rename(columns={'SUB-TOTAL (R$)': 'TOTAL (R$)'})

        table_valores_header = ['TOTAL POR ARMAZÉM', 'CUSTO\n(R$)', 'QUANTIDADE\n(kg)']
        table_valores = [table_valores_header] + df_valores.values.tolist()

        # Index das colunas que você deseja formatar
        idx_custo = table_valores_header.index('CUSTO\n(R$)')
        idx_quantidade = table_valores_header.index('QUANTIDADE\n(kg)')

        for row in table_valores[1:]:  # Começa do segundo item para pular o cabeçalho
            row[idx_custo] = format_decimal(row[idx_custo])
            if row[idx_quantidade] != '':
                row[idx_quantidade] = format_decimal(row[idx_quantidade])

        def build_elements():
            elements_pdf = []

            # Adicionar logo
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_enaplic_path = os.path.join(script_dir, '..', 'resources', 'images', 'logo_enaplic.jpg')

            if os.path.exists(logo_enaplic_path):
                logo = Image(logo_enaplic_path, 5 * inch, 0.5 * inch)
                elements_pdf.append(logo)

            # Adicionar título e data/hora
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(name='TitleStyle', fontSize=16, fontName='Helvetica-Bold', leading=24,
                                         alignment=TA_CENTER)
            normal_style = ParagraphStyle(name='NormalStyle', fontSize=10, leading=12, alignment=TA_CENTER)
            product_style = ParagraphStyle(name='ProductStyle', fontSize=12, leading=20, fontName='Helvetica-Bold',
                                           spaceAfter=12)

            title = Paragraph("Relatório - Custo de Matéria-Prima por Produto", title_style)
            date_time = Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), normal_style)
            elements_pdf.append(Paragraph("<br/><br/>", normal_style))
            product = Paragraph(f'{self.codigo} XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', product_style)

            elements_pdf.append(title)
            elements_pdf.append(date_time)
            elements_pdf.append(Spacer(1, 12))
            elements_pdf.append(product)
            elements_pdf.append(Spacer(1, 12))  # Espaço entre título e tabela

            # Dados da tabela
            column_headers_dados = list(df_dados.columns)
            table_dados = [column_headers_dados] + df_dados.values.tolist()

            # Função para calcular a largura das colunas com base no conteúdo
            def calculate_col_widths(dataframe, col_width_multiplier=1.2, min_width=45):
                col_widths = []
                for col in dataframe.columns:
                    max_length = max(dataframe[col].astype(str).apply(len).max(), len(col))
                    col_width = max_length * col_width_multiplier
                    if col == 'DESCRIÇÃO':
                        col_width *= 3  # Aumentar a largura da coluna "descrição"
                    col_width = max(col_width, min_width)
                    col_widths.append(col_width)
                return col_widths

            col_widths_dados = calculate_col_widths(df_dados)

            col_idx_descricao = column_headers_dados.index('DESCRIÇÃO')

            # Estilo da tabela
            style_dados = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (col_idx_descricao, 0), (col_idx_descricao, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])

            table_dados = Table(table_dados, colWidths=col_widths_dados)
            table_dados.setStyle(style_dados)
            elements_pdf.append(table_dados)

            style_valores = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Alinha a primeira coluna à esquerda
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Alinha as demais colunas à direita
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])

            summary_table = Table(table_valores)
            summary_table.setStyle(style_valores)

            elements_pdf.append(Spacer(1, 36))  # Espaço entre tabela e sumário
            elements_pdf.append(summary_table)

            return elements_pdf

        # Primeira passagem para contar as páginas
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20, bottomMargin=30)
        elements = build_elements()

        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            text = f"Página {page_num}"
            canvas.drawRightString(200 * mm, 5 * mm, text)

        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        pdf = buffer.getvalue()
        buffer.close()

        # Contar o número total de páginas
        reader = PdfReader(io.BytesIO(pdf))
        num_pages = len(reader.pages)

        # Segunda passagem para adicionar paginação completa
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20, bottomMargin=30)
        elements = build_elements()

        def add_page_number_with_total(canvas, doc):
            page_num = canvas.getPageNumber()
            text = f"Página {page_num} de {num_pages}"
            canvas.drawRightString(200 * mm, 5 * mm, text)

        doc.build(elements, onFirstPage=add_page_number_with_total, onLaterPages=add_page_number_with_total)
        final_pdf = buffer.getvalue()
        buffer.close()

        # Salvar o PDF final
        with open(pdf_path, "wb") as f:
            f.write(final_pdf)
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

    def controle_campos_formulario(self, status):
        self.campo_codigo.setEnabled(status)
        self.btn_consultar.setEnabled(status)
        self.btn_exportar_excel.setEnabled(status)
        self.btn_exportar_pdf.setEnabled(status)

    def query_consulta(self):
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
        select_query = self.query_consulta()
        self.controle_campos_formulario(False)

        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}')

        try:
            dataframe = pd.read_sql(select_query, engine)

            if not dataframe.empty:
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
                self.controle_campos_formulario(True)
            else:
                exibir_mensagem("EUREKA® Comercial", 'Produto não encontrado!', "info")
                self.controle_campos_formulario(True)
                return

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
