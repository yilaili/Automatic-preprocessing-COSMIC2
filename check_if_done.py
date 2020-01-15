#!/usr/bin/env python
import subprocess

def check_state_comet(query_cmd, job_id, keyarg):
    cmd = query_cmd + job_id
    try:
        str = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        str = ''
        # if subprocess.CalledProcessError, means job id is invalid
    try:
        str = str.decode('utf-8')
    except AttributeError:
        pass
    if str == '':
        state = 'completed'
    else:
        state = 'pending or running'
    return state
