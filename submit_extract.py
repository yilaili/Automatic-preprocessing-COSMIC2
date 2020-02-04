#!/usr/bin/env python3
import json
import argparse
import os
import sys
import subprocess
from check_if_done import check_state
import time
import shutil
import re
'''
Extract the particles with relion.
Inputs: 1. micrographs_ctf.star,
        2. the PARENT DIRECORY of the directory that has coordinate files.
Output: Extracted particles, organized just like the coordinate directory.
'''
#%%############################################################################
def setupParserOptions():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input',
                    help="Provide absolute path of the star file of the ctf corrected micrographs.")
    ap.add_argument('--coord_dir',
                    help="Provide the absolute path of the PARENT DIRECORY of the directory that has coordinate files.")
    ap.add_argument('--coord_suffix', default='.star',
                    help="Extension name of the coordinate file.")
    ap.add_argument('--part_dir',
                    help="Name of the directory where the extracted particles are stored.")
    # ap.add_argument('--part_star',
    #                 help="Name of the star file of the extracted particles.")
    ap.add_argument('-t', '--template', default='lsi_submit_template.sh',
                    help="Name of the submission template. Currently only supports lsi_submit_template.sh")
    ap.add_argument('-c', '--cluster', default='lsi_cluster',
                    help='The computer cluster the job will run on. Currently only supports lsi_cluster.')
    ap.add_argument('-p', '--program', default='relion_extract',
                    help='The program to use to do particle extraction. Currently only supports relion_extract.')
    ap.add_argument('--size',
                    help="Size of the box for particle extraction (in pixels).")
    ap.add_argument('--bg_radius',
                    help="Radius of the circular mask that will be used to define the background area (in pixels).")
    ap.add_argument('--scale',
                    help="Re-scale the particles to this size (in pixels).")
    ap.add_argument('-j', '--jobname', default='extraction',
                    help='Jobname on the submission script.')
    ap.add_argument('-n', '--nodes', default='5',
                    help='Number of nodes used in the computer cluster.')
    args = vars(ap.parse_args())
    return args

def clusterconfig(cluster, jobname, nodes):
    with open('cluster_config.json', 'r') as f:
        cluster_config = json.load(f)
    cluster_config[cluster]['job_name'] = jobname
    cluster_config[cluster]['nodes'] = nodes
    return cluster_config

def editparameter(s, extract_size, bg_radius, scale):
    new_s = s.replace('$$extract_size', extract_size)\
    .replace('$$bg_radius', bg_radius)\
    .replace('$$scale', scale)
    return new_s

def jobconfig(input, coord_suffix, program, extract_size, bg_radius, scale):
    with open('extract_config.json', 'r') as f:
        job_config = json.load(f)
    job_config['general']['input'] = '--i ' + input + ' '
    job_config['general']['coord_suffix'] = '--coord_suffix ' + coord_suffix + ' '
    # job_config['general']['coord_dir'] = '--coord_dir ' + coord_dir + ' '
    # job_config['general']['part_dir'] = '--part_dir ' + part_dir + ' '
    # job_config['general']['part_star'] = '--part_star ' + part_star + ' '
    # job_config['general']['runout'] = '> ' + os.path.join(part_dir, 'run_extract.out') + ' '
    # job_config['general']['runerr'] = '2> ' + os.path.join(part_dir, 'run_extract.err') + ' '

    s = job_config[program]['parameters']
    job_config[program]['parameters'] = editparameter(s, extract_size, bg_radius, scale)
    return job_config

def check_good(part_dir, coord_dir):
    cmd = 'ls -l *.star | egrep -c \'^-\''
    num_part = int(subprocess.check_output(cmd, shell=True, cwd=os.path.join(part_dir, 'micrographs')))
    num_coord = int(subprocess.check_output(cmd, shell=True, cwd=os.path.join(coord_dir, 'micrographs')))
    return num_part == num_coord

#%%############################################################################
def submit(**args):
    # args = setupParserOptions() #Get input parameters from the command line
    prevdir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    os.chdir(prevdir)

    program = args['program']
    cluster = args['cluster']
    template_file = args['template']
    cluster_config = clusterconfig(cluster, args['jobname'], args['nodes'])

    wkdir = os.path.abspath(os.path.join(args['coord_dir'], os.pardir))
    ## wkdir is the job directory: .../job001
    os.chdir(wkdir)
    ## Below: remove the particle directory if exists, e.g.: rm -r xxxx/job001/extract/
    try:
        shutil.rmtree(args['part_dir'])
    except OSError:
        pass
    ## Below: mkdir particle directory, e.g.: mkdir xxxx/job001/extract/
    try:
        os.mkdir(args['part_dir'])
    except OSError:
        pass
    ## Below: remove the submission file if exists
    # try:
    #     os.remove('submit_extract.sh')
    # except OSError:
    #     pass

    try:
        os.remove('extract_log.txt')
    except OSError:
        pass
    ## Below: mkdir of the subdirecories in the particle directory,
    ## e.g.: mkdir xxxx/job001/extract/cryolo_d130t0.2/
    ## and loop through all directories.
    job_id_list = []
    for subdir in os.listdir(args['coord_dir']):
        ## Find the boxsize used in particle picking.
        try:
            boxsize = int(re.findall('[-+]?\d*\.\d+|\d+', subdir)[0])
        except IndexError:
            pass

        ## Use the boxsize in particle picking to calculate the extraction size, etc..
        ## size = 2*boxsize, scale = 0.5*boxsize, bg_radius = 0.75*0.25*boxsize
        args['size'] = str(int(2 * boxsize))
        scale = int(0.5 * boxsize)
        if scale % 2 == 0:
            args['scale'] = str(scale)
        else:
            args['scale'] = str(scale+1)
        args['bg_radius'] = str(int(0.75 * 0.25 * boxsize))
        # if args['size'] == None:
        #     args['size'] = str(int(2 * boxsize))
        # if args['scale'] == None:
        #     scale = int(0.5 * boxsize)
        #     if scale % 2 == 0:
        #         args['scale'] = str(scale)
        #     else:
        #         args['scale'] = str(scale+1)
        # if args['bg_radius'] == None:
        #     args['bg_radius'] = str(int(0.75 * 0.25 * boxsize))

        os.mkdir(os.path.join(args['part_dir'], subdir))
        os.chdir(prevdir)
        job_config = jobconfig(args['input'], args['coord_suffix'], program, args['size'], args['bg_radius'], args['scale'])

        os.chdir(wkdir)
        coord_dir = os.path.join(args['coord_dir'], subdir)
        part_dir = os.path.join(args['part_dir'], subdir)
        part_star = os.path.join(args['part_dir'], (subdir + 'particles.star'))
        job_config['general']['coord_dir'] = '--coord_dir ' + coord_dir + ' '
        job_config['general']['part_dir'] = '--part_dir ' + part_dir + ' '
        job_config['general']['part_star'] = '--part_star ' + part_star + ' '
        job_config['general']['runout'] = '> ' + os.path.join(part_dir, 'run_extract.out') + ' '
        job_config['general']['runerr'] = '2> ' + os.path.join(part_dir, 'run_extract.err') + ' '

        command = job_config[program]['command'] + \
                    job_config['general']['input'] + \
                    job_config['general']['coord_suffix'] + \
                    job_config['general']['coord_dir'] + \
                    job_config['general']['part_dir'] + \
                    job_config['general']['part_star'] + \
                    job_config[program]['parameters'] + \
                    job_config['general']['runout'] + \
                    job_config['general']['runerr'] + \
                    job_config[program]['tail']

        submit_file = 'submit_extract' + str(boxsize) + '.sh'
        with open(os.path.join(prevdir, template_file), 'r') as f:
            with open(submit_file, 'w') as new_f:
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
        # cmd='qsub submit_extract.sh'
        cmd = 'qsub ' + submit_file
        job_id = subprocess.check_output(cmd, shell=True)
        job_id = job_id[:-1]
        job_id = job_id.decode("utf-8")
        job_id_list.append(job_id)
        with open('extract_log.txt', 'a+') as f:
            f.write('Particle exraction job %s submitted. Job ID is %s.\n' %(subdir, job_id))
        query_cmd = cluster_config[cluster]['query_cmd']
        keyarg = cluster_config[cluster]['keyarg']
        os.chdir(prevdir) ## cd back to the directory of the code
    return job_id_list, query_cmd, keyarg

def check_complete(job_id, query_cmd, keyarg, **args):
    ## Below: check every half minute if the job has finished.
    state = check_state(query_cmd, job_id, keyarg)
    start_time = time.time()
    interval = 30
    i = 1
    while state!='C':
        time.sleep(start_time + i*interval - time.time())
        state = check_state(query_cmd, job_id, keyarg)
        i = i + 1

def check_all_good(**args):
    ## Below: check if the particle picking output is correct.
    # print('Checking outputs....')
    wkdir = os.path.abspath(os.path.join(args['coord_dir'], os.pardir))
    ## wkdir is the job directory: .../job001
    os.chdir(wkdir)
    for subdir in os.listdir(args['coord_dir']):
        isgood = check_good(os.path.join(args['part_dir'], subdir), os.path.join(args['coord_dir'], subdir))
        with open('extract_log.txt', 'a+') as f:
            if isgood:
                f.write('Particle extraction for %s has finished.\n' %(subdir))
            else:
                f.write('Submission job %s is done but the output may not be right. Please check.\n' %(subdir))
                print('An error occured. Please check the log file.')
    print(os.path.join(args['part_dir'], '*particles.star') + '[0]', end='')

#%%############################################################################
if __name__ == '__main__':
    args = setupParserOptions()
    job_id_list, query_cmd, keyarg = submit(**args)
    wkdir = os.path.abspath(os.path.join(args['coord_dir'], os.pardir))
    ## wkdir is the job directory: .../job001
    os.chdir(wkdir)
    with open('extract_log.txt', 'a+') as f:
        f.write('Wait until all jobs are completed....\n')
    i = 0
    for job_id in job_id_list:
        check_complete(job_id, query_cmd, keyarg, **args)
        i = i+1
    with open('extract_log.txt', 'a+') as f:
        f.write('All jobs are completed. Checking outputs....\n')
    check_all_good(**args)
