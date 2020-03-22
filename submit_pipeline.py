#!/usr/bin/env python3
import json
import argparse
import os
import sys
import subprocess
from check_if_done import check_state_lsi
import time
import shutil
from write_submit_script_lsi import write_submit_lsi
import re

'''
Submit the whole pipeline. This is a python wrapper to submit pipeline.sh to the cluster.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input_dir', default='micrographs', help="Path to the directory with all the micrographs.")
    ap.add_argument('--input_star', default='micrographs.star', help="Name of the micrographs star file. Default is micrographs.star.")
    ap.add_argument('--CS', help='Spherical aberration of the microscope.')
    ap.add_argument('--HT', help='Kev')
    ap.add_argument('--apix', help='The original pixel size in Angstrom (before any scaling).')
    ap.add_argument('--final_apix', default='1.5', help="Final reextracted pixel size in Angstrom. Default is 1.5 Angstrom.")
    ## Cluster submission needed
    # ap.add_argument('--user_email', help='User email address to send the notification to.')
    args = vars(ap.parse_args())
    return args

def submit(**args):
    code_dir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    wkdir = os.getcwd()
    # Below: write the pipeline.sh file in the working directory
    with open(os.path.join(code_dir, 'pipeline.sh'), 'r') as f:
        with open(os.path.join(wkdir, 'pipeline.sh'), 'w') as new_f:
            for line in f:
                new_line = line.replace('$$input_dir', args['input_dir'])\
                .replace('$$input_star', args['input_star'])\
                .replace('$$CS', args['CS'])\
                .replace('$$HT', args['HT'])\
                .replace('$$apix', args['apix'])\
                .replace('$$final_apix', args['final_apix'])
                new_f.write(new_line)
    # Below: copy the submission script
    shutil.copyfile(os.path.join(code_dir, 'submit_pipeline.sh'), os.path.join(wkdir, 'submit_pipeline.sh'))
    # Submit the job and print the job ID (this is the job ID for the whole pipeline.)
    # cmd='qsub submit_pipeline.sh'
    # job_id = subprocess.check_output(cmd, shell=True)
    # job_id = job_id.decode("utf-8")
    # job_id = str(int(job_id))
    # print(job_id)

if __name__ == '__main__':
    args = setupParserOptions()
    submit(**args)
