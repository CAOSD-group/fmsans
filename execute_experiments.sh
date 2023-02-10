#!/bin/bash

# Execute a given script over all models of a given folder and get statistics of all experiments.
# The given scripts is a script.sh that executes an experiment X times.
# A new .csv file is written with the result of each model.
# This scripts takes 2 inputs:
# The script.sh to be executed (e.g., sat_experiment.sh)
# The folder containing all models to use.


RUNS=30
SOLVER=g3
AUXFILE="aux.csv"

SCRIPT="sat_experiment.sh"
FOLDER=$1
OUTPUT="$(basename $SCRIPT ".sh").csv"

if [ -f $OUTPUT ]; then
    rm $OUTPUT
fi

for MODEL in $(find $FOLDER -name '*.uvl'); do
    echo $MODEL
    OUTPUTMODEL="$(basename $MODEL ".uvl").csv"
    echo "Output in $OUTPUTMODEL"
    $(source $SCRIPT $MODEL $SOLVER $RUNS)
    python 06main_stats_raw2means.py $OUTPUTMODEL 2 3 4 5 6 7 8 9 > $AUXFILE
    if [ -f $OUTPUT ]; then    
        tail -1 $AUXFILE >> $OUTPUT
    else
        tail -2 $AUXFILE > $OUTPUT
    fi
done
rm $AUXFILE
