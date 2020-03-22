#!/bin/bash
### Job name
#PBS -N pipeline
### Keep Output and Error
#PBS -k eo
### Queue name
#PBS -q batch
### Specify the number of nodes and thread (ppn) for your job.
#PBS -l nodes=1:ppn=1
### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS
#PBS -l walltime=72:00:00
#################################
module purge
module load python-anaconda3/latest
conda activate pipeline
cd $PBS_O_WORKDIR
bash pipeline.sh > run_pipeline.out 2> run_pipeline.err
