import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import sys

class Potato(object):
    def __init__(self):
        self._a = 1
        self._b = 2
        self._c = 1
        self._d = 0
        self._pool = ThreadPoolExecutor(max_workers=2)
        self._loop = asyncio.get_event_loop()
        self.coros = []

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

    async def tasks(self):
        self.coros.append(self._loop.create_task(self.ship_to_process()))
        self.coros.append(self._loop.create_task(self.long_time()))
        self.coros.append(self._loop.create_task(self.hi()))
        self.coros.append(self._loop.create_task(self.sneaky()))
        for coro in self.coros:
            await asyncio.wait([coro])
        return self.coros
    
    def run(self):
        try:
            self._loop.run_until_complete(self.tasks())
        except KeyboardInterrupt:
            self._pool.shutdown(wait=False)
        else:
            self._pool.shutdown(wait=True)
        finally:
            for task in asyncio.Task.all_tasks():
                task.cancel()
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.stop()
            self._loop.close()
            sys.exit(0)
            
if __name__ == '__main__':
    alamak = Potato()
    alamak.run()