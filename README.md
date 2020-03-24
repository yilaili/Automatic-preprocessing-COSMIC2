# Automatic preprocessing for cryoEM on LSI cluster (U of Michigan)

Code to run the automatic preprocessing workflow on LSI cluster.

## First, you need to setup the conda environments

First, setup cryolo:
```
conda create -n cryolo-cpu -c anaconda python=3.6 pyqt=5 cudnn=7.1.2 numpy==1.14.5 cython wxPython==4.0.4 intel-openmp==2019.4
```
```
conda activate cryolo-cpu
```
```
pip install 'cryolo[cpu]'
```
```
conda deactivate
```

Then, setup cryoassess:
```
conda create -n cryoassess-cpu -c anaconda python=3.6 pyqt=5 cudnn=7.1.2 numpy=1.14.5 intel-openmp=2019.4
```
```
pip install tensorflow==1.10.1 keras==2.2.5 Pillow==4.3.0 mrcfile==1.1.2 pandas==0.25.3 opencv-python==4.1.2.30 scikit-image==0.16.2
```
```
conda deactivate
```

Last, setup pipeline:
```
conda create -n pipeline -c anaconda python=3.6 pyqt=5 cudnn=7.1.2 numpy==1.18.1 cython wxPython==4.0.4 intel-openmp==2019.4
```
```
conda activate pipeline
```
```
pip install pandas
```
```
conda deactivate
```

## To use:
Navigate to the desired directory:
```
python submit_pipeline.py --input_dir <directory contains all the micrographs> --CS 2.7 --HT 300 --apix 0.66 --final_apix 1
```
And then:
```
nohup bash pipeline.sh &> log.txt &
```
