import os
import camelot
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF

class PDFExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Extrator de Tabelas de PDF')

        # Canvas para interagir
        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Carregar PDF
        self.pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not self.pdf_path:
            return  # Caso o usuário não escolha nenhum arquivo, fecha a aplicação

        self.pdf_document = fitz.open(self.pdf_path)

        # Exibir a primeira página do PDF
        self.page_number = 0
        self.show_pdf_page(self.page_number)

        # Caixa de marcação (retângulo)
        self.rect = None
        self.start_x = None
        self.start_y = None

        # Botão para extrair a tabela
        self.extract_button = tk.Button(self.root, text="Extrair Tabela", command=self.extract_table)
        self.extract_button.pack()

    def show_pdf_page(self, page_number):
        # Converte a página para imagem e exibe no canvas
        page = self.pdf_document.load_page(page_number)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((800, 600))  # Ajusta o tamanho da imagem
        self.img_tk = ImageTk.PhotoImage(img)

        self.canvas.create_image(0, 0, image=self.img_tk, anchor="nw")

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)

    def on_mouse_drag(self, event):
        # Atualiza o retângulo conforme o movimento do mouse
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red")

    def on_button_release(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.extract_area(self.start_x, self.start_y, self.end_x, self.end_y)

    def extract_area(self, x1, y1, x2, y2):
        # Ajusta as coordenadas para melhorar o alinhamento
        adjusted_x1 = x1
        adjusted_y1 = y1 - 10  # Ajuste para cima
        adjusted_x2 = x2
        adjusted_y2 = y2 - 10  # Ajuste para cima

        # Converte as coordenadas para a área no formato que o PyMuPDF usa
        self.table_area = [adjusted_x1, adjusted_y1, adjusted_x2, adjusted_y2]
        print(f"Área selecionada: {self.table_area}")

        # Extrai o texto da área selecionada usando PyMuPDF
        page = self.pdf_document.load_page(self.page_number)
        rect = fitz.Rect(adjusted_x1, adjusted_y1, adjusted_x2, adjusted_y2)
        text = page.get_text("text", clip=rect)
        print(f"Texto extraído: {text}")

    def extract_table(self):
        if not hasattr(self, 'table_area'):
            print("Nenhuma área selecionada.")
            return

        # Lê a tabela usando Camelot com a área selecionada
        tables = camelot.read_pdf(
            self.pdf_path,
            pages='1',
            flavor='stream',
            table_areas=[",".join(map(str, self.table_area))],
            columns=['65, 107, 156, 212, 280, 336, 383, 450']
        )

        if tables:
            print(tables[0].df)
        else:
            print("Nenhuma tabela encontrada.")

if __name__ == '__main__':
    root = tk.Tk()
    app = PDFExtractorApp(root)
    root.mainloop()
