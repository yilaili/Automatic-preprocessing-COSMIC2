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
Submit 2DAssess job to comet.
Will loop through all the subdirectories in the 2DClass folder and submit multiple
corresponding 2DAssess jobs.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ## General inputs
    ap.add_argument('-i', '--input',
                    help="Provide the path of the Relion 2d classification job outputted by the pipeline.")
    ap.add_argument('--mrcs_name',
                    help="Provide the name of the mrcs file (must be the same name for all subdirs) outputted by relion 2d classification.")
    ap.add_argument('-o', '--output', default='2DAssess',
                    help="Name of the output PARENT directory. Default is 2DAssess.")
    ap.add_argument('-p', '--program', default='2dassess',
                    help='The program to use to do micrograph assessment. Currently only supports 2dassess.')
    ## Program specific parameters
    ap.add_argument('-m', '--model', default='/home/yilaili/codes/Automatic-preprocessing-COSMIC2/models/2dassess_062119.h5',
                    help="Model file (.h5 file) for 2DAssess.")
    ap.add_argument('--starfile',
                    help="Name of the _model.star file for the input mrc file.")
    # ap.add_argument('-n', '--name',
    #                 help="Name (prefix) of the particle.")
    ap.add_argument('--outfile', default='good_part_frac.txt',
                    help="Output file to store the fraction of the good particles. Default is good_part_frac.txt.")
    ## Cluster submission needed
    ap.add_argument('--template', default='comet_submit_template.sh',
                    help="Name of the submission template. Currently only supports comet_submit_template.sh")
    ap.add_argument('--cluster', default='comet-gpu',
                    help='The computer cluster the job will run on. Currently only supports comet-gpu.')
    ap.add_argument('--jobname', default='2DAssess',
                    help='Jobname on the submission script.')
    ap.add_argument('--user_email',
                    help='User email address to send the notification to.')
    ap.add_argument('--walltime', default='01:00:00',
                    help='Expected max run time of the job.')
    # ap.add_argument('-n', '--nodes', default='1',
    #                 help='Number of nodes used in the computer cluster.')
    args = vars(ap.parse_args())
    return args

def editparameters(s, model, name, starfile, outfile):
    new_s = s.replace('$$model', model).replace('$$name', name)\
            .replace('$$starfile', starfile).replace('$$outfile', outfile)
    return new_s

def check_good(outfile):
    '''
    Check if outfile exists.
    '''
    # os.chdir(os.path.dirname(input))
    return os.path.isfile(outfile)

def submit(**args):

    cluster = args['cluster']
    codedir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    wkdir = os.path.abspath(os.path.join(args['input'], os.pardir))
    submit_name = 'submit_%s.sh' %args['program']
    cluster_config_file='cluster_config.json'
    job_config_file = '2dassess_config.json'

    os.chdir(wkdir)
    dir_list = os.listdir(args['input'])
    ## Make directories "2DAssess/diamxxxk200" for all available diamxxxk200 in 2DClass
    for name in dir_list:
        output_dir = os.path.join(args['output'], name)
        try:
            shutil.rmtree(output_dir)
        except OSError:
            pass
        os.makedirs(output_dir, exist_ok=True)

    os.chdir(codedir)
    with open(cluster_config_file, 'r') as f:
        cluster_config = json.load(f)
    with open(job_config_file, 'r') as f:
        job_config = json.load(f)

    jobname = args['jobname']
    user_email = args['user_email']
    walltime = args['walltime']
    program = args['program']
    nodes = '1'
    args['starfile'] = os.path.join(args['input'], dir_list[0], args['starfile'])
    args['input'] = os.path.join(args['input'], dir_list[0], args['mrcs_name'])
    args['output'] = os.path.join(args['output'], dir_list[0])
    input = '-i %s ' %args['input']
    output = '-o %s ' %args['output']
    stdout = os.path.join('> %s'%args['output'], 'run_%s.out '%args['program'])
    stderr = os.path.join('2> %s'%args['output'], 'run_%s.err ' %args['program'])
    module = ' '
    conda_env = 'conda activate /projects/cosmic2/conda/cryoassess'
    command = 'python /home/yilaili/codes/Automatic-preprocessing-COSMIC2/2dassess_pipeline.py '
    parameters = editparameters(job_config[program]['parameters'], args['model'], \
                                dir_list[0], args['starfile'], args['outfile'])

    write_submit_comet(codedir, wkdir, submit_name, \
                        jobname, user_email, walltime, nodes, \
                        job_config_file, program, \
                        input, output, stdout, stderr, \
                        module, conda_env, command, parameters, \
                        template_file=args['template'],\
                        cluster='comet-gpu')

    ## Edit submit file so that multiple 2DAssess will be submitted in the same script
    with open(submit_name, encoding='utf-8') as f:
        full_cmd = f.readlines()[-1]
    with open(submit_name, 'a+', encoding='utf-8') as f:
        for name in dir_list[1:]:
            new_full_cmd = full_cmd.replace(dir_list[0], name)
            f.write(new_full_cmd)

    cmd='sbatch ' + submit_name
    job_id = subprocess.check_output(cmd, shell=True)
    job_id = job_id.decode("utf-8")
    job_id = re.findall('job (\d+)', job_id)[0]
    with open('%s_log.txt' %args['program'], 'a+') as f:
        f.write('Job submitted. Job ID is %s.\n' %(job_id))
    query_cmd = cluster_config[cluster]['query_cmd']
    keyarg = cluster_config[cluster]['keyarg']
    # os.chdir(codedir) ## cd back to the directory of the code
    return job_id, query_cmd, keyarg

def check_complete(job_id, query_cmd, keyarg):
    ## Below: check every two sec if the job has finished.
    state = check_state_comet(query_cmd, job_id, keyarg)
    start_time = time.time()
    interval = 2
    # i = 1
    # while state!='completed':
    #     time.sleep(start_time + i*interval - time.time())
    #     state = check_state_comet(query_cmd, job_id, keyarg)
    #     i = i + 1
    while state!='completed':
        time.sleep(interval)
        state = check_state_comet(query_cmd, job_id, keyarg)

def check_output_good(**args):
    ## Disable all console outputs
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")
    wkdir = os.path.abspath(os.path.join(args['input'], os.pardir))
    os.chdir(wkdir)
    # print(wkdir)
    ## Below: check if the output is correct.
    with open('%s_log.txt' %args['program'], 'a+') as f:
        f.write('Checking outputs....\n')
    isgood = check_good(args['outfile'])
    with open('%s_log.txt' %args['program'], 'a+') as f:
        if isgood:
            f.write('2DAssess has finished.\n')
        else:
            f.write('Submission job is done but the output may not be right. Please check.\n')

if __name__ == '__main__':
    args = setupParserOptions()
    job_id, query_cmd, keyarg = submit(**args)
    check_complete(job_id, query_cmd, keyarg)
    check_output_good(**args)
