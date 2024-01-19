for f in $(ls models/evaluation_corpus/heuristics/small); do
    if [ "${f: -4}" == ".uvl" ]; then
        for h in $(seq 0 1 3); do
            for r in $(seq 0 1 29); do
                echo "Model: models/evaluation_corpus/heuristics/small/$f, Heuristic: $h, Run: $r"
                python step2.py -fm models/evaluation_corpus/heuristics/small/$f -c 16 -H $h -r $r
            done
        done
    fi
done


