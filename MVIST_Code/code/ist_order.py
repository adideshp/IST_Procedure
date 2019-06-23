class ISTOrder:
    def __init__(self, date, sku, from_store, to_store, quantity):
        self.date = date 
        self.sku = sku
        self.from_store = from_store
        self.to_store = to_store 
        self.quantity = quantity

    def __str__(self):
        print(self.date + "|" + self.sku + "|" + self.from_store + "|" + self.to_store + "|" + str(self.quantity))
