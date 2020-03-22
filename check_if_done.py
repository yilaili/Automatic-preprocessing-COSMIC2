#!/usr/bin/env python
import subprocess

def check_state_lsi(query_cmd, job_id, keyarg):
    cmd = query_cmd + job_id + ' -f'
    try:
        str = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        # if subprocess.CalledProcessError, means job id is invalid, most likely
        # because job was already done before checking.
        str = keyarg + 'C'
    try:
        str = str.decode('utf-8')
    except AttributeError:
        pass
    state = str[str.find(keyarg) + len(keyarg)]
    return state
