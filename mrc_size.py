#!/usr/bin/env python3
import os
import argparse
import mrcfile
import glob

'''
Input a directory of micrographs in mrc format (must all be the same size).
Output a file named "mrc_size.txt" with the first line is height, second line is width.
'''


def setupParserOptions():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input',
                    help="Input directory of the micrographs in mrc format.")
    args = vars(ap.parse_args())
    return args


def mrc_size(**args):
    wkdir = os.path.abspath(os.path.join(args['input'], os.pardir))
    os.chdir(wkdir)
    mrc_f = os.listdir(args['input'])[0]
    height, width = mrcfile.open(os.path.join(args['input'], mrc_f)).data.shape

    output = 'mrc_size.txt'
    with open(output, 'w') as f:
        f.write('%d\n'%height)
        f.write('%d\n'%width)

    return height, width


if __name__ == '__main__':
    args = setupParserOptions()
    mrc_size(**args)
