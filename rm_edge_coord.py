#!/usr/bin/env python3
import os
import argparse
import pandas as pd
import glob

'''
Loop every coord star files, remove the edge particles.
Edge particle is determined based on the extraction boxsize (2*particle boxsize).
Will not submitted to the cluster. Maybe will later.

e.g.: rm_edge_particles.py -i ./ppicker/ --height 3710 --width 3838 -b 142 --apix 1
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input',
                    help="Path to the ppicker directory")
    ap.add_argument('-b', '--boxsize',
                    help="Boxsize of particle picking (not for later extraction!) in Angstrom")
    ap.add_argument('--apix',
                    help="Pixel size of the original mrc images (e.g. 0.66 A/pixel)")
    ap.add_argument('--height',
                    help="Height of the original mrc images in pixel")
    ap.add_argument('--width',
                    help="Width of the original mrc images in pixel")
    args = vars(ap.parse_args())
    return args


def rm_edge(**args):

    wkdir = os.path.abspath(os.path.join(args['input'], os.pardir))
    os.chdir(wkdir)
    print(wkdir)
    print(glob.glob(os.path.join(args['input'], 'micrographs', '*'))[0])

    boxsize = int(args['boxsize'])
    width = int(args['width'])
    height = int(args['height'])
    apix = float(args['apix'])

    for p in glob.glob(os.path.join(args['input'], 'micrographs', '*')):

        with open(p) as f:
            coord = f.readlines()

        header = coord[0:9]
        coord = coord[9:]
        coord_df = [x.split() for x in coord]
        coord_df = pd.DataFrame(coord_df, dtype=float)
        coord_df = coord_df.dropna()

        good_list = []
        for i in range(len(coord_df)):
            particle = coord_df.iloc[i,:].values
            if particle[0] > (boxsize/apix) and particle[0] < width-(boxsize/apix):
                if particle[1] > (boxsize/apix) and particle[1] < height-(boxsize/apix):
                    good_list.append(coord[i])

        with open(p, 'w') as f:
            for l_0 in header:
                f.write(l_0)
            # for l_1 in good_list:
                # f.write(l_1)

    print('Removed particle coordinates that will clip the micrograph edges.')

if __name__ == '__main__':
    args = setupParserOptions()
    rm_edge(**args)
