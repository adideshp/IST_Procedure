# IST_Procedure


## Solution:
The below mentioned steps are for Ubuntu. The user will have to perform minor modifications to install the app on other platforms
### Installation

The application requires Python 3 to run.
Install python 3 from https://realpython.com/installing-python/


virtual environment is a part of standard library for python3. 

Clone the application 
```sh
$ git clone  https://github.com/adideshp/IST_Procedure.git
```


Follow the installation steps as mentioned below,
```sh
$ python3.6 -m venv <NAME_OF_THE_ENVIRONMENT> 
$ source <NAME_OF_THE_ENVIRONMENT>/bin/activate
```
Above mentioned commands create a virtual-env named <NAME_OF_THE_ENVIRONMENT> (This is a custom name). Second command activates the virtual env. Virtual environment creates a isolated environment for all the package installation.

Install all the packages listed in requirements.txt. Follow the steps below,
```sh
$ cd IST_Procedure
$ pip install -r requirements.txt
```

### Starting the application
The application can be started by executing the commands below.

For executing the IST procedure:

```sh
$  python main.py --perform_ist <ClusterName>
```

For updating the CRON jobs
```sh
$  python main.py --update_cron <PATH to python executable>
```

### Output
Output files are generated at the ROOT folder. The default output file names are 'ist_summary.csv' and 'ist_detail.csv'


### Settings
Certain initializations are done in the settings.py file in the Root directory. The user can change the default values with the values of his liking.
