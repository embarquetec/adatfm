import os

filelist = sorted(os.listdir('data/REDEMET'))

with open('data/compiled2009-2019.txt', 'a', encoding='utf8') as w_fh:
    for file in filelist:
        with open(f'data/REDEMET/{file}', 'r', encoding='utf8') as r_fh:
            data = r_fh.read()

        w_fh.write(data)

    with open(f'data/MESONET/2012-2019_formated.txt', 'r',
              encoding='utf8') as r_fh:
        data = r_fh.read()
