#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess

TEMP_DIR = '__ipynb2pdf__'

HIDE_CODE_TEMPLATE = """
((*- extends 'article.tplx' -*))

((* block input_group *))
    ((*- if cell.metadata.get('nbconvert', {}).get('show_code', False) -*))
        ((( super() )))
    ((*- endif -*))
((* endblock input_group *))
"""

OLD1 = r'\usepackage[mathletters]{ucs} % Extended unicode (utf-8) support'
NEW1 = r'''\usepackage[mathletters]{ucs} % Extended unicode (utf-8) support

    % ----- INSERTED BLOCK BEGIN -----
    \usepackage[utf8x]{inputenc}
    \usepackage[T1,T2A]{fontenc}
    \usepackage[russian,english]{babel}
    % ----- INSERTED BLOCK END -------
'''
REPLACE = [(OLD1, NEW1)]


def get_ext(file_with_ext):
    last_point_idx = file_with_ext.rfind('.')

    if last_point_idx == -1:
        return (file_with_ext, '')

    file_without_ext = file_with_ext[:last_point_idx]
    ext = file_with_ext[last_point_idx + 1:]
    return (file_without_ext, ext)


def ipynb2tex(filename, hide_code, verbose):
    base, ext = get_ext(filename)
    if ext != '' and ext != 'ipynb':
        print(ext)
        raise RuntimeError(f'Can\'t open "{filename}". Please, check input file correctness.')
    tex_filename = f'{base}.tex'

    if hide_code:
        template_filename = 'hidecode.tplx'
        with open(template_filename, 'w') as template_file:
            template_file.write(HIDE_CODE_TEMPLATE)

        ipynb_to_tex_command = (
            f'jupyter nbconvert {base}.ipynb --to latex '
            f'--template {template_filename} --output {tex_filename}'
        )
    else:
        ipynb_to_tex_command = (
            f'jupyter nbconvert {base}.ipynb '
            f'--to latex --output {tex_filename}'
        )

    if verbose:
        process = subprocess.run(ipynb_to_tex_command,
                                 shell=True,
                                 timeout=5)
    else:
        process = subprocess.run(ipynb_to_tex_command,
                                 shell=True,
                                 timeout=5,
                                 stdout=subprocess.PIPE)
    if process.returncode != 0:
        raise RuntimeError(f'Converting to LaTeX failed. Process returned: {process}')

    for old, new in REPLACE:
        with open(tex_filename, 'r') as tex_file:
            raw_tex = tex_file.read()
        replaced_tex = raw_tex.replace(old, new)
        with open(tex_filename, 'w') as tex_file:
            tex_file.write(replaced_tex)


def tex2pdf(filename_base, verbose):
    if verbose:
        process = subprocess.run(f'pdflatex {filename_base}.tex',
                                 shell=True,
                                 timeout=5)
    else:
        process = subprocess.run(f'pdflatex {filename_base}.tex',
                                 shell=True,
                                 timeout=5,
                                 stdout=subprocess.PIPE)
    if process.returncode != 0:
        raise RuntimeError(f'Converting to pdf failed. Process returned: {process}')


def main(args):
    filename = args.filename
    if not filename.endswith('.ipynb'):
        filename = f'{filename}.ipynb'
    if not os.path.exists(filename):
        print(f'Can\'t open "{filename}". Please, check input file correctness.')
        return

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.mkdir(TEMP_DIR)
    os.chdir(TEMP_DIR)
    os.symlink(f'../{filename}', filename)

    base, ext = get_ext(filename)
    try:

        ipynb2tex(base, args.hide_code, args.verbose)

        out_name = os.path.split(args.output or base)[1]
        print(f'[ipynb2pdf] Converting latex document {base}.tex to {out_name}.pdf')

        tex2pdf(base, args.verbose)

        print('[ipynb2pdf] Conversion done!')

    except RuntimeError as e:
        print(e)

    finally:
        os.chdir('..')
        output = args.output or base
        os.renames(f'{TEMP_DIR}/{base}.pdf', f'{output}.pdf')
        shutil.rmtree(TEMP_DIR)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, help='ipynb file to convert to pdf')
    parser.add_argument('-o', '--output', type=str, help='specify output file')
    parser.add_argument('-v', '--verbose', action='store_true', help='run in verbose mode')
    parser.add_argument('-hc', '--hide-code', action='store_true', help='remove code from output pdf')
    args = parser.parse_args()
    main(args)
