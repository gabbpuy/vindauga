# -*- coding: utf-8 -*-
from .prefix import Prefix

# A flag to remove some of the prefixes we don't like to use
RealWorld = True

NoPrefix = Prefix('', '', 0)             # : No Prefix
yotta = Prefix('Y', 'yotta', 24)       # : SI yotta
zetta = Prefix('Z', 'zetta', 21)       # : SI zetta
exa = Prefix('E', 'exa', 18)           # : SI exa
peta = Prefix('P', 'peta', 15)         # : SI peta
tera = Prefix('T', 'tera', 12)         # : SI tera
giga = Prefix('G', 'giga', 9)          # : SI giga
mega = Prefix('M', 'mega', 6)          # : SI mega
kilo = Prefix('k', 'kilo', 3)          # : SI kilo

if not RealWorld:
    # These prove to be difficult in "the real world"
    # hecto is commonly used with Pascals though
    # ditto deca for steradians
    # ditto deci for litres
    # ditto centi for metres
    hecto = Prefix('h', 'hecto', 2)    # : SI hecto (needs RealWorld = False)
    deca = Prefix('da', 'deca', 1)     # : SI deca (needs RealWorld = False)
    deci = Prefix('d', 'deci', -1)     # : SI deci (needs RealWorld = False)
    centi = Prefix('c', 'centi', -2)   # : SI centi (needs RealWorld = False)

milli = Prefix('m', 'milli', -3)       # : SI milli
micro = Prefix('', 'micro', -6)       # : SI micro
# We want this to be the one, so we do it 2nd so it ends up in the index
micro = Prefix('µ', 'micro', -6)  # : SI micro (with mu symbol)
nano = Prefix('n', 'nano', -9)         # : SI nano
pico = Prefix('p', 'pico', -12)        # : SI pico
femto = Prefix('f', 'femto', -15)      # : SI femto
atto = Prefix('a', 'atto', -18)        # : SI atto
zepto = Prefix('z', 'zepto', -21)      # : SI zepto
yocto = Prefix('y', 'yocto', -24)      #: SI yocto
