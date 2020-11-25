#!/bin/bash
#SBATCH -o stdout.txt  # Name of stdout output file(%%j expands to jobId)
#SBATCH -e stderr.txt  # Name of stderr output file(%%j expands to jobId)
#SBATCH --partition=$$partition     # submit to the ‘large’ queue for jobs > 256 nodes
#SBATCH -J $$job_name    # Job name
#SBATCH -t $$walltime     # Run time (hh:mm:ss)
#SBATCH --mail-user=$$user_email
#SBATCH --mail-type=begin
#SBATCH --mail-type=end
##SBATCH --qos=nsg
#The next line is required if the user has more than one project
# #SBATCH -A A-yourproject # Allocation name to charge job against
#SBATCH -A $$allocation_name # Allocation name to charge job against
#SBATCH --nodes=$$nodes # Total number of nodes requested (16 cores/node)
#SBATCH --ntasks-per-node=$$nt_per_node       # Total number of mpi tasks requested
$$gpu_config
#SBATCH --cpus-per-task=$$cpus_per_task
#SBATCH --no-requeue
#SBATCH --export=NONE
export MODULEPATH=/share/apps/compute/modulefiles/applications:$MODULEPATH
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
module purge
module load anaconda/4.7.12
$$modules
$$extra
__conda_setup="$('/share/apps/compute/anaconda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/share/apps/compute/anaconda/etc/profile.d/conda.sh" ]; then
        . "/share/apps/compute/anaconda/etc/profile.d/conda.sh"
    else
        export PATH="/share/apps/compute/anaconda/bin:$PATH"
    fi
fi
unset __conda_setup

$$conda_env
$$command_to_run
