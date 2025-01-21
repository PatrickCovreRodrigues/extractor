import os
import camelot
import  pandas as pd
import matplotlib.pyplot as plt
import matplotlib

file_name = 'corretora_jornada_de_dados'
path = os.path.abspath(f'files/pdf/{file_name}.pdf')

tables = camelot.read_pdf(
    path,
    pages='1-end',
    flavor='stream',
    table_areas=['65, 558, 500,298']
)

print(tables[0].parsing_report)
camelot.plot(tables[0], kind='contour')
plt.show()
