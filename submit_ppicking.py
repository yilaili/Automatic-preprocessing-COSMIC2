#!/usr/bin/env python3
import json
import argparse
import os
import sys
import subprocess
from check_if_done import check_state_comet
import time
import shutil
from shutil import copy2
from write_submit_script_comet import write_submit_comet
import re

'''
Submit particle picking job.
Inputs: 1. Path to the directory of the micrographs,
        2. Path to the directory where the outputs are saved,
        3. Boxsize of the particle,
        4. Minimum distance between the neighboring picked particles.
           If not given, distance = 0.5 * boxsize.
Output: Path to the directory where the outputs are saved.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ## General inputs
    ap.add_argument('-i', '--input',
                    help="Provide the directory of mrc files of the micrographs.")
    ap.add_argument('-o', '--output',
                    help="Path of output directory for particle picking outputs to be located.")
    ap.add_argument('-p', '--program', default='cryolo',
                    help='The program to use to do particle picking. Currently only supports cryolo.')
    ## Program specific parameters
    ap.add_argument('--config', default='cryolo_config.json',
                    help='Only if you use cryolo. Configuration file of cryolo.')
    ap.add_argument('--boxsize',
                    help='Only if you use cryolo. The size of the particle picking box, in Angstrom.')
    ap.add_argument('--apix', help='Pixel size in Angstrom.')
    ap.add_argument('--distance',
                    help='Only if you use cryolo. The minimum distance of two picked particles.')
    ap.add_argument('--model', default='/home/yilaili/codes/Automatic-preprocessing-COSMIC2/models/gmodel_phosnet_201912_N63.h5',
                    help='Model of cryolo. Currently only support cryolo.')
    ap.add_argument('--thresh', default='0.1',
                    help='Only if you use cryolo. Threshold number of cryolo.')
    ## Cluster submission needed
    ap.add_argument('--template', default='comet_submit_template.sh',
                    help="Name of the submission template. Currently only supports comet_submit_template.sh")
    ap.add_argument('--cluster', default='comet',
                    help='The computer cluster the job will run on. Currently only supports comet.')
    ap.add_argument('--jobname', default='ppicking', help='Jobname on the submission script.')
    ap.add_argument('--user_email', help='User email address to send the notification to.')
    ap.add_argument('--walltime', default='05:00:00', help='Expected max run time of the job.')
    args = vars(ap.parse_args())
    return args

def editparameters(s, config, model, thresh, distance):
    new_s = s.replace('$$config', config)\
    .replace('$$model', model)\
    .replace('$$thresh', thresh)\
    .replace('$$distance', distance)
    return new_s

def cryolo_editconfig(config, pixel_boxsize):
    ## Edit the config.json file of cryolo according to the given boxsize.
    pixel_boxsize = int(pixel_boxsize)
    with open(config, 'r') as f:
        cryolo_config = json.load(f)
        anchors = [pixel_boxsize, pixel_boxsize]
        cryolo_config['model']['anchors'] = anchors
    new_config = 'boxsize%s_'%pixel_boxsize + config
    with open(new_config, 'w') as f:
        json.dump(cryolo_config, f, indent=4, sort_keys=True)
    return new_config

def check_good(runout):
    '''
    Currently only works for cryolo.
    Check if 'particles in total are found' is in the last 5 lines
    of the run_ppicker.out file.
    '''
    cmd = 'tail -5 '+ runout
    last_line = subprocess.check_output(cmd, shell=True).decode("utf-8")
    str = 'particles in total are found'
    return last_line.find(str) != -1

def submit(**args):

    program = args['program']
    cluster = args['cluster']
    codedir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    wkdir = os.path.abspath(os.path.join(args['input'], os.pardir))
    cluster_config_file='cluster_config.json'
    job_config_file = 'ppicking_config.json'

    ## mkdir to setup the job
    os.chdir(wkdir)
    # Below: remove the output dir if exists
    try:
        shutil.rmtree(args['output'])
    except OSError:
        pass
    # Below: mkdir output
    try:
        os.mkdir(args['output'])
    except OSError:
        pass
    os.chdir(codedir)
    # Below: copy the cryolo_config file to the wkdir.
    try:
        copy2(args['config'], wkdir)
    except OSError:
        pass

    with open(cluster_config_file, 'r') as f:
        cluster_config = json.load(f)
    with open(job_config_file, 'r') as f:
        job_config = json.load(f)

    jobname = args['jobname']
    user_email = args['user_email']
    walltime = args['walltime']
    program = args['program']
    input = '-i %s ' %args['input']
    output = '-o %s ' %args['output']
    stdout = os.path.join('> %s'%args['output'], 'run_%s.out '%args['program'])
    stderr = os.path.join('2> %s'%args['output'], 'run_%s.err '%args['program'])
    module = ' '
    conda_env = 'conda activate cryolo-pipeline'
    command = 'cryolo_predict.py '
    pixel_boxsize = str(int(int(args['boxsize']) / float(args['apix']))) # Convert boxsize from Angstrom to pixels
    suffix = program + '_d' + pixel_boxsize + 't' + args['thresh'] # suffix e.g.: cryolo_d130t0.3
    submit_name = 'submit_%s.sh' %suffix
    # If distance is not given, distance = 0.5 * boxsize
    if args['distance'] == None:
        args['distance'] = str(int(0.5 * int(pixel_boxsize)))

    os.chdir(wkdir)
    edited_config = cryolo_editconfig(args['config'], pixel_boxsize)
    parameters = editparameters(job_config[program]['parameters'], \
                edited_config, args['model'], args['thresh'], args['distance'])
    os.chdir(codedir)
    write_submit_comet(codedir, wkdir, submit_name, \
                        jobname, user_email, walltime, \
                        job_config_file, program, \
                        input, output, stdout, stderr, \
                        module, conda_env, command, parameters)
    os.chdir(wkdir)
    cmd='sbatch ' + submit_name
    job_id = subprocess.check_output(cmd, shell=True)
    job_id = job_id.decode("utf-8")
    job_id = re.findall('job (\d+)', job_id)[0]
    with open('%s_log.txt' %suffix, 'a+') as f:
        f.write('Job submitted. Job ID is %s.\n' %(job_id))
    query_cmd = cluster_config[cluster]['query_cmd']
    keyarg = cluster_config[cluster]['keyarg']
    os.chdir(codedir) ## cd back to the directory of the code
    return job_id, query_cmd, keyarg


def check_complete(job_id, query_cmd, keyarg, **args):

    wkdir = os.path.abspath(os.path.join(args['input'], os.pardir))
    os.chdir(wkdir)
    program = args['program']
    pixel_boxsize = str(int(int(args['boxsize']) / float(args['apix']))) # Convert boxsize from Angstrom to pixels
    suffix = program + '_d' + pixel_boxsize + 't' + args['thresh'] # suffix e.g.: cryolo_d130t0.3

    ## Below: check every 10 seconds if the job has finished.
    state = check_state_comet(query_cmd, job_id, keyarg)
    start_time = time.time()
    interval = 10
    i = 1
    while state!='C':
        time.sleep(start_time + i*interval - time.time())
        state = check_state_comet(query_cmd, job_id, keyarg)
        i = i + 1

    ## Below: check if the particle picking output is correct.
    with open('%s_log.txt' %suffix, 'a+') as f:
        f.write('Submission job %s is done. Checking outputs....\n'%(parameter))
    stdout = os.path.join('> %s'%args['output'], 'run_%s.out '%args['program'])
    isgood = check_good(stdout)
    if isgood:
        os.mkdir(os.path.join(args['output'], 'micrographs'))
        cmd = 'mv '+ os.path.join(os.path.join(args['output'], 'STAR'), '*') \
        + ' ' + os.path.join(args['output'], 'micrographs')
        subprocess.call(cmd, shell=True)
        with open('%s_log.txt' %suffix, 'a+') as f:
            f.write('Particle picking for %s has finished.\n'%suffix)
        # print(args['output'], end='')
    else:
        with open('%s_log.txt' %suffix, 'a+') as f:
            f.write('Submission job %s is done but the output may not be right. Please check.\n'%suffix)
        print('An error occured. Please check the log file.')

if __name__ == '__main__':
    args = setupParserOptions()
    job_id, query_cmd, keyarg = submit(**args)
    check_complete(job_id, query_cmd, keyarg, **args)
