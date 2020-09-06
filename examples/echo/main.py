import uasyncio as asyncio
from machine import UART
from rylr import RYLR

async def main(rylr):
    await rylr.init()
    while True:
        # Receive data
        data = await rylr.recv()
        # Print to terminal
        print(data)
        # Echo data
        await rylr.send(data)

# Get second UART device (rx=16, tx=17 on ESP32 devkitc)
uart = UART(2, 115200)
rylr = RYLR(uart)

loop = asyncio.get_event_loop()

# Create RYLR background task
loop.create_task(rylr.loop())

# Create main task
loop.create_task(main(rylr))

# Start IO loop
loop.run_forever()
