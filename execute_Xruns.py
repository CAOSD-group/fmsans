"""
Example of execution:
    python execute_Xruns.py -r 30 -s main_sat_analysis.py -a "-fm fm_models/fms/Pizzas_complex.uvl -s g3"
"""
import os
import argparse
import subprocess
import locale


PYTHON_SCRIPT_SUMMARIZE_STATS = '06main_summarize_stats.py'
#COLUMNS_VALUES = [str(i) for i in range(4, 13+1)]
COLUMNS_VALUES = ['4']


def main(runs: int, script: str, arguments: list[str]) -> None:
    # Get path and filename
    filepath = arguments[1]
    path, filename = os.path.split(filepath)
    filename = '.'.join(filename.split('.')[:-1])


    results = []
    print(f'Executing {runs} runs: ')
    for i in range(1, runs + 1):
        print(f'{i} ', end='', flush=True)
        process = subprocess.run(args=['python', script, *arguments], stdout=subprocess.PIPE) #, stderr=subprocess.DEVNULL)
        result = process.stdout.decode(locale.getdefaultlocale()[1])
    
        # Parse result:
        result_split = result.split(os.linesep)
        header = result_split[-3]
        #header = f'Run,{header}'
        res = result_split[-2]
        #res = f'{i},{res}'
        if not results:
            results.append(header)
            results.append(res)
        else:
            results.append(res)

    print()
    results_str = os.linesep.join(results)
    print(results_str)

    output_file = os.path.join(path, f'{filename}.csv')
    with open(output_file, 'w', encoding='utf8') as file:
        file.write(results_str)

    # Sumarize stats
    process = subprocess.run(args=['python', PYTHON_SCRIPT_SUMMARIZE_STATS, output_file, *COLUMNS_VALUES], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    result = process.stdout.decode(locale.getdefaultlocale()[1])
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Execute X runs the given script with its arguments.')
    parser.add_argument('-r', '--runs', dest='runs', type=int, required=False, default=1, help='Number of executions (default 1).')
    parser.add_argument('-s', '--script', dest='script', type=str, required=True, help='Python script to execute (.py).')
    parser.add_argument('-a', '--args', dest='args', type=str, required=False, default='', help='Arguments of the script to execute as a single string.')
    args = parser.parse_args()

    arguments = args.args.split()
    main(args.runs, args.script, arguments)
    