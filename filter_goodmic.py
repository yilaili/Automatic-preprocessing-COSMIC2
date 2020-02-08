#!/usr/bin/env python3

import os
import pandas as pd
import subprocess

'''
Using the star file to filter out bad micrographs in the directory containing the
mrc files. Will create a new folder with the symlinks to the original mrc files.
The original folder remains untouched.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input', default='micrographs',
                    help="Input directory of the micrographs in mrc format.")
    ap.add_argument('-g', '--good_star', default='micrographs_micassess.star',
                    help='The star file outputted by MicAssess.')
    ap.add_argument('-o', '--output', default='good_micrographs',
                    help="Name of the output star file. Default is good_micrographs.star.")

def prepare(wkdir, input, output):
    '''
    Make the output directory, and sym link all the mrc files in the input directory
    to the output directory.
    '''
    try:
        shutil.rmtree(output)
        os.mkdir(output)
    except OSError:
        os.mkdir(output)
    input_mrc = os.path.join(input, '*.mrc')
    cmd = 'ln -s %s %s'%(input_mrc, output)
    subprocess.run(cmd, shell=True)

def star2df(starfile):
    with open(starfile) as f:
        star = f.readlines()

    for i in range(len(star)):
        if 'loop_' in star[i]:
            start_idx = i
            break
    key_idx = []
    for j in range(start_idx+1, len(star)):
        if star[j].startswith('_'):
            key_idx.append(j)

    keys = [star[ii] for ii in key_idx]
    star_df = star[1+key_idx[-1]:]
    star_df = [x.split() for x in star_df]
    star_df = pd.DataFrame(star_df)
    star_df = star_df.dropna()
    star_df.columns = keys

    return star_df

def filter_bad(good_star, output):
    good_mic_df = star2df(good_star)
    good_mic_list = good_mic_df['_rlnMicrographName\n'].tolist()
    mrc_list = os.listdir(output)
    for f in mrc_list:
        if f not in good_mic_list:
            os.remove(f)

def main(**args):
    wkdir = os.path.abspath(os.path.join(args['input'], os.pardir))
    os.chdir(wkdir)
    prepare(wkdir, args['input'], args['output'])
    filter_bad(args['good_star'], args['output'])

if __name__ == '__main__':
    args = setupParserOptions()
    main(**args)
