from machine import Pin, SoftSPI
#from os import uname

# this is a mini version that read only.
# modified from https://github.com/Zenvi/ESP8266-RC522-MicroPython

class RC522:
    # PCD: Proximity Coupling Device (RC522 itself)
    PCD_IDLE            = 0x00
    PCD_AUTHENT         = 0x0E
    PCD_TRANSCEIVE      = 0x0C
    PCD_RESETPHASE      = 0x0F
    PCD_CALCCRC         = 0x03
    # PICC: Proximity card （S50 card)
    PICC_REQIDL         = 0x26
    PICC_REQALL         = 0x52
    PICC_ANTICOLL       = 0x93
    PICC_SELECTTAG      = 0x93
    PICC_AUTHENT1A      = 0x60
    PICC_AUTHENT1B      = 0x61
    PICC_READ           = 0x30
    PICC_WRITE          = 0xA0
    PICC_DECREMENT      = 0xC0
    PICC_INCREMENT      = 0xC1
    PICC_TRANSFER       = 0xB0
    OK       = 0
    NOTAGERR = 1
    ERR      = 2
    # RC522's registers addresses
    CommandReg          = 0x01
    CommIEnReg          = 0x02
    CommIrqReg          = 0x04
    DivIrqReg           = 0x05
    ErrorReg            = 0x06
    Status2Reg          = 0x08
    FIFODataReg         = 0x09
    FIFOLevelReg        = 0x0A
    ControlReg          = 0x0C
    BitFramingReg       = 0x0D
    ModeReg             = 0x11
    TxControlReg        = 0x14
    TxAutoReg           = 0x15
    CRCResultRegM       = 0x21
    CRCResultRegL       = 0x22
    TModeReg            = 0x2A
    TPrescalerReg       = 0x2B
    TReloadRegH         = 0x2C
    TReloadRegL         = 0x2D
    def __init__(self, sck, mosi, miso, rst, cs):
        self.sck = Pin(sck, Pin.OUT)
        self.mosi = Pin(mosi, Pin.OUT)
        self.miso = Pin(miso)
        self.rst = Pin(rst, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)
        self.rst.value(0)
        self.cs.value(1)
        #board = uname()[0]
        #if board == 'esp8266':
        self.spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=self.sck, mosi=self.mosi, miso=self.miso)
        self.spi.init()
        '''
        elif board == 'WiPy' or board == 'LoPy' or board == 'FiPy':
            self.spi = SoftSPI(0)
            self.spi.init(SoftSPI.MASTER, baudrate=1000000, pins=(self.sck, self.mosi, self.miso))
        else:
            raise RuntimeError("Unsupported platform")
        '''
        self.rst.value(1)
        self.init()
    def _wreg(self, reg, val):
        '''
        Write a register of RC522
        reg is the address of the register you wish to write
        val is the value you wish to write to reg
        '''
        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & ((reg << 1) & 0x7e)))
        self.spi.write(b'%c' % int(0xff & val))
        self.cs.value(1)
    def _rreg(self, reg):
        '''
        Read a register of RC522
        reg is the address of the register you wish to read
        '''
        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & (((reg << 1) & 0x7e) | 0x80)))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]
    def _sflags(self, reg, mask):
        '''
        Set some bits to 1 for a register.
        '''
        self._wreg(reg, self._rreg(reg) | mask)
    def _cflags(self, reg, mask):
        '''
        Set some bits to 0 for a register.
        '''
        self._wreg(reg, self._rreg(reg) & (~mask))
    def _tocard(self, cmd, send):
        '''
        Send information to CARD via RC522
        '''
        recv = []
        bits = irq_en = wait_irq = n = 0
        stat = self.ERR
        if cmd == self.PCD_AUTHENT:   # 0x0E  验证密钥
            irq_en = 0x12     # 0001 0010
            wait_irq = 0x10   # 0001 0000
        elif cmd == self.PCD_TRANSCEIVE:   # 0x0C  发送并接收数据
            irq_en = 0x77     # 0111 0111
            wait_irq = 0x30   # 0011 0000
        self._wreg(self.CommIEnReg, irq_en | 0x80)
        self._cflags(self.CommIrqReg, 0x80)
        self._wreg(self.CommandReg, self.PCD_IDLE)
        self._sflags(self.FIFOLevelReg, 0x80)
        for c in send:
            self._wreg(self.FIFODataReg, c)
        self._wreg(self.CommandReg, cmd)
        if cmd == self.PCD_TRANSCEIVE:
            self._sflags(self.BitFramingReg, 0x80)
        i = 2000
        while True:
            n = self._rreg(self.CommIrqReg)
            i -= 1
#             if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
            if not ((i != 0) and (not (n & 0x01)) and (not (n & wait_irq))):
                break
        self._cflags(self.BitFramingReg, 0x80)
        if i != 0:
            if (self._rreg(self.ErrorReg) & 0x1B) == 0x00:
                stat = self.OK
                if n & irq_en & 0x01:
                    stat = self.NOTAGERR
                elif cmd == self.PCD_TRANSCEIVE:
                    n = self._rreg(self.FIFOLevelReg)
                    lbits = self._rreg(self.ControlReg) & 0x07
                    if lbits != 0:
                        bits = (n - 1) * 8 + lbits
                    else:
                        bits = n * 8
                    if n == 0:
                        n = 1
                    elif n > 16:
                        n = 16
                    for _ in range(n):
                        recv.append(self._rreg(self.FIFODataReg))
            else:
                stat = self.ERR
        self._sflags(self.ControlReg, 0x80)
        self._wreg(self.CommandReg, self.PCD_IDLE)
        return stat, recv, bits
    def init(self):
        self.reset()
        self._wreg(self.TModeReg, 0x8D)
        self._wreg(self.TPrescalerReg, 0x3E)
        self._wreg(self.TReloadRegL, 30)
        self._wreg(self.TReloadRegH, 0)
        self._wreg(self.TxAutoReg, 0x40)
        self._wreg(self.ModeReg, 0x3D)
        self.antenna_on()
    def reset(self):
        self._wreg(self.CommandReg, self.PCD_RESETPHASE)
    def antenna_on(self, on=True):
        if on and ~(self._rreg(self.TxControlReg) & 0x03):
            self._sflags(self.TxControlReg, 0x03)
        else:
            self._cflags(self.TxControlReg, 0x03)
    def request(self, mode):
        self._wreg(self.BitFramingReg, 0x07)
        (stat, recv, bits) = self._tocard(self.PCD_TRANSCEIVE, [mode])
        if (stat != self.OK) | (bits != 0x10):
            stat = self.ERR
        return stat, bits
    def anticoll(self):
        ser_chk = 0
        ser = [self.PICC_ANTICOLL, 0x20]
        self._wreg(self.BitFramingReg, 0x00)
        (stat, recv, bits) = self._tocard(self.PCD_TRANSCEIVE, ser)
        if stat == self.OK:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk = ser_chk ^ recv[i]
                if ser_chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR
        return stat, recv
