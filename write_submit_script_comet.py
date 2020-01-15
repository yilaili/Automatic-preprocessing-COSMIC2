'''
Write the submission script for Comet, given:
1. comet_submit_template.sh
2. cluster_config.json
3. job_config.json for any type of job
4. All the job specific parameters given
'''

import json
import os

def editclusterconfig(jobname, user_email, walltime, \
    cluster_config_file='cluster_config.json', cluster='comet', \
    allocation_name='csd547', partition='gpu', nodes='1', nt_per_node='6', \
    gpu_config='gpu:k80:4', cpus_per_task='2', query_cmd='squeue ', keyarg='job_state = '):

    '''
    Edit the cluster config json file. Default is using a 4 gpu machine (k80) on comet,
    with allocation for the cosmic2 project.
    '''

    with open(cluster_config_file, 'r') as f:
        cluster_config = json.load(f)
    cluster_config[cluster]['job_name'] = jobname
    cluster_config[cluster]['user_email'] = user_email
    cluster_config[cluster]['walltime'] = walltime
    cluster_config[cluster]['allocation_name'] = allocation_name
    cluster_config[cluster]['partition'] = partition
    cluster_config[cluster]['nodes'] = nodes
    cluster_config[cluster]['nt_per_node'] = nt_per_node
    cluster_config[cluster]['gpu_config'] = gpu_config
    cluster_config[cluster]['cpus_per_task'] = cpus_per_task
    cluster_config[cluster]['query_cmd'] = query_cmd
    cluster_config[cluster]['keyarg'] = keyarg
    return cluster_config

def editjobconfig(job_config_file, program, input, output, stdout, stderr, \
    module, conda_env, command, parameters, extra='', tail=''):

    '''
    Edit the job config file with the input information.
    '''

    with open(job_config_file, 'r') as f:
        job_config = json.load(f)
    job_config['general']['input'] = input
    job_config['general']['output'] = output
    job_config['general']['stdout'] = stdout
    job_config['general']['stderr'] = stderr
    job_config[program]['module'] = module
    job_config[program]['extra'] = extra
    job_config[program]['conda_env'] = conda_env
    job_config[program]['command'] = command
    job_config[program]['parameters'] = parameters
    job_config[program]['tail'] = tail
    # s = job_config[program]['parameters']
    # job_config[program]['parameters'] = editparameter(s, model, threshold)
    return job_config

def write_submit_comet(codedir, wkdir, submit_name, \
                        jobname, user_email, walltime, \
                        job_config_file,
                        program, \
                        input, output, stdout, stderr, \
                        module, \
                        conda_env, \
                        command, \
                        parameters, \
                        extra='', \
                        tail='', \
                        template_file='comet_submit_template.sh'
                        cluster_config_file='cluster_config.json', \
                        cluster='comet', \
                        allocation_name='csd547', \
                        partition='gpu', \
                        nodes='1', \
                        nt_per_node='6', \
                        gpu_config='gpu:k80:4', \
                        cpus_per_task='2', \
                        query_cmd='squeue ', \
                        keyarg='job_state = '):
    # wkdir is the directory where the submission file is written into
    # codedir is the directory where all the template files are
    cluster_config = editclusterconfig(jobname, user_email, walltime, \
                                        cluster_config_file='cluster_config.json', \
                                        cluster='comet', \
                                        allocation_name='csd547', \
                                        partition='gpu', \
                                        nodes='1', \
                                        nt_per_node='6', \
                                        gpu_config='gpu:k80:4', \
                                        cpus_per_task='2', \
                                        query_cmd='squeue ', \
                                        keyarg='job_state = ')

    job_config = editjobconfig(job_config_file, \
                                program, \
                                input, output, stdout, stderr, \
                                module, \
                                conda_env, \
                                command, \
                                parameters, \
                                extra='', \
                                tail='')

    command = job_config[program]['command'] + \
                job_config['general']['input'] + \
                job_config['general']['output'] + \
                job_config[program]['parameters'] + \
                job_config['general']['stdout'] + \
                job_config['general']['stderr'] + \
                job_config[program]['tail']

    os.chdir(wkdir)
    ## Below: remove the submission file if exists
    try:
        os.remove(submit_name)
    except OSError:
        pass
    ## Below: write the submission file    
    with open(os.path.join(codedir, template_file), 'r') as f:
        with open(submit_name, 'w') as new_f:
            for line in f:
                newline = line.replace('$$job_name', cluster_config[cluster]['job_name'])\
                .replace('$$walltime', cluster_config[cluster]['walltime'])\
                .replace('$$user_email', cluster_config[cluster]['user_email'])\
                .replace('$$partition', cluster_config[cluster]['partition'])\
                .replace('$$allocation_name', cluster_config[cluster]['allocation_name'])\
                .replace('$$nodes', cluster_config[cluster]['nodes'])\
                .replace('$$nt_per_node', cluster_config[cluster]['nt_per_node'])\
                .replace('$$gpu_config', cluster_config[cluster]['gpu_config'])\
                .replace('$$cpus_per_task', cluster_config[cluster]['cpus_per_task'])\
                .replace('$$modules', job_config[program]['module'])\
                .replace('$$extra', job_config[program]['extra'])\
                .replace('$$conda_env', job_config[program]['conda_env'])\
                .replace('$$command_to_run', command)
                new_f.write(newline)
