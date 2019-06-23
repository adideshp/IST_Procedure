from datetime import datetime
import multiprocessing as mp
from algorithm import Algorithm
from csp_algorithm import CSP

import csv
import numpy as np
from numpy import zeros


def execute_algo(i):
    detail_list =[]
    temp = ItemDetails("STORE_D1",str(i),1,10,0.6)
    detail_list.append(temp)
    temp = ItemDetails("STORE_E1",str(i),20,1,0.8)
    detail_list.append(temp)
    temp = ItemDetails("STORE_E2",str(i),8,2,0.8)
    detail_list.append(temp)
    temp = ItemDetails("STORE_D2",str(i),2,8,0.7)
    detail_list.append(temp)
    strategy = DefaultAlgorithm(detail_list)
    algorithm = Algorithm(strategy)
    ist_list, ist_details = algorithm.execute(max_orders=5, min_qty=5, exclusion_list=[])
    return ist_list, ist_details



def create_input_array():
    sku_map = {}
    reverse_sku_map = {}
    reverse_store_map = {}
    sku_index = 0
    store_map = {}
    store_index = 0
    #zeros([3,5])

    with open('MVIST_Data/current_store_inventory.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                if not(row[0] in sku_map):
                    sku_map[row[0]] = sku_index
                    reverse_sku_map[sku_index] = row[0]
                    sku_index += 1
                if not(row[1] in store_map):
                    store_map[row[1]] = store_index
                    reverse_store_map[store_index] = row[1]
                    store_index += 1
                
                line_count += 1

    return sku_map, reverse_sku_map, store_map, reverse_store_map


def valid_quantity_limit(limit, shop_index, transfer):
    """
    transfering store transfering shop do not execeed transfer greater than limit(50) units
    """
    total_qty = np.sum(transfer[shop_index,:]) 
    return limit - total_qty



def valid_shop_to_shop_transfer_limit(limit, shop_index, transfer):
    """
    max shop to shop transfer is less than limit (5)
    """
    non_zero = np.nonzero(transfer[shop_index,:])[0].shape[0]
    if non_zero > limit:
        return False
    else:
        return True


def get_nth_minimum(n, array_2d):
    result = np.vstack(np.unravel_index(np.argpartition(array_2d.flatten(), n)[n], array_2d.shape)).T
    return result[0]


def get_nth_maximum(n, array_2d):
    result = np.vstack(np.unravel_index(np.argpartition(array_2d.flatten(), np.negative(n))[np.negative(n)], array_2d.shape)).T
    return result[0]


def get_deficit_sku_list(shop_index, requirement_all_sku):
    deficit_sku = np.where(requirement_all_sku < 0)
    return deficit_sku


def get_excess_sku_list(shop_index, requirement_all_sku):
    excess_sku = np.where(requirement_all_sku > 0)
    return excess_sku    


def get_transferable_units(deficit_sku, excess_shop_index, deficit_shop_index, requirement):
    transfer_units = 0
    if requirement[deficit_sku, excess_shop_index] < abs(requirement[deficit_sku, deficit_shop_index]):
        #deficit is more than available units. transfer available units
        transfer_units = requirement[deficit_sku, excess_shop_index]
    else:
        #Available units are more than required. transfer all that are required
        transfer_units = abs(requirement[deficit_sku, deficit_shop_index])
    return transfer_units
            

def get_ist_estimate(deficit_shop_index, excess_shop_index, requirement, candidate_sku_index, qty_limit):
    
    total_ist_qty = 0
    transactions = []
    #Check if the IST for candidate SKU is valid
    total_ist_qty =  get_transferable_units(candidate_sku_index, excess_shop_index, deficit_shop_index, requirement)
    if total_ist_qty > qty_limit:
        transactions.append((candidate_sku_index, qty_limit))
        return qty_limit, transactions
    transactions.append((candidate_sku_index, total_ist_qty))
    
    source_deficit_sku = get_deficit_sku_list(deficit_shop_index, requirement[:, deficit_shop_index])[0]
    dest_excess_sku = get_excess_sku_list(excess_shop_index, requirement[:, excess_shop_index])[0]
    
    
    for deficit_sku in source_deficit_sku:
        if deficit_sku == candidate_sku_index:
            continue
        if deficit_sku in dest_excess_sku and total_ist_qty < qty_limit:
            transfer_units = get_transferable_units(deficit_sku, excess_shop_index, deficit_shop_index, requirement)          
            if (total_ist_qty + transfer_units > qty_limit):
                transfer_units = qty_limit - total_ist_qty
            
            total_ist_qty += transfer_units
            #Storing all the possible transfers
            transactions.append((deficit_sku, transfer_units))

    return total_ist_qty, transactions


def get_max_supply_shop(candidate_sku_index, source_shop_index, inventory, requirement, transfer):
    index = 1
    
    while(index != transfer.shape[0]):
        #Check for shop that has the max qty of candidate_sku 
        max_supply_shop_index =  get_nth_maximum(index, inventory[candidate_sku_index,:])[0]
        if max_supply_shop_index == source_shop_index:
            index +=1
            continue
        qty_limit = valid_quantity_limit(50, max_supply_shop_index, transfer)
        if qty_limit > 0:
            if valid_shop_to_shop_transfer_limit(5, max_supply_shop_index, transfer) == True:
                #Amongst all the SKUs now check if: all the transfers can lead to item_qyty >5
                prob_transfer_units, transcations = get_ist_estimate(source_shop_index, max_supply_shop_index, requirement, candidate_sku_index, qty_limit)
                if  prob_transfer_units >= 5 and prob_transfer_units <= 50:
                    return max_supply_shop_index, transcations, prob_transfer_units     
        #Look for next max_supply_shop
        index +=1
    #No valid shop found 
    return -1, [], 0


def perform_ist(dest_store, source_store, transactions, total_transfers, inventory, requirement, shortage, transfer, probability, sku_map, reverse_sku_map, store_map, reverse_store_map):
    """
    Update all the data structures that indicate a IST
    inventory[sku,store]
    requirement[sku,store] 
    shortage[sku,store]
    transfer[store, store]
    """
    for tx in transactions: 
        #Update Inventory
        inventory[tx[0], dest_store]  += tx[1]
        inventory[tx[0], source_store]  -= tx[1]

        #Update requirement
        requirement[tx[0], dest_store]  -= tx[1]  #Subtracting as the req will be -ve
        requirement[tx[0], source_store]  -= tx[1]

        #Update shortage
        shortage[tx[0], dest_store] = requirement[tx[0], dest_store] * probability[tx[0], dest_store]
        shortage[tx[0], source_store] = requirement[tx[0], source_store] * probability[tx[0], source_store]

    #Update transfer
    transfer[source_store, dest_store] += total_transfers
    print("Transfer from " + str(reverse_store_map[source_store]) + " to " + str(reverse_store_map[dest_store]) + " : " + str(total_transfers)) 

    
    return inventory, requirement, shortage, transfer






"""
def transfer_products_making_min_store_transfer(limit)
"""



def main():
    sku_map, reverse_sku_map, store_map, reverse_store_map = create_input_array()
    
    inventory = zeros([len(sku_map), len(store_map)])
    requirement = zeros([len(sku_map), len(store_map)])
    shortage = zeros([len(sku_map), len(store_map)])
    probability = zeros([len(sku_map), len(store_map)])
    transfer = zeros([len(store_map), len(store_map)])
    transfer_detail = zeros([len(sku_map), len(store_map)])

    with open('MVIST_Data/current_store_inventory.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                inventory[sku_map[row[0]]][store_map[row[1]]] =  int(row[2])

    with open('MVIST_Data/bsq.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                requirement[sku_map[row[0]]][store_map[row[1]]] =  inventory[sku_map[row[0]]][store_map[row[1]]] - int(row[2])

    with open('MVIST_Data/projected_probability.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                probability[sku_map[row[0]]][store_map[row[1]]] =  float(row[2])
                shortage[sku_map[row[0]]][store_map[row[1]]] =  float(row[2]) * requirement[sku_map[row[0]]][store_map[row[1]]]

    """
    Logic:
    1. Find the sku,store pair with minimum value in shortage array
    2. Try to reduce the shortage by transferring items from the same row that has highest probability.
    3. While transfer, ensure 
        3a transfering store transfering shop do not execeed transfer greater than 50 units, 
        3b smax shop to shop transfer is less than 5
        3c look for other products in the candidate shop to ensure than the items transfered are greater than 5

    """
    
    total_sku_count = inventory.shape[0]
    nth_sku = 1
    while(nth_sku != total_sku_count):
        #Get location of nth sku and corrosponding store
        min_sku, min_store = get_nth_minimum(nth_sku, shortage) 
        #Get shop that can satisfy all the algo conditions   
        shop_index, transactions, total_transfers = get_max_supply_shop(min_sku, min_store, inventory, requirement, transfer)
        if (shop_index == -1):
            #No shop found
            nth_sku +=1
            continue
        else:
            inventory, requirement, shortage, transfer = perform_ist(min_store, shop_index, transactions, total_transfers, inventory, requirement, shortage, transfer, probability, sku_map, reverse_sku_map, store_map, reverse_store_map)


    print("VALIDATION")
    for index in range(0,transfer.shape[0]):
        s = np.sum(transfer[index,:])
        temp = transfer[index,:]
        m = np.amin(temp[temp > 0])
        non_zero = np.nonzero(transfer[index,:])[0]
        print("Total Transfers from " + str(reverse_store_map[index] + " = " + str(s)) + " | min : " + str(m) + " | total orders:" + str(non_zero.shape[0]))

    import pdb; pdb.set_trace()


if __name__ == '__main__':
    sku_map = {} 
    store_map = {}
    reverse_sku_map = {} 
    reverse_store_map = {}
    main()


