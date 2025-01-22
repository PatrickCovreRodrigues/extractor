import os
import camelot
import matplotlib.pyplot as plt
import pandas as pd
import logging

from configs.rules.regras import rules_dict
from configs.tools.postgre import RDSPostgreSQLManager

logging.basicConfig(level=logging.INFO)


class PDFTableExtractor:
    def __init__(self, file_name, configs):
        self.path = os.path.abspath(f"/files/pdf/regra1/{file_name}.pdf")
        self.csv_path = os.path.abspath(f'files/csv/')
        self.file_name = file_name
        self.configs = configs

    def start(self):
        logging.info(f"Start pdf - {self.file_name}")
        header = self.get_table_data(self.configs["header_table_areas"], self.configs["header_columns"],
                                     self.configs["header_fix"])
        main = self.get_table_data(self.configs["table_areas"], self.configs["columns"], self.configs["fix"])
        small = self.get_table_data(self.configs["small_table_areas"], self.configs["small_columns"],
                                    self.configs["small_fix"])

        main = self.add_infos(header, main)
        small = self.add_infos(header, small)

        main = self.sanitize_column_names(main)
        if self.configs["small_sanitize"]:
            small = self.sanitize_column_names(small)

        logging.info(f"Saving csv - {self.file_name}")
        self.save_csv(main, self.file_name)
        self.save_csv(small, f"{self.file_name}_small")

        logging.info(f"Sending to DB - {self.file_name}")
        self.send_to_db(main, f"Fatura_{self.configs['name']}".lower())
        self.send_to_db(small, f"Fatura_{self.configs['name']}_small".lower())

        return {"main": main, "small": small}

    def get_table_data(self, table_areas, table_columns, fix=True):
        logging.info(f"Attempting to extract tables for file: {self.file_name}")
        try:
            tables = camelot.read_pdf(
                self.path,
                flavor=self.configs['flavor'],
                table_areas=table_areas,
                columns=table_columns,
                strip_text=self.configs['strip_text'],
                page=self.configs['pages'],
            )
            if not tables or len(tables) == 0:
                logging.warning(f"No tables found in {self.file_name}. Please check the table areas and columns.")
                return pd.DataFrame()  # Return empty DataFrame if no tables are found

            # Process the extracted tables
            table_content = [self.fix_header(page.df) if fix else page.df for page in tables]
            result = pd.concat(table_content, ignore_index=True) if len(table_content) > 1 else table_content[0]

            # Adicione esta linha para verificar o conteúdo da tabela
            logging.info(f"Extracted table content: {result}")

            return result

        except Exception as e:
            logging.error(f"Failed to extract tables: {e}")
            return pd.DataFrame()

    def save_csv(self, df, file_name):
        if not os.path.exists(self.csv_path):
            os.makedirs(self.csv_path, exist_ok=True)
        path = os.path.join(self.csv_path, f'{file_name}.csv')

        # Adicione esta linha para verificar o DataFrame antes de salvar
        logging.info(f"DataFrame to be saved: {df}")

        df.to_csv(path, sep=';', index=False, encoding='utf-8')

    def add_infos(self, header, content):
        if header.empty:
            logging.warning("Header está vazio. Informações adicionais não serão adicionadas.")
            return content  # Retorna o conteúdo original sem adicionar informações do cabeçalho

        infos = header.iloc[0]
        df = pd.DataFrame([infos.value] * len(content), columns=header.column.columns)
        content = pd.concat([content.reset_index(drop=True), df.reset_index(drop=True)], axis=1)
        content['Data de Inserção'] = pd.Timestamp('today').normalize()
        return content

    @staticmethod
    def fix_header(df):
        df.columns = df.iloc[0]
        df = df.drop(0)
        df = df.drop(df.columns[0], axis=1)
        return df

    def sanitize_column_names(self, df):
        if df.empty:
            logging.warning("O DataFrame está vazio. Nenhuma coluna para sanitizar.")
            return df

        if not df.columns.is_unique:
            logging.warning("Os nomes das colunas não são únicos. Pode haver problemas na estrutura dos dados.")

        if not all(isinstance(col, str) for col in df.columns):
            logging.warning("Nem todas as colunas têm nomes em formato de string. Verifique a estrutura do DataFrame.")
            df.columns = df.columns.map(str)  # Converte os nomes para strings

        # Substitui espaços por underscores
        df.columns = df.columns.str.replace(' ', '_', regex=False)
        return df

    def send_to_db(self, df, table_name):
        try:
            connection = RDSPostgreSQLManager().alchemy()
            df.to_sql(table_name, connection, if_exists='append', index=False)
            logging.info(f'Dados salvo {table_name}.')
        except Exception as e:
            logging.error(e)

    def visualize_table_areas(self):
        try:
            tables = camelot.read_pdf(
                self.path,
                flavor=self.configs['flavor'],
                table_areas=self.configs['table_areas'],
                columns=self.configs['columns'],
                strip_text=self.configs['strip_text'],
                page=self.configs['pages']
            )
            if tables is None or len(tables) == 0:
                logging.warning(f"No tables found in {self.file_name}. Please check the table areas and columns.")
                return

            for table in tables:
                fig, ax = plt.subplots()
                ax.imshow(table._image, aspect='auto')
                for area in self.configs['table_areas']:
                    x1, y1, x2, y2 = map(float, area.split(','))
                    rect = plt.Rectangle((x1, y1), x2 - x1, y2 - y1, edgecolor='red', facecolor='none')
                    ax.add_patch(rect)
                plt.show()

        except Exception as e:
            logging.error(f"Failed to visualize table areas: {e}")


def list_files(folder):
    try:
        files = [os.path.splitext(f)[0] for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        return files
    except FileNotFoundError:
        logging.info(f"A pasta '{folder}' não foi encontrada.")
        return []
    except Exception as e:
        logging.info(f"Ocorreu um erro: {e}")
        return []


if __name__ == '__main__':
    file_name = 'regra1'
    folder = os.path.abspath(f'files/pdf/{file_name}/')
    files = list_files(folder)
    for file in files:
        extractor = PDFTableExtractor(file, configs=rules_dict[file_name])
        extractor.visualize_table_areas()
        extractor.start()
    logging.info("Todos os arquivos foram processados")