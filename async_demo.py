import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import sys
import uvloop
import socket

HOST = 'localhost'
PORT = 5000

class Potato(object):
    def __init__(self):
        self._a = 1
        self._b = 2
        self._c = 1
        self._d = 0
        self._pool = ThreadPoolExecutor(max_workers=2)
        uvloop.install()
        self._loop = asyncio.get_event_loop()
        self.coros = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((HOST, PORT))
        self.sock.listen(10)

    def bogus(self, c):
        '''slow cpu bound task'''
        sleep(1.5)
        self._d += 1
        return self._a + self._b + c
    
    async def long_time(self):
        """simulates a super laggy IO"""
        while True:
            await asyncio.sleep(1)
            print('long_time ended!')

    async def sneaky(self):
        """changes the value of self._a after running for a while"""
        while True:
            await asyncio.sleep(2.001)
            self._a +=1

    async def hi(self):
        while True:
            print('hi, d = {}'.format(self._d))
            await asyncio.sleep(0.2)
    
    async def ship_to_process(self):
        while True:
            thread_args = [self._c]
            result = await self._loop.run_in_executor(self._pool,self.bogus,*thread_args)
            # result = self.bogus(*thread_args)
            expected = self._a + self._b + self._c
            print('Result = {} , Expected = {}'.format(result, expected))

    async def echo_handler(self, conn, addr):
        while True:
            msg = await self._loop.sock_recv(conn, 1024)
            if not msg or msg is b'\xff\xf4\xff\xfd\x06':
                break
            # print(msg)
            else:
                try:
                    msg_str = msg.decode().rstrip()[::-1]
                except UnicodeDecodeError:
                    break
                print('Received: {} | From: {}'.format(msg_str, addr))
                msg = (msg_str + '\n').encode()
                await self._loop.sock_sendall(conn, msg)
        print('Connection closed: {}'.format(addr))
        conn.close()

    async def echo_server(self):
        while True:
            conn, addr = await self._loop.sock_accept(self.sock)
            print('Connection opened: {}'.format(addr))
            self._loop.create_task(self.echo_handler(conn, addr))

    async def tasks(self):
        self.coros.append(self._loop.create_task(self.ship_to_process()))
        self.coros.append(self._loop.create_task(self.long_time()))
        self.coros.append(self._loop.create_task(self.hi()))
        self.coros.append(self._loop.create_task(self.sneaky()))
        self.coros.append(self._loop.create_task(self.echo_server()))
        await asyncio.wait(self.coros)
        return self.coros
    
    def run(self):
        try:
            coros = self._loop.run_until_complete(self.tasks())
            print(coros)
        except KeyboardInterrupt:
            pass
            # self._pool.shutdown(wait=False)
        else:
            pass
        finally:
            self._pool.shutdown(wait=True)
            for task in asyncio.Task.all_tasks(self._loop):
                task.cancel()
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.stop()
            self._loop.close()
            sys.exit(0)
            
if __name__ == '__main__':
    alamak = Potato()
    alamak.run()