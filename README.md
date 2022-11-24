# General description of the project
This project implements a tool generating explanations for end-users of combinatorial optimization systems 
solving a Workforce Scheduling and Routing Problem (WSRP). \
It contains various objects including:
ones for modeling WSRP instances and solutions as well as 
ones for modeling explanations about WSRP solutions, \
It contains various algorithms, among others: 
algorithms for solving WSRP instances, for checking WSRP solutions feasibility, for generating explanations. \
It contains a web interface for testing the explanation tool in a user-friendly way.


# 1. Description of the project content

## 1.1. Description of the root directory
The directory `src` contains the source code of the project. 
The directory `data` contains the data used in the project (including instances and solutions for demo). 
The directory `inputs` is where input data must be located when one wants to run the `__main__.py` script.
The directory `outputs` is where output data, if any, will be located after one has run the `__main__.py` script. \
The file `__main__.py` is the main script of the project.
The file `configuration.py` contains the configuration of the project. \
The file `requirements_with_gurobi.txt` contains the list of Python packages required to run the entire project.
The file `requirements.txt` contains the list of Python packages required to 
run the web application deployed on Heroku. \
The file `Procfile` is used by Heroku to run the project.


## 1.2. Description of the `src` directory
The directory `utils` contains various utility functions and global variables. \
The directory `modeling` contains the objects used to model WSRP instances and solutions. \
The directory `optimization` contains the scripts used for solving WSRP instances. \
The directory `drawing` contains the scripts used for representing WSRP solutions. \
The directory `checking` contains the scripts used for checking WSRP solutions feasibility. \
The directory `explaining` contains the scripts used for generating explanations. \
The directory `evaluation` contains the scripts related to the evaluation of the explanations. \
The directory `reading` contains the scripts used for reading WSRP instances and solutions 
given as Excel and txt files. \
The directory `writing` contains the scripts used for writing WSRP solutions


# 2. Using the project

## 2.1. Installing the project
This project has been developed and tested in Python 3.9.6. We recommend using this version of Python. \
To install the project, start by creating and activating a virtual environment using the following commands:
```
python -m venv env
source env/bin/activate
```
Then, install the required packages. If you have a Gurobi license, then use the following command:
```
pip install -r requirements_with_gurobi.txt
```
If you do not have a Gurobi license, then use the following command:
```
pip install -r requirements.txt
```
NB: in this second case, using Gurobi will have to be disabled in the `configuration.py` file (see next section).


## 2.2. Running the project
To run the project, start by providing the input data 
(usually one or several instances and their corresponding solutions)
in the `inputs` directory. \
Then, edit the `configuration.py`.
Choose which routine you want to execute by assigning the right value to `ROUTINE`.
Choose in which language you want the explanations as well as the web interface to be written in 
by assigning the right value to `LANGUAGE`.
Choose whether you want to use Gurobi or not by assigning the right value to `USE_GUROBI`.
In case, you do not have a Gurobi license, the value of `USE_GUROBI` must be set to `False`. \
Finally, run the `__main__.py` script using the following command:
```
python __main__.py
```


# 3. Notes for the developers
Each time you add a new Python package to the project, 
it must be added to both of the `requirements_without_gurobi.txt` and `requirements.txt` files. \
Each time the project is pushed to Heroku,
the variable `USE_GUROBI` must be set to `False` in the `configuration.py` file (as Heroku cannot use Gurobi). 
