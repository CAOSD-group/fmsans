#!/bin/bash

SCRIPT="main_sat_analysis.py"
AUXFILE="aux.csv"

MODEL=$1
SOLVER=$2
RUNS=$3
OUTPUT="$(basename $1 ".uvl").csv"

touch $OUTPUT
rm $OUTPUT

echo "FM model: $MODEL, SAT solver: $SOLVER"
echo "running $RUNS runs..."
echo -n 1
python $SCRIPT -fm $MODEL -s $SOLVER > $AUXFILE
tail -2 $AUXFILE >> $OUTPUT
for i in $(seq 2 1 $RUNS); do
    echo -n " $i"
    python $SCRIPT -fm $MODEL -s $SOLVER > $AUXFILE
    tail -1 $AUXFILE >> $OUTPUT
done
echo ""
rm $AUXFILE
