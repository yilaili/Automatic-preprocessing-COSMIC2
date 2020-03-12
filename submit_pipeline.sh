#!/bin/bash
#SBATCH -o stdout.txt  # Name of stdout output file(%%j expands to jobId)
#SBATCH -e stderr.txt  # Name of stderr output file(%%j expands to jobId)
#SBATCH --partition=shared     # submit to the ‘large’ queue for jobs > 256 nodes
#SBATCH -J Pipeline    # Job name
#SBATCH -t 48:00:00     # Run time (hh:mm:ss)
#SBATCH --mail-user=yilai@umich.edu
#SBATCH --mail-type=begin
#SBATCH --mail-type=end
##SBATCH --qos=nsg
#The next line is required if the user has more than one project
# #SBATCH -A A-yourproject # Allocation name to charge job against
#SBATCH -A csd547 # Allocation name to charge job against
#SBATCH --nodes=1 # Total number of nodes requested (16 cores/node)
#SBATCH --ntasks-per-node=1       # Total number of mpi tasks requested
#SBATCH --cpus-per-task=1
#SBATCH --no-requeue
export MODULEPATH=/share/apps/compute/modulefiles/applications:$MODULEPATH
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
module purge

bash pipeline.sh > run_pipeline.out 2> run_pipline.err
