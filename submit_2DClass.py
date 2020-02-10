#!/usr/bin/env python3
import json
import argparse
import os
import sys
import subprocess
from check_if_done import check_state_comet
import time
import shutil
from write_submit_script_comet import write_submit_comet
import re

'''
Submit relion 2D classification job.
Inputs: 1. Path of the *particles.star file from particle extraction,
        2. Name of the 2D classification directory,
        3. Diameter of the mask,
        4. Number of classes.
Output: 2D classification results, saved in the output directory.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ## General inputs
    ap.add_argument('-i', '--input',
                    help="Provide star file of the ctf corrected micrographs.")
    ap.add_argument('-o','--output', default='2DClass',
                    help="Name of the directory where the outputs of 2d classification are stored.")
    ap.add_argument('-p', '--program', default='relion_2DClass',
                    help='The program to use to do particle extraction. Currently only supports relion_class2d.')
    ## Program specific parameters
    ap.add_argument('-d', '--diameter',
                    help="Diameter of the particle to be used in 2D classification (in Angstrom).")
    ap.add_argument('-K', '--numclass', default='200',
                    help="Number of classes to be used in 2D classification. Default is 200 (the max allowed).")
    ## Cluster submission needed
    ap.add_argument('--template', default='comet_submit_template.sh',
                    help="Name of the submission template. Currently only supports comet_submit_template.sh")
    ap.add_argument('--cluster', default='comet',
                    help='The computer cluster the job will run on. Currently only supports comet.')
    ap.add_argument('--jobname', default='2DClassification', help='Jobname on the submission script.')
    ap.add_argument('--user_email', help='User email address to send the notification to.')
    ap.add_argument('--walltime', default='72:00:00', help='Expected max run time of the job.')

    args = vars(ap.parse_args())
    return args

def editparameters(s, diameter, k):
    new_s = s.replace('$$diameter', diameter).replace('$$K', k)
    return new_s

def check_good(class_dir):
    '''
    Currently only supports relion 2D classification.
    Check if 'run_it025_model.star' file exists.
    '''
    return os.path.isfile(os.path.join(class_dir, 'run_it025_model.star'))

def submit(**args):

    cluster = args['cluster']
    codedir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    wkdir = os.path.abspath(os.path.join(os.path.dirname(args['input']), os.pardir))
    cluster_config_file='cluster_config.json'
    job_config_file = '2DClass_config.json'

    ## mkdir to setup the job
    os.chdir(wkdir)
    try:
        os.mkdir(args['output'])
    except OSError:
        pass

    os.chdir(codedir)
    with open(cluster_config_file, 'r') as f:
        cluster_config = json.load(f)
    with open(job_config_file, 'r') as f:
        job_config = json.load(f)

    jobname = args['jobname']
    user_email = args['user_email']
    walltime = args['walltime']
    program = args['program']
    specs = 'diam%sk%s'%(args['diameter'], args['numclass'])
    submit_name = 'submit_%s_%s.sh' %(args['program'], specs)
    input = '--i %s '%args['input']
    output_dir = os.path.join(args['output'], specs)
    output = '--o %s/run '%output_dir
    stdout = os.path.join('> %s'%output_dir, 'run_%s.out '%args['program'])
    stderr = os.path.join('2> %s'%output_dir, 'run_%s.err '%args['program'])
    module = 'module load relion/3.0.8_gpu_k80'
    conda_env = ''
    command = 'mpirun -np 5 relion_refine_mpi '
    parameters = editparameters(job_config[program]['parameters'], \
                                args['diameter'], args['numclass'])

    write_submit_comet(codedir, wkdir, submit_name, \
                        jobname, user_email, walltime, \
                        job_config_file, program, \
                        input, output, stdout, stderr, \
                        module, conda_env, command, parameters,\
                        nt_per_node='4', cpus_per_task='6')

    os.chdir(wkdir)
    try:
        shutil.rmtree(output_dir)
        os.mkdir(output_dir)
    except OSError:
        os.mkdir(output_dir) # make "diamxxxkxxx" directory under the output directory

    cmd='sbatch ' + submit_name
    job_id = subprocess.check_output(cmd, shell=True)
    job_id = job_id.decode("utf-8")
    job_id = re.findall('job (\d+)', job_id)[0]
    with open('%s_%s_log.txt' %(args['program'], specs), 'a+') as f:
        f.write('Job submitted. Job ID is %s.\n' %(job_id))
    query_cmd = cluster_config[cluster]['query_cmd']
    keyarg = cluster_config[cluster]['keyarg']
    # os.chdir(codedir) ## cd back to the directory of the code
    return job_id, query_cmd, keyarg


def check_complete(job_id, query_cmd, keyarg):
    ## Below: check every 2 seconds if the job has finished.
    state = check_state_comet(query_cmd, job_id, keyarg)
    start_time = time.time()
    interval = 2
    # i = 1
    # while state!='completed':
    #     time.sleep(start_time + i*interval - time.time())
    #     state = check_state(query_cmd, job_id, keyarg)
    #     i = i + 1
    while state!='completed':
        time.sleep(interval)
        state = check_state_comet(query_cmd, job_id, keyarg)

def check_output_good(**args):
    wkdir = os.path.abspath(os.path.join(os.path.dirname(args['input']), os.pardir))
    os.chdir(wkdir)
    specs = 'diam%sk%s'%(args['diameter'], args['numclass'])
    output_dir = os.path.join(args['output'], specs)
    ## Below: check if the particle picking output is correct.
    with open('%s_%s_log.txt' %(args['program'], specs), 'a+') as f:
        f.write('Checking outputs....\n')
    isgood = check_good(output_dir)
    with open('%s_%s_log.txt' %(args['program'], specs), 'a+') as f:
        if isgood:
            f.write('2D classification for %s has finished.\n'%specs)
        else:
            f.write('Submission job %s is done but the output may not be right. Please check.\n'%specs)

if __name__ == '__main__':
    args = setupParserOptions()
    job_id, query_cmd, keyarg = submit(**args)
    check_complete(job_id, query_cmd, keyarg)
    check_output_good(**args)
