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
        self.page = self.pdf_document.load_page(page_number)
        pix = self.page.get_pixmap()
        self.pdf_width, self.pdf_height = pix.width, pix.height  # Dimensões reais do PDF

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((800, 600))  # Ajusta o tamanho da imagem
        self.img_tk = ImageTk.PhotoImage(img)

        self.canvas.create_image(0, 0, image=self.img_tk, anchor="nw")

        # Dimensões da imagem no Canvas
        self.canvas_width, self.canvas_height = self.img_tk.width(), self.img_tk.height()

    def convert_canvas_to_pdf_coords(self, x, y):
        """Converte coordenadas do Canvas para coordenadas reais do PDF."""
        pdf_x = (x / self.canvas_width) * self.pdf_width
        pdf_y = (y / self.canvas_height) * self.pdf_height
        return pdf_x, pdf_y

    def on_button_press(self, event):
        self.start_x, self.start_y = self.convert_canvas_to_pdf_coords(event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)

    def on_mouse_drag(self, event):
        end_x, end_y = self.convert_canvas_to_pdf_coords(event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            event.x, event.y, self.start_x * (self.canvas_width / self.pdf_width),
            self.start_y * (self.canvas_height / self.pdf_height),
            outline="red"
        )

    def on_button_release(self, event):
        end_x, end_y = self.convert_canvas_to_pdf_coords(event.x, event.y)
        self.table_area = [self.start_x, self.start_y, end_x, end_y]
        print(f"Área selecionada (coordenadas PDF): {self.table_area}")

        # Extrai o texto da área selecionada usando PyMuPDF
        rect = fitz.Rect(self.table_area)
        text = self.page.get_text("text", clip=rect)
        print(f"Texto extraído:\n{text}")

    def extract_table(self):
        if not hasattr(self, 'table_area'):
            print("Nenhuma área selecionada.")
            return

        # Lê a tabela usando Camelot com a área selecionada
        tables = camelot.read_pdf(
            self.pdf_path,
            pages=str(self.page_number + 1),  # Camelot usa indexação a partir de 1
            flavor='stream',
            table_areas=[",".join(map(str, self.table_area))]
        )

        if tables and len(tables) > 0:
            print(tables[0].df)
        else:
            print("Nenhuma tabela encontrada.")

if __name__ == '__main__':
    root = tk.Tk()
    app = PDFExtractorApp(root)
    root.mainloop()
