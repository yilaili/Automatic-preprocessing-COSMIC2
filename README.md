# Automatic-preprocessing-COSMIC2
Automatic preprocessing for cryoEM on COSMIC2

Code to run the automatic preprocessing workflow on COSMIC2.

To use:
1. Navigate to the desired directory
2. Example:
```
python submit_pipeline.py --input_dir <directory contains all the micrographs> --CS 2.7 --HT 300 --apix 0.66 --final_apix 1 --user_email <user email>
```
The code will submit the whole workflow to the cluster and print the Job ID.
Note: The whole workflow job is just a master job. It only uses one core on one node.
From the master job, it will submit different steps as different jobs, using either CPU or GPU nodes, depending on the nature of the job.
You can kill the whole workflow by using the Job ID printed from this script. However, already submitted jobs cannot be canceled.
The Job ID of the all the sub jobs are stored in the log files corresponding to the name of the specific job. For example, Job ID for CTF job can be found in CTFFIND4_log.txt.
