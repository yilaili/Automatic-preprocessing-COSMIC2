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
Extract the particles with relion.
Inputs: 1. micrographs_ctf.star,
        2. the PARENT DIRECORY of the directory that has coordinate files.
Output: Extracted particles, organized just like the coordinate directory.
'''

def setupParserOptions():
    ap = argparse.ArgumentParser()
    ## General inputs
    ap.add_argument('-i', '--input',
                    help="Provide the path of the star file of the ctf corrected micrographs.")
    ap.add_argument('-p', '--program', default='relion_extract',
                    help='The program to use to do particle extraction. Currently only supports relion_extract.')
    ## Program specific parameters
    ap.add_argument('--coord_dir',
                    help="Provide the path of the PARENT DIRECORY of the directory that has coordinate files.")
    ap.add_argument('--coord_suffix', default='.star', help="Extension name of the coordinate file.")
    ap.add_argument('--part_dir', help="Name of the directory where the extracted particles are stored.")
    ap.add_argument('--part_star', help="Name of the star file of the extracted particles.")
    ap.add_argument('--apix', help='The original pixel size in Angstrom (before any scaling).')
    ap.add_argument('--scaled_apix', default='3',
                    help="The desired pixel size in Angstrom after scaling. Default is 3 Angstrom.")
    ap.add_argument('--extract_size', help="Size of the box for particle extraction (in pixels). Usually is 2*particle_diameter.")
    ## Cluster submission needed
    ap.add_argument('--template', default='comet_submit_template.sh',
                    help="Name of the submission template. Currently only supports comet_submit_template.sh")
    ap.add_argument('--cluster', default='comet',
                    help='The computer cluster the job will run on. Currently only supports comet.')
    ap.add_argument('--jobname', default='Extraction', help='Jobname on the submission script.')
    ap.add_argument('--user_email', help='User email address to send the notification to.')
    ap.add_argument('--walltime', default='05:00:00', help='Expected max run time of the job.')
    args = vars(ap.parse_args())
    return args

def editparameters(s, coord_suffix, coord_dir, part_dir, part_star, extract_size, bg_radius, scale):
    new_s = s.replace('$$coord_suffix', coord_suffix)\
    .replace('$$coord_dir', coord_dir)\
    .replace('$$part_dir', part_dir)\
    .replace('$$part_star', part_star)\
    .replace('$$extract_size', extract_size)\
    .replace('$$bg_radius', bg_radius)\
    .replace('$$scale', scale)
    return new_s

def check_good(part_dir, coord_dir):
    cmd = 'ls -l *.star | egrep -c \'^-\''
    num_part = int(subprocess.check_output(cmd, shell=True, cwd=os.path.join(part_dir, 'micrographs')))
    num_coord = int(subprocess.check_output(cmd, shell=True, cwd=os.path.join(coord_dir, 'micrographs')))
    return num_part == num_coord

def submit(**args):

    cluster = args['cluster']
    codedir = os.path.abspath(os.path.join(os.path.realpath(sys.argv[0]), os.pardir))
    wkdir = os.path.abspath(os.path.join(os.path.dirname(args['input']), os.pardir))
    submit_name = 'submit_%s.sh' %args['program']
    cluster_config_file='cluster_config.json'
    job_config_file = 'extract_config.json'

    ## mkdir to setup the job
    os.chdir(wkdir)
    try:
        shutil.rmtree(args['part_dir'])
        os.mkdir(args['part_dir'])
    except OSError:
        os.mkdir(args['part_dir'])

    os.chdir(codedir)
    with open(cluster_config_file, 'r') as f:
        cluster_config = json.load(f)
    with open(job_config_file, 'r') as f:
        job_config = json.load(f)

    jobname = args['jobname']
    user_email = args['user_email']
    walltime = args['walltime']
    program = args['program']
    input = '--i %s ' %args['input']
    output = ''
    args['part_star'] = os.path.join(args['part_dir'], args['part_star']) # particle star file should be inside the particle dir folder
    stdout = os.path.join('> %s'%args['part_dir'], 'run_%s.out '%args['program'])
    stderr = os.path.join('2> %s'%args['part_dir'], 'run_%s.err '%args['program'])
    module = 'module load relion/3.0.8_gpu_k80'
    conda_env = ''
    command = 'mpirun -np 24 relion_preprocess_mpi '

    scale_factor = float(args['scaled_apix'])/float(args['apix'])
    scale = int(int(args['extract_size']) / scale_factor * 0.5) * 2
    bg_radius = int(0.75 * 0.5 * scale)
    scale = str(scale)
    bg_radius = str(bg_radius)

    parameters = editparameters(job_config[program]['parameters'], \
                                args['coord_suffix'], args['coord_dir'], \
                                args['part_dir'], args['part_star'], \
                                args['extract_size'], bg_radius, scale)

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
    with open('%s_log.txt' %args['program'], 'a+') as f:
        f.write('Job submitted. Job ID is %s.\n' %(job_id))
    query_cmd = cluster_config[cluster]['query_cmd']
    keyarg = cluster_config[cluster]['keyarg']
    # os.chdir(codedir) ## cd back to the directory of the code
    return job_id, query_cmd, keyarg

def check_complete(job_id, query_cmd, keyarg, **args):
    ## Below: check every 10 seconds if the job has finished.
    state = check_state_comet(query_cmd, job_id, keyarg)
    start_time = time.time()
    interval = 10
    # i = 1
    # while state!='completed':
    #     time.sleep(start_time + i*interval - time.time())
    #     state = check_state(query_cmd, job_id, keyarg)
    #     i = i + 1
    while state!='completed':
        time.sleep(interval)
        state = check_state_comet(query_cmd, job_id, keyarg)

    ## Below: check if the particle picking output is correct.
    isgood = check_good(args['part_dir'], args['coord_dir'])
    with open('%s_log.txt' %args['program'], 'a+') as f:
        if isgood:
            f.write('Particle extraction has finished.\n')
        else:
            f.write('Submission job was done but the output may not be right. Please check.\n')
            print('An error occured. Please check the log file.')

if __name__ == '__main__':
    args = setupParserOptions()
    job_id, query_cmd, keyarg = submit(**args)
    check_complete(job_id, query_cmd, keyarg, **args)
