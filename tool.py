from textwrap import wrap
from os import walk, sep, getcwd, linesep
from os.path import join


# *** replace automated the header in source files ***
def header_from_pkg(pkg):
    new_lines = pkg.__name__,
    new_lines += '-' * len(pkg.__name__),
    new_lines += tuple(wrap(pkg.__doc__))
    new_lines += '',
    new_lines += "Author:   " + pkg.__author__,
    new_lines += "Version:  " + pkg.__version__ + ', copyright ' + pkg.__date__,
    new_lines += "Website:  " + pkg.__url__,
    new_lines += "License:  " + pkg.__license__ + " (see LICENSE file)",
    return ["# -*- coding: utf-8 -*-", ''] + ['# ' + l for l in new_lines] + ['', '']


def replace_header(lines, new_header_lines):
    lines = list(map(str.rstrip, lines))
    while not lines[0] or lines[0].startswith('#'):
        print('remove : ' + lines.pop(0).strip())
    new_lines = new_header_lines + lines
    return new_lines


def replace_headers(rootdir, new_header, test=True):
    for subdir, dirs, files in walk(rootdir):
        for file in files:
            if file.endswith('py'):
                file = join(subdir, file)
                print('\n*** process %s ***\n' % file)

                f = open(file, 'r')
                lines = f.readlines()
                f.close()

                new_lines = replace_header(lines, new_header)
                print('__________')
                print('\n'.join(new_lines[:20]))

                if not test:
                    f = open(file, 'w')
                    f.write(linesep.join(new_lines))
                    f.write(linesep)  # last empty line
                    f.close()


if __name__ == '__main__':
    # replace automated the header in source files
    import dcf as pkg

    root_dir = getcwd() + sep + pkg.__name__
    new_header = header_from_pkg(pkg)
    replace_headers(root_dir, new_header, False)
