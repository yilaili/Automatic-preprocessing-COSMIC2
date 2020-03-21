#!/bin/bash
###Inherit all current environment variables
#PBS -V
### Job name
#PBS -N $$job_name
### Keep Output and Error
#PBS -k eo
### Queue name
#PBS -q $$queue_name
### Specify the number of nodes and thread (ppn) for your job.
#PBS -l nodes=$$nodes:ppn=$$ppn
### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS
#PBS -l walltime=$$walltime
#################################
NSLOTS=$(wc -l $PBS_NODEFILE|awk {'print $1'})

### Switch to the working directory;
source ~/modules.sh
$$modules
$$extra
cd $PBS_O_WORKDIR
### Run:
$$command_to_run
echo "done"
