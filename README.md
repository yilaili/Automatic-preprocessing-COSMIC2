Automatic preprocessing for cryoEM on LSI cluster (U of Michigan)

Code to run the automatic preprocessing workflow on LSI cluster.

To use:
1. Navigate to the desired directory
2. Example:
```
python submit_pipeline.py --input_dir <directory contains all the micrographs> --CS 2.7 --HT 300 --apix 0.66 --final_apix 1
```
And then:
```
nohup bash pipeline.sh &> log.txt &
```
