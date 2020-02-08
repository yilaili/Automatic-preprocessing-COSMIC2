#!/usr/bin/env python3
import os
import pandas as pd
import subprocess
import argparse
import shutil
import numpy as np

'''
Using the output from crYOLO (CBOX) folder, calculate the estimated boxsize of
the picked particle.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input',
                    help="Outputted directory of crYOLO. Should contain the \"CBOX\" directory.")
    ap.add_argument('-o', '--output', default='findsize.txt',
                    help="Will write the estimated boxsize (in Angstrom) into this file.")
    ap.add_argument('--apix', help='Pixel size in Angstrom.')
    args = vars(ap.parse_args())
    return args

def readCBOX(input_dir, partnum_threshold=20):
    '''
    Read all the .cbox files in the directory, return an np.array with all the 
    estimated box sizes.
    Will skip the .cbox file with particle number lower than the partnum_threshold.
    '''
    input_dir = os.path.join(input_dir, 'CBOX')
    for cbox_file in os.listdir(input_dir):
        with open(cbox_file) as f:
            lines = f.readlines()
            if len(lines) >= 20:
                x = np.array([float(l.split()[5]) for l in lines])
                y = np.array([float(l.split()[6]) for l in lines])
                cryolo_boxsizes = np.concatenate([x, y])
    return cryolo_boxsizes            
    
def findsize(cryolo_boxsizes, apix, output):
    '''
    Using cryolo_boxsizes (np array with all the estimated box sizes from crYOLO 
    cbox files), find the size of the particle and write the box size in Angstrom
    to the output file.
    In the output file:
        1st row: final estimated boxsize
        2nd row: mean of all boxsizes
        3rd row: 0.25 quantile
        4th row: 0.75 quantile
        5th row: std of all boxsizes
        6th row: total sample size
        7th row: sample size used to calculate the final boxsize
    The final size is calculated by averaging the 10%-90% boxsize values.
    '''
    cryolo_boxsizes = cryolo_boxsizes * apix # convert to Angstrom
    idx_filter = (cryolo_boxsizes >= np.quantile(cryolo_boxsizes, 0.1)) & (cryolo_boxsizes <= np.quantile(cryolo_boxsizes, 0.9))
    tmp = cryolo_boxsizes[idx_filter]
    final_size = int(np.mean(tmp))
    # Write to the output file
    with open(output, 'w') as f:
        f.write('%d\n'%final_size)
        f.write('%d\n'%np.mean(cryolo_boxsizes))
        f.write('%d\n'%np.quantile(cryolo_boxsizes, 0.25))
        f.write('%d\n'%np.quantile(cryolo_boxsizes, 0.75))
        f.write('%d\n'%np.std(cryolo_boxsizes))
        f.write('%d\n'%len(cryolo_boxsizes))
        f.write('%d\n'%len(tmp))        
    return final_size
        
def main(**args):
    wkdir = os.path.abspath(os.path.join(args['input'], os.pardir))
    os.chdir(wkdir)
    cryolo_boxsizes = readCBOX(args['input'])
    findsize(cryolo_boxsizes, args['apix'], args['output'])

if __name__ == '__main__':
    args = setupParserOptions()
    main(**args)
