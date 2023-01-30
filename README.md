# Table of Contents
- [Table of Contents](#table-of-contents)
- [FM Solver](#fm-solver)
  - [Artifact description](#artifact-description)
  - [How to use it](#how-to-use-it)
    - [Requirements](#requirements)
    - [Download and install](#download-and-install)
    - [Execution](#execution)
    - [Configuration](#configuration)
  
# FM Solver
*FM Solver* is a solver and a set of utils for feature models that implement analysis operations without the need of a SAT, #SAT, or BDD solver.


It relies on the concept of an *FMSans*. An *FMSans* is a feature model in which cross-tree constraints have been completely refactored into the feature diagram. Thus, all cross-tree constraints are eliminated from the feature model.
First, complex constraints are refactored using the approach of [Knüppel et al.](https://doi.org/10.1145/3106237.3106252).
Then, simple constraints (requires and excludes) are refactored using the approach of [van den Broek et al.](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=97c0f26a89db833e41113421c8c1e4633370cb82). 
However, since the latter approach is demonstrated that it does not scale in memory, *FMSans* codifies the transformations that need to be performed over the feature model in order to refactor the simple constraints, passing the memory complexity to time complexity.
FMSans exploits parallellization for efficiency.

## Artifact description
*FM Solver* is composed by a set of Python scripts to manage FMSans:
- `fm_to_fmsans.py`: It converts a feature model to an FMSans (.json) and optionally to a full feature model without constraints (.uvl).
- **TO DO**

## How to use it

### Requirements
The implementation of *FM Solver* relies on the Python programming language. 
By convention, all requirements are depicted in the `requirements.txt` file. 
In particular, the dependencies are:

- [Python 3.9+](https://www.python.org/)
- [Flama](https://flamapy.github.io/)
- [YAML](https://pyyaml.org/)

The framework has been tested in Linux and Windows.

### Download and install
1. Install [Python 3.9+](https://www.python.org/)
2. Clone this repository and enter into the main directory:

    `git clone https://github.com/jmhorcas/fm_solver.git`

    `cd fm_solver`

3. Create a virtual environment: `python -m venv env`

4. Activate the environment: 
   
   In Linux: `source env/bin/activate`

   In Windows: `.\env\Scripts\Activate`

   ** In case that you are running Ubuntu, please install the package python3-dev with the command `sudo apt update && sudo apt install python3-dev` and update wheel and setuptools with the command `pip  install --upgrade pip wheel setuptools` right after step 4.
   
5. Install the dependencies: `pip install -r requirements.txt`


### Execution
- To convert a feature model (.uvl) to an FMSans (.json), execute: 
    
    `python fm_to_fmsans.py -fm FEATURE_MODEL [-o]`

    The `FEATURE_MODEL` parameter is mandatory and specifies the file path of the feature model in UVL format.
    
    The `-o` argument is optional, if provided, the full feature model without constraints is also generated as output in UVL format.

- To analyze a feature model using *FM Solver*, execute:
    
    **UNDER CONSTRUCTION**

### Configuration
By default, the scripts also generate two log files: 

(1) `fm_solver.log` with useful information of the process including execution times and memory profilers.

(2) `fm_stats.log` with statistics of the input and output feature models.

These logs can be activated/deactivated and configured using the following configuration files and parameters:

- Configuration file for logs: `logging_config.yml`

  - To completely activate/deactivate the logs, set the `disabled` param to `yes/no` (default `no`), for each logger you want to activate/deactivate:

    The `main_logger` manages the `fm_solver.log` file.

    The `fm_logger` manages the `fm_stats.log` file.

  - To change the log LEVEL, change the `level` param to `DEBUG` or `INFO`. Currently, only the `main_logger` is configurable.

  - To change the output file for the logs, change the `filename` param for each logger.

- Global configuration file: `config.yml`

  - To activate/deactivate the Timer in charge of calculating the execution time of several subprocess, set the `timer_enabled` param to `yes/no` (default `yes`)

  - To activate/deactivate the Sizer in charge of calculating the memory usage of the feature model, set the `sizer_enabled` param to `yes/no` (default `yes`)

  - To activate/deactivate the Memory Profiler in charge of calculating the memory usage of the several subprocess, set the `memoryprofiler_enabled` param to `yes/no` (default `yes`)

