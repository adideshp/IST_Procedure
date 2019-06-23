from datetime import datetime
from algorithm import Strategy
from ist_order import ISTOrder
from item_details import ItemDetails

class DefaultAlgorithm(Strategy):
    def __init__(self, shop_sku_detail_list):
        self.input = shop_sku_detail_list
        self.excess_list = []
        self.deficit_list = []
        self.balanced_list = []

        #Input list of all stores with excess inventory. Will be consumed
        self.input_excess_list = []

    def preprocess(self, exclusion_list):
        """
        Populates execess_list, deficit_list and balanced_list based on the current inventory and 
        base invnetory. 
        """
        for item in self.input:
            if item.store in exclusion_list:
                continue
            if item.get_transferable_qty() < 0:
                self.deficit_list.append(item)
            elif item.get_transferable_qty() > 0:
                self.input_excess_list.append(item) 
            else:
                self.balanced_list.append(item)


    def perform_ist(self, max_orders, min_qty):
        """
        Based on the initialized parameters executes the Default InterStore Transfer Algorithm
        """
        #Initialization of the counters
        orders_processed = 0  
        items_transferred = 0
        ist_transfers_qty = {}
        ist_transfers_detail = {}
        
        for excess_item in self.input_excess_list:
            #print("Excess ITEM check" + str(excess_item.store))
            if excess_item.get_transferable_qty() < min_qty:
                continue
            
            #Sort deficit list on Projected Probability of sales
            stores_sku_with_deficit = sorted(self.deficit_list,key=lambda x: x.pps, reverse=True)
            #print("Length:" + str(len(stores_sku_with_deficit)))

            for deficit_item in stores_sku_with_deficit:
                transferable_qty = excess_item.get_transferable_qty()
                
                #print("ITEM FROM " + deficit_item.store + " removed")
                deficit = abs(deficit_item.get_transferable_qty())
                
                if (deficit < min_qty):
                    #Skip shop_sku pair if the deficit is less than minimum allowed transfer
                    continue

                #Create an entry in the transfers data structures
                if not(excess_item.store in ist_transfers_qty.keys()):
                    ist_transfers_qty[excess_item.store] = {}
                    ist_transfers_detail[excess_item.store] = {}
                
                    

                # Check Algorithm constraints
                if (transferable_qty > min_qty) and (orders_processed < max_orders) and (items_transferred < 50):
                    transfered = 0 #total items transfered 
                    #Remove the item form deficit list
                    self.deficit_list.remove(deficit_item)

                    if (transferable_qty >= deficit):
                        items_transferred += deficit
                        transfered += deficit 

                        #Update deficit_item and excess_item
                        deficit_item.csi += deficit
                        excess_item.csi -= deficit
                        
                        # Requirement is satisfied
                        self.balanced_list.append(deficit_item)

                    else:
                        deficit -= transferable_qty
                        items_transferred += transferable_qty
                        transfered += transferable_qty
                        
                        #Update deficit_item and excess_item
                        deficit_item.csi += transferable_qty
                        excess_item.csi -= transferable_qty
                        
                        #Deficit still present
                        self.deficit_list.append(deficit_item)
                    
                    #Add IST details to the Report instance
                    date = datetime.date(datetime.now()).strftime("%d/%m/%Y")
                    ist_record = ISTOrder(date, deficit_item.sku, excess_item.store, deficit_item.store, transfered)
                    
                    if deficit_item.store in ist_transfers_qty[excess_item.store]:
                        ist_transfers_qty[excess_item.store][deficit_item.store] += transfered
                        ist_transfers_detail[excess_item.store][deficit_item.store].append((deficit_item.sku, transfered))
                    else:
                        ist_transfers_qty[excess_item.store][deficit_item.store] = transfered
                        ist_transfers_detail[excess_item.store][deficit_item.store] = [(deficit_item.sku, transfered)]
                    orders_processed += 1

            #Decision on adding excess_item in one of the lists
            if excess_item.get_transferable_qty() > 0:
                self.excess_list.append(excess_item)
            else:
                #The excess item inventory will  not go less than 0
                self.balanced_list.append(excess_item)
        
        return ist_transfers_qty, ist_transfers_detail

    def execute(self, max_orders, min_qty, exclusion_list):
        """
        Performs the Preprocessing step and then later run the perform_ist function 
        """
        self.preprocess(exclusion_list)
        ist_transfers_qty, ist_transfers_detail = self.perform_ist(max_orders, min_qty)
        return ist_transfers_qty, ist_transfers_detail
    