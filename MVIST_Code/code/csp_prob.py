from datetime import datetime
import csv
import numpy as np
from numpy import zeros
from algorithm import Strategy
import time
from tqdm import tqdm


class CSP_Prob(Strategy):
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
                        #Consider stores that are part of the cluster
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
        #TODO: Add a way to get the deficit sku by probability. SORT  
        deficit_sku_list = []
        #Descending order by probability
        store_sku_by_probability = np.argsort(self.probability[:,shop_index])[::-1]
        for index in store_sku_by_probability:
            if requirement_all_sku[index] > 0:
                deficit_sku_list.append(index)
        return deficit_sku_list


    def get_excess_sku_list(self, shop_index, requirement_all_sku):
        excess_sku = np.where(requirement_all_sku > 0)
        return excess_sku    


    def get_transferable_units(self, deficit_sku, excess_shop_index, deficit_shop_index):
        """
        Returns the total number of product units that can be transferred between 2 shops for 
        deficit sku
        """
        transfer_units = 0
        if self.requirement[deficit_sku, excess_shop_index] < abs(self.requirement[deficit_sku, deficit_shop_index]):
            #deficit is more than available units. transfer available units
            transfer_units = self.requirement[deficit_sku, excess_shop_index]
        else:
            #Available units are more than required. transfer all that are required
            transfer_units = abs(self.requirement[deficit_sku, deficit_shop_index])
        return transfer_units
            

    def get_ist_estimate(self, deficit_shop_index, excess_shop_index, candidate_sku_index, qty_limit):
        """
        For a given candidate Sku and from, to store. try to find if the IST can be performed
        while keeping a track of all the constraints
        """
        
        total_ist_qty = 0
        transactions = []

        #Check if the IST for candidate SKU is valid
        total_ist_qty =  self.get_transferable_units(candidate_sku_index, excess_shop_index, deficit_shop_index)
        if total_ist_qty > qty_limit:
            transactions.append((candidate_sku_index, qty_limit)) #Tranfer qty_limit number of units
            return qty_limit, transactions, True
        
        #No units available for the transfer
        if total_ist_qty <=0:
            return 0, [], False
        
        # Items transfered are less than qty_limit. Still scope to transfer items.
        transactions.append((candidate_sku_index, total_ist_qty))
        
        #Update the quantity limit to represent total units required.
        qty_limit -= total_ist_qty 

        #Check for previous transfers in these 2 shops
        if qty_limit < 45:
            return qty_limit, transactions, True

        #Atleast 5 units should be transfered between 2 shops for Successful IST
        reqd_units_for_sucess = 5 - (50 - qty_limit)
              
        #Fetch deficit SKUs arranged by probability
        source_deficit_sku = self.get_deficit_sku_list(deficit_shop_index, self.requirement[:, deficit_shop_index])
        dest_excess_sku = self.get_excess_sku_list(excess_shop_index, self.requirement[:, excess_shop_index])[0]
        
        secondary_ist_qty = 0
        for deficit_sku in source_deficit_sku:
            if deficit_sku == candidate_sku_index:
                continue
            if deficit_sku in dest_excess_sku and secondary_ist_qty < reqd_units_for_sucess:
                transfer_units = self.get_transferable_units(deficit_sku, excess_shop_index, deficit_shop_index)          
                
                #If more units than required are available, transfer all the required units
                if (secondary_ist_qty + transfer_units > reqd_units_for_sucess):
                    transfer_units = reqd_units_for_sucess - secondary_ist_qty
                    transactions.append((deficit_sku, transfer_units)) #Storing all the possible transfers
                    secondary_ist_qty += transfer_units
                    return total_ist_qty + secondary_ist_qty, transactions, True
        
        #IST is not possible
        return 0, [], False
                


    def get_max_prob_shop(self, candidate_sku_index, source_shop_index):
        """
        Verifies if the source shop can undergo IST
        if yes, what is the quantity that can be transferd and the transactions that need to be executed
        to make it work.
        """
        index = 1
        qty_limit = self.valid_quantity_limit(50, source_shop_index)  # -ve qty_limit signifies that the shop has transfered more than the quota
        
        
        while(index != self.transfer.shape[0] and qty_limit > 0 and self.valid_shop_to_shop_transfer_limit(5, source_shop_index) == True):
            
            #Check for shop that has the max prob of candidate_sku 
            max_prob_shop_index =  self.get_nth_maximum(index, self.probability[candidate_sku_index,:])[0]
            
            #Max prob store does not have a deficit
            if self.requirement[candidate_sku_index,max_prob_shop_index] > 0 or max_prob_shop_index==source_shop_index:
                index += 1
                continue

            #Amongst all the SKUs now check if: all the transfers can lead to item_qyty >=5
            items_transferred, transcations, ist_successful = self.get_ist_estimate(max_prob_shop_index, source_shop_index, candidate_sku_index, qty_limit) 
            if  ist_successful:
                return max_prob_shop_index, transcations, items_transferred     
            
            #Look for next max_prob_shop
            index +=1
        
        #No valid shop found 
        return -1, [], 0


    def perform_ist(self, dest_store, source_store, transactions, total_transfers):
        """
        Update all the data structures that indicate a IST
        inventory[sku,store]
        requirement[sku,store] 
        transfer[store, store]
        """
        for tx in transactions: 
            #Update Inventory
            self.inventory[tx[0], dest_store]  += tx[1]
            self.inventory[tx[0], source_store]  -= tx[1]

            #Update requirement
            self.requirement[tx[0], dest_store]  -= tx[1]  #Subtracting as the req will be -ve
            self.requirement[tx[0], source_store]  -= tx[1]

            #Store the tx source, dest wise in report
            date = datetime.date(datetime.now()).strftime("%d/%m/%Y")
            self.report_skuwise.append([date, self.reverse_sku_map[tx[0]], self.reverse_store_map[source_store], self.reverse_store_map[dest_store], tx[1]])

        #Update transfer
        self.transfer[source_store, dest_store] += total_transfers
        self.report_summary.append([date, self.reverse_store_map[source_store], self.reverse_store_map[dest_store], str(total_transfers)])
        #mini_report[..., (date, source_store, dest_store, sku, qty),...]
        return True


    def execute(self):
        total_sku_count = self.inventory.shape[0]
        nth_sku = 1
        status_bar = tqdm(total=total_sku_count)
        while(nth_sku != total_sku_count):
            #Get location of nth sku and corrosponding store
            max_sku, max_store = self.get_nth_maximum(nth_sku, self.requirement) 
            
            #Get shop that can satisfy all the algo conditions   
            shop_index, transactions, total_transfers = self.get_max_prob_shop(max_sku, max_store)
            if (shop_index == -1):
                #No shop found
                nth_sku +=1
                status_bar.update(1)
                continue
            else:
                self.perform_ist(shop_index, max_store, transactions, total_transfers)

        """
        print("Transfers from each store:")
        for index in range(0,self.transfer.shape[0]):
            s = np.sum(self.transfer[index,:])
            temp = self.transfer[index,:]
            m = np.amin(temp[temp > 0])
            non_zero = np.nonzero(self.transfer[index,:])[0]
            print("Total Transfers from " + str(self.reverse_store_map[index] + " = " + str(s)) + " | min : " + str(m) + " | total orders:" + str(non_zero.shape[0]))
        """


    