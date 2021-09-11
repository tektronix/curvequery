import sys
from time import sleep
from visadore import get
from tqdm import tqdm

osc = get(sys.argv[1])
print(osc.idn)
print(osc.features)
print(osc.curve().sources)

for _ in tqdm(range(100)):
    osc.curve()
    for i in osc.acquire(count=5, timeout=30):
        pass
    sleep(5)
    settings = osc.setup()
    osc.default_setup()
    sleep(5)
    osc.setup(settings)
