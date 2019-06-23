
class ItemDetails:
    def __init__(self, store,sku,csi,bsq,pps):
        self.store = store
        self.sku = sku
        self.csi = csi
        self.bsq = bsq
        self.pps = pps

    def get_transferable_qty(self):
        #print( str(self.store) + " Quantity : " + str(self.csi - self.bsq))
        return self.csi - self.bsq