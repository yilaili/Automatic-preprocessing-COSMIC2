input_dir='$$input_dir'
input_star='$$input_star'
CS=$$CS
HT=$$HT
apix=$$apix
final_apix=$$final_apix
start_boxsize=150

module purge
module load python-anaconda3/latest
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
conda activate pipeline

printf 'data_\nloop_\n_rlnMicrographName\n' >> $input_star | ls $input_dir/*.mrc >> $input_star

python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_micassess.py -i $input_star
python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_ctf.py -i micrographs_micassess.star -o ctf --CS $CS --HT $HT --DStep $apix --nodes 2
python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/filter_goodmic.py -i $input_dir -o good_micrographs -g micrographs_micassess.star

mkdir mic_subset
cp --preserve=links `find $input_dir/*.mrc | shuf -n 20` mic_subset
python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_ppicking.py -i mic_subset -o findsize --boxsize $start_boxsize --apix $apix
python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/findsize.py -i findsize -o findsize.txt --apix $apix
rm -r tmp_filtered

size=$(head -1 findsize.txt)
python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_ppicking.py -i good_micrographs -o ppicking --boxsize $size --apix $apix

let extract_size=2*$size
python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_extract.py -i ctf/micrographs_ctf.star --coord_dir ppicking --part_dir extract --part_star particles.star --apix $apix --extract_size $extract_size --nodes 2

# diam1=$(echo "$size*0.5" | bc)
# diam1=${diam1%.*}
# diam2=$(echo "$size*0.8" | bc)
# diam2=${diam2%.*}
diam3=$size
# diam4=$(echo "$size*1.2" | bc)
# diam4=${diam4%.*}
# diam5=$(echo "$size*1.5" | bc)
# diam5=${diam5%.*}

# python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_2DClass.py -i extract/particles.star -d $diam1 --user_email $user_email --nodes 5 &
# python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_2DClass.py -i extract/particles.star -d $diam2 --user_email $user_email --nodes 5 &
python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_2DClass.py -i extract/particles.star -d $diam3 --user_email $user_email --nodes 5 &
# python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_2DClass.py -i extract/particles.star -d $diam4 --user_email $user_email --nodes 8 &
# python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_2DClass.py -i extract/particles.star -d $diam5 --user_email $user_email --nodes 20 &
# wait

python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_2dassess.py -i 2DClass --mrcs_name run_it025_classes.mrcs -o 2DAssess --starfile run_it025_model.star
python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/write_good_particles.py -i run_it025_data.star -c 2DClass -g good_part_frac.txt -o selected_particles.star
mv selected_particles.star extract/

python /lsi/groups/mcianfroccolab/yilai/codes/Automatic-preprocessing-COSMIC2/submit_extract.py -p relion_reextract -i ctf/micrographs_ctf.star --coord_dir ppicking --part_dir reextract --part_star reextract_selected_particles.star --reextract_data_star extract/selected_particles.star --apix $apix --extract_size $extract_size --scaled_apix $final_apix --nodes 2
