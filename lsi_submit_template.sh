#!/bin/bash
### Job name
#PBS -N $$job_name
### Keep Output and Error
#PBS -k eo
### Queue name
#PBS -q $$queue_name
### Specify the number of nodes and thread (ppn) for your job.
#PBS -l nodes=$$nodes:ppn=20
### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS
#PBS -l walltime=$$walltime
#################################
NSLOTS=$(wc -l $PBS_NODEFILE|awk {'print $1'})

module purge
module load python-anaconda3/latest

$$modules
$$extra
$$conda_env

### Run:
$$command_to_run
