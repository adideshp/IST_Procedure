from datetime import datetime
import csv
import numpy as np
from numpy import zeros
from algorithm import Strategy

import time
from tqdm import tqdm

class CSP(Strategy):
    def __init__(self, cluster_name, cluster_info_filename, inventory_filename, bsq_filename, prob_filename):
        
        valid_stores_list = []

        with open(cluster_info_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    if str(row[1]) == cluster_name:
                        valid_stores_list.append(row[0])

        #Generate indexes for each store and sku. Used for creating numpy arrays
        self.sku_map, self.reverse_sku_map, self.store_map, self.reverse_store_map = self.create_maps(inventory_filename, valid_stores_list)

        #Initializing the inputs
        self.inventory = zeros([len(self.sku_map), len(self.store_map)])
        self.requirement = zeros([len(self.sku_map), len(self.store_map)])
        self.shortage = zeros([len(self.sku_map), len(self.store_map)])
        self.probability = zeros([len(self.sku_map), len(self.store_map)])
        self.transfer = zeros([len(self.store_map), len(self.store_map)])

        #Output Datastructure
        self.report_skuwise = []
        self.report_summary = []

        with open(inventory_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    self.inventory[self.sku_map[row[0]]][self.store_map[row[1]]] =  int(row[2])

        with open(bsq_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    self.requirement[self.sku_map[row[0]]][self.store_map[row[1]]] =  self.inventory[self.sku_map[row[0]]][self.store_map[row[1]]] - int(row[2])

        with open(prob_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    self.probability[self.sku_map[row[0]]][self.store_map[row[1]]] =  float(row[2])
                    self.shortage[self.sku_map[row[0]]][self.store_map[row[1]]] =  float(row[2]) * self.requirement[self.sku_map[row[0]]][self.store_map[row[1]]]


    def create_maps(self, inventory_filename, valid_stores_list):
        sku_map = {}
        reverse_sku_map = {}
        reverse_store_map = {}
        sku_index = 0
        store_map = {}
        store_index = 0

        with open(inventory_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    if row[1] in valid_stores_list:
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

    def valid_quantity_limit(self, limit, shop_index):
        """
        transfering store transfering shop do not execeed transfer greater than limit(50) units
        """
        total_qty = np.sum(self.transfer[shop_index,:]) 
        return limit - total_qty



    def valid_shop_to_shop_transfer_limit(self, limit, shop_index):
        """
        max shop to shop transfer is less than limit (5)
        """
        non_zero = np.nonzero(self.transfer[shop_index,:])[0].shape[0]
        if non_zero > limit:
            return False
        else:
            return True


    def get_nth_minimum(self, n, array_2d):
        result = np.vstack(np.unravel_index(np.argpartition(array_2d.flatten(), n)[n], array_2d.shape)).T
        return result[0]


    def get_nth_maximum(self, n, array_2d):
        result = np.vstack(np.unravel_index(np.argpartition(array_2d.flatten(), np.negative(n))[np.negative(n)], array_2d.shape)).T
        return result[0]


    def get_deficit_sku_list(self, shop_index, requirement_all_sku):
        deficit_sku = np.where(requirement_all_sku < 0)
        return deficit_sku


    def get_excess_sku_list(self, shop_index, requirement_all_sku):
        excess_sku = np.where(requirement_all_sku > 0)
        return excess_sku    


    def get_transferable_units(self, deficit_sku, excess_shop_index, deficit_shop_index):
        transfer_units = 0
        if self.requirement[deficit_sku, excess_shop_index] < abs(self.requirement[deficit_sku, deficit_shop_index]):
            #deficit is more than available units. transfer available units
            transfer_units = self.requirement[deficit_sku, excess_shop_index]
        else:
            #Available units are more than required. transfer all that are required
            transfer_units = abs(self.requirement[deficit_sku, deficit_shop_index])
        return transfer_units
            

    def get_ist_estimate(self, deficit_shop_index, excess_shop_index, candidate_sku_index, qty_limit):
        
        total_ist_qty = 0
        transactions = []
        #Check if the IST for candidate SKU is valid
        total_ist_qty =  self.get_transferable_units(candidate_sku_index, excess_shop_index, deficit_shop_index)
        if total_ist_qty > qty_limit:
            transactions.append((candidate_sku_index, qty_limit))
            return qty_limit, transactions
        transactions.append((candidate_sku_index, total_ist_qty))
        
        source_deficit_sku = self.get_deficit_sku_list(deficit_shop_index, self.requirement[:, deficit_shop_index])[0]
        dest_excess_sku = self.get_excess_sku_list(excess_shop_index, self.requirement[:, excess_shop_index])[0]
        
        
        for deficit_sku in source_deficit_sku:
            if deficit_sku == candidate_sku_index:
                continue
            if deficit_sku in dest_excess_sku and total_ist_qty < qty_limit:
                transfer_units = self.get_transferable_units(deficit_sku, excess_shop_index, deficit_shop_index)          
                if (total_ist_qty + transfer_units > qty_limit):
                    transfer_units = qty_limit - total_ist_qty
                
                total_ist_qty += transfer_units
                #Storing all the possible transfers
                transactions.append((deficit_sku, transfer_units))

        return total_ist_qty, transactions


    def get_max_supply_shop(self, candidate_sku_index, source_shop_index):
        index = 1
        
        while(index != self.transfer.shape[0]):
            #Check for shop that has the max qty of candidate_sku 
            max_supply_shop_index =  self.get_nth_maximum(index, self.requirement[candidate_sku_index,:])[0]
            
            #Max is -ve
            if self.requirement[candidate_sku_index,max_supply_shop_index] <= 0:
                return -1, [], 0
            if max_supply_shop_index == source_shop_index:
                index +=1
                continue
            qty_limit = self.valid_quantity_limit(50, max_supply_shop_index)
            if qty_limit > 0:
                if self.valid_shop_to_shop_transfer_limit(5, max_supply_shop_index) == True:
                    #Amongst all the SKUs now check if: all the transfers can lead to item_qyty >5
                    prob_transfer_units, transcations = self.get_ist_estimate(source_shop_index, max_supply_shop_index, candidate_sku_index, qty_limit)
                    if  prob_transfer_units >= 5 and prob_transfer_units <= 50:
                        return max_supply_shop_index, transcations, prob_transfer_units     
            #Look for next max_supply_shop
            index +=1
        #No valid shop found 
        return -1, [], 0


    def perform_ist(self, dest_store, source_store, transactions, total_transfers):
        """
        Update all the data structures that indicate a IST
        inventory[sku,store]
        requirement[sku,store] 
        shortage[sku,store]
        transfer[store, store]
        """
        total = 0
        for tx in transactions: 
            #Update Inventory
            self.inventory[tx[0], dest_store]  += tx[1]
            self.inventory[tx[0], source_store]  -= tx[1]

            #Update requirement
            self.requirement[tx[0], dest_store]  -= tx[1]  #Subtracting as the req will be -ve
            self.requirement[tx[0], source_store]  -= tx[1]

            #Update shortage
            self.shortage[tx[0], dest_store] = self.requirement[tx[0], dest_store] * self.probability[tx[0], dest_store]
            self.shortage[tx[0], source_store] = self.requirement[tx[0], source_store] * self.probability[tx[0], source_store]

            #Store the tx source, dest wise in report
            date = datetime.date(datetime.now()).strftime("%d/%m/%Y")
            self.report_skuwise.append([date, self.reverse_sku_map[tx[0]], self.reverse_store_map[source_store], self.reverse_store_map[dest_store], tx[1]])
            total += tx[1]

        #Update transfer
        self.transfer[source_store, dest_store] += total
        self.report_summary.append([date, self.reverse_store_map[source_store], self.reverse_store_map[dest_store], str(total)])
        
        #mini_report[..., (date, source_store, dest_store, sku, qty),...]
        return True


    def execute(self):
        total_sku_count = self.inventory.shape[0]
        nth_sku = 1
        status_bar = tqdm(total=total_sku_count)
        while(nth_sku != total_sku_count):
            
            #Get location of nth sku and corrosponding store
            min_sku, min_store = self.get_nth_minimum(nth_sku, self.shortage) 
            #Get shop that can satisfy all the algo conditions   
            shop_index, transactions, total_transfers = self.get_max_supply_shop(min_sku, min_store)
            if (shop_index == -1):
                #No shop found
                nth_sku +=1
                status_bar.update(1)
                continue
            else:
                self.perform_ist(min_store, shop_index, transactions, total_transfers)

        """
        print("Transfers from each store:")
        for index in range(0,self.transfer.shape[0]):
            s = np.sum(self.transfer[index,:])
            temp = self.transfer[index,:]
            m = np.amin(temp[temp > 0])
            non_zero = np.nonzero(self.transfer[index,:])[0]
            print("Total Transfers from " + str(self.reverse_store_map[index] + " = " + str(s)) + " | min : " + str(m) + " | total orders:" + str(non_zero.shape[0]))
        """


    