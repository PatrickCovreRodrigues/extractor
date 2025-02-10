import os
import camelot
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import pandas as pd

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
            self.root.destroy()  # Fecha a aplicação se nenhum arquivo for escolhido
            return

        self.pdf_folder = os.path.dirname(self.pdf_path)  # Obtém a pasta onde está o PDF selecionado
        self.pdf_document = fitz.open(self.pdf_path)

        # Exibir a primeira página do PDF
        self.page_number = 0
        self.show_pdf_page(self.page_number)

        # Caixa de marcação (retângulo)
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.selected_areas = []

        # Botões para extrair e limpar seleções
        self.extract_button = tk.Button(self.root, text="Extrair Tabelas", command=self.extract_tables)
        self.extract_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = tk.Button(self.root, text="Limpar Seleções", command=self.clear_selections)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Fechamento Limpo
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_pdf_page(self, page_number):
        try:
            # Converte a página para imagem e exibe no canvas
            self.page = self.pdf_document.load_page(page_number)
            pix = self.page.get_pixmap()
            self.pdf_width, self.pdf_height = pix.width, pix.height

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.thumbnail((800, 600))  # Ajusta o tamanho da imagem
            self.img_tk = ImageTk.PhotoImage(img)

            self.canvas.create_image(0, 0, image=self.img_tk, anchor="nw")
            self.canvas_width, self.canvas_height = self.img_tk.width(), self.img_tk.height()
        except Exception as e:
            print(f"Erro ao carregar a página: {e}")

    def convert_canvas_to_pdf_coords(self, x, y):
        pdf_x = (x / self.canvas_width) * self.pdf_width
        pdf_y = self.pdf_height - (y / self.canvas_height) * self.pdf_height  # Inverte o eixo Y
        return pdf_x, pdf_y

    def on_button_press(self, event):
        self.start_x, self.start_y = self.convert_canvas_to_pdf_coords(event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)

    def on_mouse_drag(self, event):
        if self.rect:
            self.canvas.delete(self.rect)

        # Desenha o retângulo no canvas com coordenadas diretamente do evento
        self.rect = self.canvas.create_rectangle(
            self.start_x * (self.canvas_width / self.pdf_width),
            (self.pdf_height - self.start_y) * (self.canvas_height / self.pdf_height),
            event.x, event.y,
            outline="red"
        )

    def on_button_release(self, event):
        end_x, end_y = self.convert_canvas_to_pdf_coords(event.x, event.y)

        # Garante que as coordenadas estão na ordem correta
        x1, y1 = min(self.start_x, end_x), max(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), min(self.start_y, end_y)

        self.selected_areas.append([x1, y1, x2, y2])
        print(f"Área selecionada (coordenadas PDF): {[x1, y1, x2, y2]}")

    def extract_tables(self):
        if not self.selected_areas:
            print("Nenhuma área selecionada.")
            return

        try:
            all_tables = []

            # Loop pelos arquivos PDF na mesma pasta
            for pdf_file in os.listdir(self.pdf_folder):
                if pdf_file.endswith(".pdf"):
                    pdf_path = os.path.join(self.pdf_folder, pdf_file)
                    pdf_document = fitz.open(pdf_path)

                    for page_number in range(len(pdf_document)):
                        for area in self.selected_areas:
                            tables = camelot.read_pdf(
                                pdf_path,
                                pages=str(page_number + 1),
                                flavor='stream',
                                table_areas=["{},{},{},{}".format(*area)],
                            )

                            if tables and len(tables) > 0:
                                df = tables[0].df

                                df.columns = [str(col).replace("\n", " ") for col in df.columns]
                                for i in range(len(df)):
                                    df.iloc[i] = df.iloc[i].apply(lambda x: str(x).replace("\n", " "))

                                all_tables.append(df)
                            else:
                                print(f"Não foram encontradas tabelas no arquivo {pdf_file}, página {page_number + 1} na área {area}.")

                    pdf_document.close()

            if all_tables:
                combined_df = pd.concat(all_tables)
                save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
                if save_path:
                    combined_df.to_csv(save_path, index=False, sep=';', decimal=',', encoding='utf-8-sig')
                    print(f"Tabelas salvas em {save_path}")
            else:
                print("Nenhuma tabela extraída.")
        except Exception as e:
            print(f"Erro ao extrair tabelas: {e}")

    def clear_selections(self):
        self.selected_areas = []
        self.canvas.delete("all")
        self.show_pdf_page(self.page_number)
        print("Seleções limpas.")

    def on_closing(self):
        self.pdf_document.close()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = PDFExtractorApp(root)
    root.mainloop()
