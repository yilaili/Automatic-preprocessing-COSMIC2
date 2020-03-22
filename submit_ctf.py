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
Submit CTF estimation job.
Inputs: 1. Path to the micrographs star file (micrographs.star),
        2. Path to the directory where the CTF outputs are saved.
Output: Path to the directory where the CTF outputs are saved.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ## General inputs
    ap.add_argument('-i', '--input',
                    help="Provide star file of the micrographs.")
    ap.add_argument('-o', '--output', default='ctf',
                    help="Output directory name for ctf outputs to be located.")
    ap.add_argument('-p', '--program', default='CTFFIND4',
                    help='The program to use to do ctf estimation. Currently only supports CTFFIND4.')
    ## Program specific parameters
    ap.add_argument('--CS', help='Spherical aberration of the microscope')
    ap.add_argument('--HT', help='Kev')
    ap.add_argument('--XMAG', default='10000', help='Magnification')
    ap.add_argument('--DStep', help='Pixel size')
    ## Cluster submission needed
    ap.add_argument('--template', default='lsi_submit_template.sh',
                    help="Name of the submission template.")
    ap.add_argument('--cluster', default='lsi',
                    help='The computer cluster the job will run on.')
    ap.add_argument('--jobname', default='CTF', help='Jobname on the submission script.')
    # ap.add_argument('--user_email', help='User email address to send the notification to.')
    ap.add_argument('--walltime', default='05:00:00', help='Expected max run time of the job.')
    ap.add_argument('--nodes', default='2', help='Number of nodes used in the computer cluster.')
    args = vars(ap.parse_args())
    return args

def editparameters(s, CS, HT, XMAG, DStep):
    new_s = s.replace('$$CS', CS)\
    .replace('$$HT', HT)\
    .replace('$$XMAG', XMAG)\
    .replace('$$DStep', DStep)
    return new_s

def check_good(wkdir, ori_star, ctf_star):
    ### Currenly only work for ctffind4 in relion.
    os.chdir(wkdir)
    cmd = 'grep \'.mrc\' %s | wc -l' %ori_star
    ori_lines = int(subprocess.check_output(cmd, shell=True))
    cmd = 'grep \'.mrc\' %s | wc -l' %ctf_star
    ctf_lines = int(subprocess.check_output(cmd, shell=True))
    return ori_lines == ctf_lines

def submit(**args):

    cluster = args['cluster']
    codedir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    wkdir = os.path.abspath(os.path.dirname(args['input']))
    submit_name = 'submit_%s.sh' %args['program']
    cluster_config_file='cluster_config.json'
    job_config_file = 'ctf_config.json'

    ## mkdir to setup the job
    os.chdir(wkdir)
    try:
        shutil.rmtree(args['output'])
        os.mkdir(args['output'])
    except OSError:
        os.mkdir(args['output'])

    os.chdir(codedir)
    with open(cluster_config_file, 'r') as f:
        cluster_config = json.load(f)
    with open(job_config_file, 'r') as f:
        job_config = json.load(f)

    jobname = args['jobname']
    # user_email = args['user_email']
    walltime = args['walltime']
    program = args['program']
    nodes = args['nodes']
    # np = str(4*int(nodes))
    input = '--i %s ' %args['input']
    output = '--o %s ' %args['output']
    stdout = os.path.join('> %s'%args['output'], 'run_%s.out '%args['program'])
    stderr = os.path.join('2> %s'%args['output'], 'run_%s.err '%args['program'])
    module = 'module load relion/3.0-beta-cluster'
    conda_env = 'conda activate pipeline'
    command = 'mpirun $NSLOTS `which relion_run_ctffind_mpi` '
    parameters = editparameters(job_config[program]['parameters'], \
                                args['CS'], args['HT'], args['XMAG'], args['DStep'])

    write_submit_lsi(codedir, wkdir, submit_name, \
                        jobname, walltime, nodes, \
                        job_config_file, program, \
                        input, output, stdout, stderr, \
                        module, conda_env, command, parameters, \
                        template_file=args['template'],\
                        cluster='lsi')

    os.chdir(wkdir)
    cmd='qsub ' + submit_name
    job_id = subprocess.check_output(cmd, shell=True)
    job_id = job_id.decode("utf-8")
    job_id = re.findall('job (\d+)', job_id)[0]
    with open('%s_log.txt' %args['program'], 'a+') as f:
        f.write('Job submitted. Job ID is %s.\n' %(job_id))
    query_cmd = cluster_config[cluster]['query_cmd']
    keyarg = cluster_config[cluster]['keyarg']
    # os.chdir(codedir) ## cd back to the directory of the code
    return job_id, query_cmd, keyarg

def check_complete(job_id, query_cmd, keyarg, **args):
    wkdir = os.path.abspath(os.path.dirname(args['input']))
    os.chdir(wkdir)
    ## Below: check every 2 seconds if the job has finished.
    state = check_state_lsi(query_cmd, job_id, keyarg)
    start_time = time.time()
    interval = 2
    # i = 1
    # while state!='completed':
    #     time.sleep(start_time + i*interval - time.time())
    #     state = check_state_lsi(query_cmd, job_id, keyarg)
    #     i = i + 1
    while state!='C':
        time.sleep(interval)
        state = check_state_lsi(query_cmd, job_id, keyarg)
    ## Below: check if the ctf output is correct.
    os.chdir(wkdir)
    isgood = check_good(wkdir, args['input'], os.path.join(args['output'], 'micrographs_ctf.star'))
    with open('%s_log.txt' %args['program'], 'a+') as f:
        f.write('Checking outputs....\n')
        if isgood:
            f.write('CTF estimation has finished.\n')
            # print(os.path.join(args['output'], 'micrographs_ctf.star'), end='')
        else:
            f.write('Submission job was done but the output may not be right. Please check.\n')
            print('An error occured. Please check the log file.')

if __name__ == '__main__':
    args = setupParserOptions()
    job_id, query_cmd, keyarg = submit(**args)
    check_complete(job_id, query_cmd, keyarg, **args)
