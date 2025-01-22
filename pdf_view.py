import os
import camelot
import  pandas as pd
import matplotlib.pyplot as plt
import matplotlib

file_name = 'corretora_jornada_de_dados'
path = os.path.abspath(f'files/pdf/regr1/{file_name}.pdf')

tables = camelot.read_pdf(
    path,
    pages='1-end',
    flavor='stream',
    table_areas=['65, 558, 500,298'],
    columns=['65, 107, 156, 212, 280, 336, 383, 450']
)

print(tables[0].parsing_report)


print(tables[0].df)