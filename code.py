
import os
from spiflash import mountspi

mountspi()

print("Mounted SPI Flash: /spi")
print(os.listdir("/spi"))
