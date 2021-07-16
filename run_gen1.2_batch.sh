#!/bin/sh
#SBATCH --job-name='gen_1.2'
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8GB
#SBATCH --output=gen1.2-%j-stdout.log
#SBATCH --time=4:00:00

PYTHON=/users/hgarsden/anaconda3_herasim/bin/python

# Delete existing output files
rm Gen1.2*.uvh5

echo "Start: `date`"
echo

for yaml in params_gen1.2g.yaml params_gen1.2u.yaml
do
    echo "Running $yaml ==========================================="
    echo
    $PYTHON run_sims.py $yaml True
done

echo
echo "Finish: `date`"

