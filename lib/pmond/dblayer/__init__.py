from pmond.dblayer import unisrt
#from pmond.dblayer import mundus

def load(ty):
    return {
        "unisrt": unisrt,
        "mundus": mundus
    }[ty].Client()
