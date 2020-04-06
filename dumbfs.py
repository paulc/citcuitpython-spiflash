
import struct

HEADER      = "8s24sIII20x"     # Magic, Label, Blocksize, NBlocks, FAT Blocks
HEADER_LEN  = 64
FAT_ENTRY   = "64sI30H"         # Name, Length, Direct Blocks (x30)

MAGIC = "DUMBFS01"

EMPTY = 0
SYS_BLOCK = 1
DATA_BLOCK = 2

class DumbFS:

    def __init__(self,blockdev,debug=False):
        self.blockdev = blockdev
        self.debug = debug
        (magic,self._label,self.blocksize,self.nblocks,self.fat_blocks) = self.header
        if magic != "DUMBFS01":
            self.mkfs()
            (magic,self._label,self.blocksize,self.nblocks,self.fat_blocks) = self.header

    def mkfs(self,label=b"",nblocks=None,fat_blocks=7):
        if self.debug:
            print("MKFS")
        # Get blocksize & number of blocks
        bs = self.blockdev.ioctl(5,0)
        nblocks = nblocks or self.blockdev.ioctl(4,0)
        if HEADER_LEN + nblocks > bs:
            raise ValueError("Not enough space for freelist ({}/{}}".format(bs-HEADER_LEN,nblocks))
        # Create block
        buf = bytearray(bs)
        print(len(buf))
        print(buf)
        # Zero FAT blocks
        for i in range(1,fat_blocks+1):
            self.blockdev.writeblocks(i,buf)
        # Write header
        struct.pack_into(HEADER,buf,0,b"DUMBFS",label,bs,nblocks,fat_blocks)
        # Mark Header + FAT blocks as used
        for i in range(fat_blocks+1):
            buf[HEADER_LEN+i] = SYS_BLOCK
        self.blockdev.writeblocks(0,buf)

    def write_partial(self,n,offset,data):
        buf = bytearray(self.bs)
        self.blockdev.readblocks(n,buf)
        buf[offset:offset+len(data)] = data
        self.blockdev.writeblocks(n,buf)

    @property
    def header(self):
        # Get first 64 bytes of block 0
        hbuf = bytearray(64)
        self.blockdev.readblocks(0,hbuf)
        return struct.unpack_from("8s24sIII20x",hbuf)

    @property
    def label(self):
        print("Label")
        return self._label

    @property
    def freelist(self):
        buf = bytearray(HEADER_LEN + self.nblocks)
        self.blockdev.readblocks(0,buf)
        return buf[HEADER_LEN:]

    @label.setter
    def label(self,value):
        print("Set-label: %s" % value)
        self._label = value

    def statvfs(self,path):
        # f_bsize, f_frsize, f_blocks, f_bfree, f_bavail, f_files, f_ffree, f_favail, f_flag, f_namemax
        return (self.bs,self.bs,self.nblocks,self.free,self.free,0,0,0,63)

    def mount(self,aaa,bbb):
        print("Mount: %s %s" % (aaa,bbb))

    def umount(self):
        print("Umount:")

    def chdir(self,path):
        print("Chdir: %s" % path)

    def ilistdir(self,path):
        print("Ilistdir: %s" % path)
        return iter([])

    def mkdir(self,path):
        print("Mkdir: %s" % path)

    def rmdir(self,path):
        print("Rmdir: %s" % path)

    def remove(self,path):
        print("Remove: %s" % path)

    def getcwd(self):
        print("Getcwd:")
        return "/"

    def rename(self,old,new):
        print("Rename: %s -> %s" % (old,new))

    def open(self,path,mode):
        print("Open: %s %s" % (path,mode))

    def stat(self,path):
        print("Stat: %s" % path)


import os
from spiflash import *

dfs = DumbFS(bdev,True)

