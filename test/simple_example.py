import sys
from time import sleep
from visadore import get

osc = get(sys.argv[1])
print(osc.idn)
print(osc.features)
print(osc.curve().sources)

for i in osc.acquire(count=5, timeout=30):
    pass
sleep(5)
settings = osc.setup()
osc.default_setup()
sleep(5)
osc.setup(settings)

print()
