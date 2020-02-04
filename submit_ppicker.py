#!/usr/bin/env python3
import json
import argparse
import os
import sys
import subprocess
from shutil import copy2
import shutil
from check_if_done import check_state
import time
'''
Submit particle picking job.
Inputs: 1. Path to the directory of the micrographs,
        2. Path to the directory where the outputs are saved,
        3. Boxsize of the particle,
        4. Minimum distance between the neighboring picked particles.
           If not given, distance = 0.8 * boxsize.
Output: Path to the directory where the outputs are saved.
'''
#%%############################################################################
def setupParserOptions():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input',
                    help="Provide the directory of mrc files of the micrographs.")
    ap.add_argument('-o', '--output',
                    help="Path of output directory for particle picking outputs to be located.")
    ap.add_argument('-t', '--template', default='lsi_submit_template.sh',
                    help="Name of the submission template. Currently only supports lsi_submit_template.sh")
    ap.add_argument('-c', '--cluster', default='lsi_cluster',
                    help='The computer cluster the job will run on. Currently only supports lsi_cluster.')
    ap.add_argument('-p', '--program', default='cryolo',
                    help='The program to use to do particle picking. Currently only supports cryolo.')
    ap.add_argument('--config', default='config.json',
                    help='Only if you use cryolo. Configuration file of cryolo.')
    ap.add_argument('-b', '--boxsize',
                    help='Only if you use cryolo. The size of the particle picking box, in Angstrom.')
    ap.add_argument('--apix',
                    help='Pixel size in Angstrom.')
    ap.add_argument('-d', '--distance',
                    help='Only if you use cryolo. The minimum distance of two picked particles.')
    ap.add_argument('--model', default='gmodel_phosnet_20190516.h5',
                    help='Only if you use cryolo. Model of cryolo.')
    ap.add_argument('--thresh', default='0.1',
                    help='Only if you use cryolo. Threshold number of cryolo.')
    ap.add_argument('-j', '--jobname', default='ppicker',
                    help='Jobname on the submission script.')
    ap.add_argument('-n', '--nodes', default='1',
                    help='Number of nodes used in the computer cluster.')
    args = vars(ap.parse_args())
    return args

def clusterconfig(cluster, jobname, nodes):
    with open('cluster_config.json', 'r') as f:
        cluster_config = json.load(f)
    cluster_config[cluster]['job_name'] = jobname
    cluster_config[cluster]['nodes'] = nodes
    return cluster_config

def cryolo_editconfig(config, boxsize):
    ## Edit the config.json file of cryolo according to the given boxsize.
    boxsize=int(boxsize)
    with open(config, 'r') as f:
        cryolo_config = json.load(f)
        anchors = [boxsize, boxsize]
        cryolo_config['model']['anchors'] = anchors
    new_config = 'boxsize%s_'%(boxsize) + config
    with open(new_config, 'w') as f:
        json.dump(cryolo_config, f, indent=4, sort_keys=True)
    return new_config

def cryolo_editparameter(s, config, model, thresh, distance):
    new_s = s.replace('$$config', config)\
    .replace('$$model', model)\
    .replace('$$thresh', thresh)\
    .replace('$$distance', distance)
    return new_s

def jobconfig(indir, outdir, program, config=None, model=None, thresh=None, distance=None):
    with open('ppicker_config.json', 'r') as f:
        job_config = json.load(f)
    job_config['general']['input'] = '-i ' + indir + ' '
    job_config['general']['output'] = '-o ' + outdir + ' '
    job_config['general']['runout'] = '> ' + os.path.join(outdir, 'run_ppicker.out') + ' '
    job_config['general']['runerr'] = '2> ' + os.path.join(outdir, 'run_ppicker.err') + ' '
    if program == 'cryolo':
        s = job_config[program]['parameters']
        job_config[program]['parameters'] = cryolo_editparameter(s, config, model, thresh, distance)
    else:
        job_config[program]['parameters'] = ''
    return job_config

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

#%%############################################################################
def prepare(**args):
    wkdir = os.path.abspath(os.path.join(args['output'], os.pardir))
    os.chdir(wkdir)
    os.mkdir('micrographs_only')
    args['input'] = os.path.basename(os.path.normpath(args['input'])) + '_only'
    cmd = 'ln -s ' + os.path.join(args['input'], '/*.mrc') + ' micrographs_only/'
    subprocess.call(cmd, shell=True, cwd=wkdir)

def submit(**args):
    # args = setupParserOptions() # Get input parameters from the command line
    prevdir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    os.chdir(prevdir)

    program = args['program']
    cluster = args['cluster']
    template_file = args['template']
    args['boxsize'] = str(int(int(args['boxsize']) / float(args['apix'])))
    parameter = program + '_d' + args['boxsize'] + 't' + args['thresh']
    # parameter e.g.: cryolo_d130t0.3
    # indir = os.path.basename(os.path.normpath(args['input'])) + '_only'
    indir = args['input']
    outdir = os.path.join(os.path.basename(os.path.normpath(args['output'])), parameter)
    # outdir e.g.: xxxx/ppicker/cryolo_d130t0.2
    submit_name = 'submit_ppicker_' + parameter + '.sh'
    # submit_name e.g.: submit_ppicker_cryolo_d130t0.2.sh

    # If distance is not given, distance = 0.5 * boxsize
    if args['distance'] == None:
        args['distance'] = str(int(0.5 * int(args['boxsize'])))
        # args['distance'] = '0'

    cluster_config = clusterconfig(cluster, args['jobname'], args['nodes'])
    config = cryolo_editconfig(args['config'], args['boxsize'])
    job_config = jobconfig(indir, outdir, program, config, args['model'], args['thresh'], args['distance'])

    command = job_config[program]['command'] + \
                job_config['general']['input'] + \
                job_config['general']['output'] + \
                job_config[program]['parameters'] + \
                job_config['general']['runout'] + \
                job_config['general']['runerr'] + \
                job_config[program]['tail']

    wkdir = os.path.abspath(os.path.join(args['output'], os.pardir))
    ## wkdir is the job directory: .../job001
    ## Below: copy the configuration and the model files to the wkdir.
    try:
        copy2(args['model'], wkdir)
        copy2(config, wkdir)
    except OSError:
        pass
    os.chdir(wkdir)
    ## Below: remove the outdir if exists, e.g.: xxxx/ppicker/cryolo_d130t0.2/
    try:
        shutil.rmtree(outdir)
    except OSError:
        pass
    ## Below: mkdir output, e.g.: mkdir xxxx/ppicker/
    try:
        os.mkdir(args['output'])
    except OSError:
        pass
    ## Below: mkdir the outdir, e.g.: mkdir xxxx/ppicker/cryolo_d130t0.2/
    try:
        os.mkdir(outdir)
    except OSError:
        pass
    ## Below: remove the submission file if exists
    try:
        os.remove(submit_name)
    except OSError:
        pass

    with open(os.path.join(prevdir, template_file), 'r') as f:
        with open(submit_name, 'w') as new_f:
            for line in f:
                newline = line.replace('$$job_name', cluster_config[cluster]['job_name'])\
                .replace('$$queue_name', cluster_config[cluster]['queue_name'])\
                .replace('$$nodes', cluster_config[cluster]['nodes'])\
                .replace('$$ppn', cluster_config[cluster]['ppn'])\
                .replace('$$walltime', cluster_config[cluster]['walltime'])\
                .replace('$$modules', job_config[program]['module'])\
                .replace('$$extra', job_config[program]['extra'])\
                .replace('$$command_to_run', command)
                new_f.write(newline)
    cmd='qsub ' + submit_name
    job_id = subprocess.check_output(cmd, shell=True)
    job_id = job_id[:-1]
    job_id = job_id.decode("utf-8")

    with open('ppicker_log.txt', 'a+') as f:
        f.write('Job %s submitted. Job ID is %s.\n' %(parameter, job_id))
    query_cmd = cluster_config[cluster]['query_cmd']
    keyarg = cluster_config[cluster]['keyarg']
    os.chdir(prevdir) ## cd back to the directory of the code
    return job_id, query_cmd, keyarg

def check_complete(job_id, query_cmd, keyarg, **args):
    # args = setupParserOptions()
    wkdir = os.path.abspath(os.path.join(args['output'], os.pardir))
    os.chdir(wkdir)

    program = args['program']
    args['boxsize'] = str(int(int(args['boxsize']) / float(args['apix'])))
    parameter = program + '_d' + args['boxsize'] + 't' + args['thresh']
    outdir = os.path.join(args['output'], parameter)

    ## Below: check every half minute if the job has finished.
    state = check_state(query_cmd, job_id, keyarg)
    start_time = time.time()
    interval = 30
    i = 1
    while state!='C':
        time.sleep(start_time + i*interval - time.time())
        state = check_state(query_cmd, job_id, keyarg)
        i = i + 1

    ## Below: check if the particle picking output is correct.
    with open('ppicker_log.txt', 'a+') as f:
        f.write('Submission job %s is done. Checking outputs....\n'%(parameter))
    isgood = check_good(os.path.join(outdir, 'run_ppicker.out'))
    if isgood:
        os.mkdir(os.path.join(outdir, 'micrographs'))
        cmd = 'mv '+ os.path.join(os.path.join(outdir, 'STAR'), '*') \
        + ' ' + os.path.join(outdir, 'micrographs')
        subprocess.call(cmd, shell=True)
        with open('ppicker_log.txt', 'a+') as f:
            f.write('Particle picking for %s has finished.\n'%(parameter))
        print(args['output'], end='')
    else:
        with open('ppicker_log.txt', 'a+') as f:
            f.write('Submission job %s is done but the output may not be right. Please check.\n'%(parameter))
        print('An error occured. Please check the log file.')

#%%############################################################################
if __name__ == '__main__':
    args = setupParserOptions()
    prepare(**args)
    job_id, query_cmd, keyarg = submit(**args)
    check_complete(job_id, query_cmd, keyarg, **args)
