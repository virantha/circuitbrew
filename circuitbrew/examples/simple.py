from module import *
from ports import *
from globals import SupplyPort
from fets import *


    
class MyFet(Module):
    bigvar= InputPort()
    bigvdd= InputPort()

    def build(self):
        self.finalize()

class Main(Module):
    a=InputPort()
    b=OutputPort()
    p=SupplyPort()
    def build(self):
        self.fet1 = MyFet()
        self.fet2 = MyFet()
        fub = self.fet1.bigvar
        self.fet2.bigvar = fub

        vdd = self.p.vdd
        self.fet1.bigvdd = vdd
        self.fet2.bigvdd = vdd
        print(locals())
        self.finalize()