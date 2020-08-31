import uasyncio as asyncio

class RYLR:

    def __init__(self, uart, **kw):
        self.uart = uart
        self.w = asyncio.StreamWriter(uart, {})
        self.r = asyncio.StreamReader(uart)
        self.response = b''
        self.waiting = []
        self._on_recv = kw.get('on_recv', None)
        self._frequency = kw.get('frequency', 915.0)
        self._bandwidth = kw.get('bandwidth', 250000)
        self._spreading_factor = kw.get('spreading_factor', 10)
        self._coding_rate = kw.get('coding_rate', 5)
        self._preamble_length = kw.get('preamble_length', 4)

    async def init(self):
        await self.set_frequency(self._frequency)
        await self._set_parameters()
        await self.set_address(0)
        await self.set_network(0)
        await self.set_aes_key('0' * 32)

    async def send(self, msg, addr=0):
        await self.w.awrite('AT+SEND=%i,%i,%s\r\n' % (addr, len(msg), msg))

    def on_recv(self, fn):
        self._on_recv = fn

    async def _cmd(self, x):
        await self.w.awrite(x + '\r\n')
        e = asyncio.Event()
        self.waiting.append(e)
        await e.wait()
        return self.response

    async def loop(self):
        r = self.r
        while True:
            try:
                x = await r.readline()
            except TypeError:
                continue
            if x is None:
                continue
            x = x[:-2].decode()
            if x.startswith('+RCV='):
                if self._on_recv:
                    self._on_recv(x)
                continue
            self.response = x
            if self.waiting:
                e = self.waiting.pop(0)
                e.set()

    async def set_baud_rate(self, x):
        return await self._cmd('AT+IPR=' + x)

    async def get_baud_rate(self):
        x = await self._cmd('AT+IPR?')
        return int(x[5:])

    async def set_frequency(self, x):
        return await self._cmd('AT+BAND=' + str(round(x * 1000000)))

    async def get_frequency(self):
        x = await self._cmd('AT+BAND?')
        return int(x[6:]) / 1000000.0

    async def _set_parameters(self):
        sf = self._spreading_factor
        bws = (7800, 10400, 15600, 20800, 31250, 41700, 62500, 125000, 250000)
        bw = 9
        for i in range(len(bws)):
            if self._bandwidth <= bws[i]:
                bw = i
                break
        cr = self._coding_rate - 4
        pl = self._preamble_length
        return await self._cmd('AT+PARAMETER=%i,%i,%i,%i' % (sf, bw, cr, pl))

    async def set_address(self, addr):
        return await self._cmd('AT+ADDRESS=' + str(addr))

    async def get_address(self):
        x = await self._cmd('AT+ADDRESS?')
        return int(x[9:])

    async def set_network(self, n):
        return await self._cmd('AT+NETWORKID=' + str(n))

    async def get_network(self):
        x = await self._cmd('AT+NETWORKID?')
        return int(x[11:])

    async def set_aes_key(self, key):
        return await self._cmd('AT+CPIN=' + key)

    async def get_aes_key(self):
        x = await self._cmd('AT+CPIN?')
        return x[6:]
