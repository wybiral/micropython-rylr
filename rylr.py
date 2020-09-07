import uasyncio as asyncio

class Packet:

    def __init__(self, data, addr=0, rssi=0, snr=0):
        self.data = data
        self.addr = addr
        self.rssi = rssi
        self.snr = snr

    def __str__(self):
        return self.data


class RYLR:

    def __init__(self, uart, **kw):
        self.uart = uart
        self.w = asyncio.StreamWriter(uart, {})
        self.r = asyncio.StreamReader(uart)
        self._packet = None
        self._resp = None
        self._waiting = []
        self._frequency = kw.get('frequency', 915.0)
        self._bandwidth = kw.get('bandwidth', 250000)
        self._spreading_factor = kw.get('spreading_factor', 10)
        self._coding_rate = kw.get('coding_rate', 8)
        self._preamble_length = kw.get('preamble_length', 4)

    async def init(self):
        await self.set_frequency(self._frequency)
        await self._set_parameters()

    async def send(self, msg, addr=0):
        await self._cmd('AT+SEND=%i,%i,%s' % (addr, len(msg), msg))

    async def recv_packet(self):
        while self._packet is None:
            await asyncio.sleep(0.1)
        data = self._packet
        self._packet = None
        return data

    async def recv(self):
        pkt = await self.recv_packet()
        return pkt.data

    async def _cmd(self, x):
        await self.w.awrite(x + '\r\n')
        e = asyncio.Event()
        self._waiting.append(e)
        await e.wait()
        return self._resp

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
                self._recv(x[5:])
                continue
            self._resp = x
            if self._waiting:
                e = self._waiting.pop(0)
                e.set()

    def _recv(self, x):
        addr, n, x = x.split(',', 2)
        n = int(n)
        data = x[:n]
        x = x[n+1:]
        rssi, snr = x.split(',')
        self._packet = Packet(data, int(addr), int(rssi), int(snr))

    async def get_baud_rate(self):
        x = await self._cmd('AT+IPR?')
        return int(x[5:])

    async def set_baud_rate(self, x):
        return await self._cmd('AT+IPR=' + x)

    async def get_frequency(self):
        x = await self._cmd('AT+BAND?')
        return int(x[6:]) / 1000000.0

    async def set_frequency(self, x):
        return await self._cmd('AT+BAND=' + str(round(x * 1000000)))

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

    async def get_address(self):
        x = await self._cmd('AT+ADDRESS?')
        return int(x[9:])

    async def set_address(self, addr):
        return await self._cmd('AT+ADDRESS=' + str(addr))

    async def get_bandwidth(self):
        return self._bandwidth

    async def set_bandwidth(self, bw):
        self._bandwidth = bw
        return await self._set_parameters()

    async def get_coding_rate(self):
        return self._coding_rate

    async def set_coding_rate(self, cr):
        self._coding_rate = cr
        return await self._set_parameters()

    async def get_preamble_length(self):
        return self._preamble_length

    async def set_preamble_length(self, pl):
        self._preamble_length = pl
        return await self._set_parameters()

    async def get_spreading_factor(self):
        return self._spreading_factor

    async def set_spreading_factor(self, sf):
        self._spreading_factor = sf
        return await self._set_parameters()

    async def get_network(self):
        x = await self._cmd('AT+NETWORKID?')
        return int(x[11:])

    async def set_network(self, n):
        return await self._cmd('AT+NETWORKID=' + str(n))

    async def get_aes_key(self):
        x = await self._cmd('AT+CPIN?')
        return x[6:]

    async def set_aes_key(self, key):
        return await self._cmd('AT+CPIN=' + key)
