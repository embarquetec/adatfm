import csv
import re

with open('data/MESONET/2012-2019_formated.txt', 'w', encoding='utf8') as w_fh:
    with open('data/MESONET/2012-2019.txt', 'r', encoding='utf8') as r_fh:
        reader = csv.reader(r_fh)

        for row in reader:
            timetag = re.sub(r"[\s\-:]", "", row[1])
            w_fh.write(f'{timetag[:-2]} - {row[2]}=\n')
