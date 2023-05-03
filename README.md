# Table of Contents
- [Table of Contents](#table-of-contents)
- [GFT solver](#gft-solver)
  - [How to use it](#how-to-use-it)
    - [Requirements](#requirements)
    - [Download and installation](#download-and-installation)
    - [Execution of the GFT solver](#execution-of-the-gft-solver)
  
# GFT solver
This repository contains all the resources and artifacts that support the GFT solver as a plugin in [Flama](https://flamapy.github.io/).

## How to use it

### Requirements
Our approach has been implemented 100% in Python and is built on top of [Flama](https://flamapy.github.io/).
In particular, the main dependencies are:

- [Python 3.9+](https://www.python.org/)
- [Flama](https://flamapy.github.io/)

The framework has been tested in Linux (Mint and Ubuntu) and Windows 11.

### Download and installation
1. Install [Python 3.9+](https://www.python.org/)
2. Download/Clone this repository and enter into the main directory.
3. Create a virtual environment: `python -m venv env`
4. Activate the environment: 
   
   In Linux: `source env/bin/activate`

   In Windows: `.\env\Scripts\Activate`

   ** In case that you are running Ubuntu, please install the package python3-dev with the command `sudo apt update && sudo apt install python3-dev` and update wheel and setuptools with the command `pip  install --upgrade pip wheel setuptools` right after step 4.
   
5. Install the dependencies: `pip install -r requirements.txt`


### Execution of the GFT solver
To execute the GFT solver.

  - Execution: `python test_gft_solver.py -fm FEATURE_MODEL`
  - Inputs: 
    - The `FEATURE_MODEL` parameter specifies the file path of the GFT in UVL format.
  - Example: `python test_gft_solver.py -fm models/gfts/JHipster_gft.uvl`


