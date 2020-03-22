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
Submit MicAssess job.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ## General inputs
    ap.add_argument('-i', '--input',
                    help="Provide the path of the micrograph.star file.")
    ap.add_argument('-o', '--output', default='micrographs_micassess.star',
                    help="Name of the output star file. Default is micrographs_micassess.star.")
    ap.add_argument('-p', '--program', default='micassess',
                    help='The program to use to do micrograph assessment. Currently only supports micassess.')
    ## Program specific parameters
    ap.add_argument('-m', '--model', default='/lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/models/micassess_051419.h5',
                    help="Model file (.h5 file) for MicAssess.")
    ap.add_argument('-t', '--threshold', type=float, default=0.1,
                    help="Threshold for classification. Default is 0.1. Higher number will cause more good micrographs being classified as bad.")
    ap.add_argument('-b', '--batch_size', type=int, default=16,
                    help="Batch size used in prediction. Default is 32. If memory error/warning appears, try lower this number to 16, 8, or even lower.")
    ## Cluster submission needed
    ap.add_argument('--template', default='lsi_submit_template.sh', help="Name of the submission template.")
    ap.add_argument('--cluster', default='lsi', help='The computer cluster the job will run on.')
    ap.add_argument('--jobname', default='MicAssess', help='Jobname on the submission script.')
    # ap.add_argument('--user_email', help='User email address to send the notification to.')
    ap.add_argument('--walltime', default='05:00:00', help='Expected max run time of the job.')
    # ap.add_argument('-n', '--nodes', default='1', help='Number of nodes used in the computer cluster.')
    args = vars(ap.parse_args())
    return args

def editparameters(s, model, threshold):
    new_s = s.replace('$$model', model).replace('$$threshold', str(threshold))
    return new_s

def check_good(output):
    '''
    Check if output file exists.
    '''
    # os.chdir(os.path.dirname(input))
    return os.path.isfile(output)

def submit(**args):

    cluster = args['cluster']
    codedir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    wkdir = os.path.abspath(os.path.dirname(args['input']))
    submit_name = 'submit_%s.sh' %args['program']
    cluster_config_file='cluster_config.json'
    job_config_file = 'micassess_config.json'

    os.chdir(codedir)
    with open(cluster_config_file, 'r') as f:
        cluster_config = json.load(f)
    with open(job_config_file, 'r') as f:
        job_config = json.load(f)

    jobname = args['jobname']
    # user_email = args['user_email']
    walltime = args['walltime']
    program = args['program']
    nodes = '1'
    input = '-i %s ' %args['input']
    output = '-o %s ' %args['output']
    stdout = '> run_%s.out ' %args['program']
    stderr = '2> run_%s.err ' %args['program']
    module = ' '
    conda_env = 'source activate cryoassess-cpu'
    command = 'python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/micassess.py '
    parameters = editparameters(job_config[program]['parameters'], args['model'], args['threshold'])

    write_submit_lsi(codedir, wkdir, submit_name, \
                        jobname, walltime, nodes, \
                        job_config_file, program, \
                        input, output, stdout, stderr, \
                        module, conda_env, command, parameters, \
                        template_file=args['template'], \
                        cluster='lsi')

    cmd='qsub ' + submit_name
    job_id = subprocess.check_output(cmd, shell=True)
    job_id = job_id.decode("utf-8")
    job_id = str(int(job_id))
    with open('%s_log.txt' %args['program'], 'a+') as f:
        f.write('Job submitted. Job ID is %s.\n' %(job_id))
    query_cmd = cluster_config[cluster]['query_cmd']
    keyarg = cluster_config[cluster]['keyarg']
    # os.chdir(codedir) ## cd back to the directory of the code
    return job_id, query_cmd, keyarg

def check_complete(job_id, query_cmd, keyarg):
    ## Below: check every 2 sec if the job has finished.
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

def check_output_good(**args):
    ## Disable all console outputs
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")
    wkdir = os.path.abspath(os.path.dirname(args['input']))
    os.chdir(wkdir)
    print(wkdir)
    ## Below: check if the output is correct.
    with open('%s_log.txt' %args['program'], 'a+') as f:
        f.write('Checking outputs....\n')
    isgood = check_good(args['output'])
    with open('%s_log.txt' %args['program'], 'a+') as f:
        if isgood:
            f.write('Micrograph assessment has finished.\n')
        else:
            f.write('Submission job is done but the output may not be right. Please check.\n')

if __name__ == '__main__':
    args = setupParserOptions()
    job_id, query_cmd, keyarg = submit(**args)
    check_complete(job_id, query_cmd, keyarg)
    check_output_good(**args)
