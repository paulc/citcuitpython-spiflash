# citcuitpython-spiflash

## Simple SPI flash driver for W25QXX devices

This module provides a simple SPI flash driver for Winbond W25QXX devices.

The driver comprises two classes:

`SPIFlash`

* `Raw` SPI flash driver 

`SPIFlashFS`

* `blockdevice` driver
* It shoukld be possible to mount this as a system storage instance using `storage.VfsFat` (THIS DOESN'T CURRENTLY WORK)

