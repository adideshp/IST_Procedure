# IST_Procedure
The problem is a constraint satisfaction problem. I have developed 2 algorithms that work towards solving the problem.

## Algorithm 1 : Default. Works by finding maximum excess sku in shop.
### CSP_Prob
1. Get total number of products: total_products 
2. initialize variable nth_sku = 1
3. While nth_sku != total_products do
    
      3.1. Get the nth_maximum item from items arranged by their stock availability (inventory - bsq). SKU of the item-> candidate_sku
      
      3.2. For candidate_sku find store (max_prob_shop) that has the maximum probability.
      
      3.3. Verify if transfer can be performed by verifiying all the constraints.
      
      3.4  If transfer is possible, Perform IST
      
      3.5  else increment the nth_sku
4. Return Transfer results


## Algorithm 2 : Default. Works by finding the minimum of requirement * probability.
### CSP

1. Get total number of products: total_products 
2. initialize variable nth_sku = 1
3. While nth_sku != total_products do
    
      3.1. Get the nth_minimum item from items arranged by their (inventory - bsq) * probability score. We call these values as shortage values. SKU of the item-> candidate_sku
      
      3.2. For candidate_sku find store (get_max_supply_shop) that has the maximum numer of excess items.
      
      3.3. Verify if transfer can be performed by verifiying all the constraints.
      
      3.4  If transfer is possible, Perform IST
      
      3.5  else increment the nth_sku
4. Return Transfer results

### Installation
The below mentioned steps are for Ubuntu. The user will have to perform minor modifications to install the app on other platforms

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

### Pending tasks
1. Test cases foe the Algorithms and other scripts
2. Running the code through linter

