import asyncio
import random
import time
import subprocess

NTTTCP_PATH = r"ntttcp.exe" #change to path to ntttcp on pc

class SimulatedDevice:
    def __init__(self, device_id, server_queue):
        self.device_id = device_id
        self.server_queue = server_queue

    async def run(self):
        try:
            while True:
                data = {
                    "device_id": self.device_id,
                    "timestamp": time.time(),
                    "temperature": round(random.uniform(20, 30), 2),
                    "humidity": round(random.uniform(40, 60), 2),
                }
                await self.server_queue.put(data)
                print(f"Device {self.device_id} sent data: {data}")
                await asyncio.sleep(random.uniform(0.5, 2))
        except asyncio.CancelledError:
            print(f"Device {self.device_id} shutting down...")
            return


async def run_ntttcp_receiver(duration=10, port_base=5001, num_streams=2):
    cmd = [NTTTCP_PATH, "-r", "-m", f"{num_streams},0,127.0.0.1", "-p", str(port_base), "-t", str(duration)]
    print("Starting NTttcp receiver...")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc


async def run_ntttcp_sender(duration=10, port_base=5001, num_streams=2):
    cmd = [NTTTCP_PATH, "-s", "-m", f"{num_streams},0,127.0.0.1", "-p", str(port_base), "-t", str(duration)]
    print("Starting NTttcp sender...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\n=== Sender Default Output ===")
    print(result.stdout)
    return result.stdout


async def main(num_devices=3, duration=10):
    server_queue = asyncio.Queue()

    # Launch IoT devices
    device_tasks = [
        asyncio.create_task(SimulatedDevice(f"device-{i+1}", server_queue).run())
        for i in range(num_devices)
    ]

    # Start receiver in background with num_devices streams
    receiver_proc = await run_ntttcp_receiver(duration=duration, num_streams=num_devices)

    # 🔑 Wait a few seconds to ensure receiver is ready
    await asyncio.sleep(2)

    # Run sender with num_devices streams
    sender_output = await run_ntttcp_sender(duration=duration, num_streams=num_devices)

    # Collect receiver output after sender finishes
    receiver_output, receiver_error = receiver_proc.communicate()
    print("\n=== Receiver Default Output ===")
    print(receiver_output)

    # Stop devices
    for task in device_tasks:
        task.cancel()
    await asyncio.gather(*device_tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main(num_devices=5, duration=10))