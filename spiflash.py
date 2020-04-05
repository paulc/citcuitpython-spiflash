
import board
import storage
from busio import SPI
from digitalio import DigitalInOut

JEDEC_ID        = b'\x9f'
MNFR_ID         = b'\x90\x00\x00\x00'
UNIQUE_ID       = b'\x4b\x00\x00\x00\x00'
STATUS          = b'\x05'
WRITE_ENABLE    = b'\x06'
CHIP_ERASE      = b'\xc7'
WRITE_PAGE      = b'\x02'
READ            = b'\x03'
PAGE_SIZE       = 256
ERASE_4K        = b'\x20'
ERASE_32K       = b'\x52'
ERASE_64K       = b'\xd8'

class SPIFlash:

    def __init__(self,spi,cs,br=42000000):
	self.spi = spi
        self.br = br
	self.cs = cs
	self.cs.switch_to_output(value=True)

    def cmd(self,cmd,length):
        response = bytearray(length)
        # Start transaction
	self.cs.value = False
        while not self.spi.try_lock():
            pass
        self.spi.configure(baudrate=self.br)
        # Command
        self.spi.write(cmd)
        self.spi.readinto(response)
        # End transaction
        self.spi.unlock()
	self.cs.value = True
        return response

    def pack_cmd(self,cmd,addr,data=None):
        if data:
            c = bytearray(4 + len(data))
        else:
            c = bytearray(4)
        c[0] = cmd[0]
        c[1] = (addr >> 16) & 255
        c[2] = (addr >> 8) & 255
        c[3] = (addr) & 255
        if data:
            c[4:] = data
        return c

    def wait(self):
        while True:
            r = self.cmd(STATUS,1)
            if r[0] == 0:
                break

    def write_enable(self):
        self.cmd(WRITE_ENABLE,0)

    def chip_erase(self):
        self.write_enable()
        self.cmd(CHIP_ERASE,0)
        self.wait()

    def erase4k(self,addr):
        cmd = self.pack_cmd(ERASE_4K,addr)
        self.write_enable()
        self.cmd(cmd,0)
        self.wait()

    def write(self,addr,data):
        length = len(data)
        pos = 0
        while pos < length:
            size = min(length-pos,PAGE_SIZE)
            cmd = self.pack_cmd(WRITE_PAGE,addr,data[pos:pos+size])
            self.write_enable()
            self.cmd(cmd,0)
            addr += size
            pos += size
        self.wait()

    def read(self,addr,length=1):
        i = 0
        r = bytearray(length)
        while i < length:
            cmd = self.pack_cmd(READ,addr)
            r[i] = self.cmd(cmd,1)[0]
            i += 1
            addr += 1
        return r

    def read_into(self,addr,buf):
        i = 0
        length = len(buf)
        while i < length:
            cmd = self.pack_cmd(READ,addr)
            buf[i] = self.cmd(cmd,1)[0]
            i += 1
            addr += 1

    @property
    def jedec_id(self):
        return self.cmd(JEDEC_ID,3)

    @property
    def mnfr_id(self):
        return self.cmd(MNFR_ID,2)

    @property
    def unique_id(self):
        return self.cmd(UNIQUE_ID,8)

class SPIFlashFS:

    def __init__(self,flash,nblocks,blksize=4096):
        self.flash = flash
        self.nblocks = nblocks
        self.blksize = blksize

    def readblocks(self,n,buf):
        print("readblocks(%s, %x(%d))" % (n, id(buf), len(buf)))
        self.flash.read_into(n * self.blksize,buf)
        return 0

    def writeblocks(self,n,buf):
        print("writeblocks(%s, %x)" % (n, id(buf)))
        self.flash.erase4k(n * self.blksize)
        self.flash.write(n * self.blksize,buf)
        return 0

    def ioctl(self,op,arg):
        print("ioctl(%d, %r)" % (op, arg))
        if op == 4: # BP_IOCTL_SEC_COUNT
            return self.nblocks
        if op == 5: # BP_IOCTL_SEC_SIZE
            return 512
            # return self.blksize

spi = SPI(board.A5,board.A7,board.A6)
cs = DigitalInOut(board.A0)
flash = SPIFlash(spi,cs)

from ramfs import RAMFS

bdev_ram = RAMFS(50)
storage.VfsFat.mkfs(bdev_ram)
vfs_ram = storage.VfsFat(bdev_ram)
storage.mount(vfs_ram,"/flash")

bdev = SPIFlashFS(flash,2048)
storage.VfsFat.mkfs(bdev)
vfs = storage.VfsFat(bdev)
storage.mount(vfs,"/flash")
