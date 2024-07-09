from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from multiprocessing import Process, Queue
import random
import time
from typing import List

app = FastAPI()

# Global queue to be used by FastAPI and processes
queue = Queue()
output_queue = Queue()  # Output queue to collect results from Consumer

class Producer(Process):
    def __init__(self, queue, items=10):
        super().__init__()
        self.queue = queue
        self.items = items

    def run(self):
        for i in range(self.items):
            item = random.randint(0, 256)
            self.queue.put(item)
            print(f"Process Producer: item {item} appended to queue {self.name}")
            time.sleep(1)
            print(f"The size of queue is {self.queue.qsize()}")

class Consumer(Process):
    def __init__(self, queue, output_queue):
        super().__init__()
        self.queue = queue
        self.output_queue = output_queue

    def run(self):
        while True:
            if self.queue.empty():
                print("The queue is empty")
                break
            else:
                item = self.queue.get()
                self.output_queue.put(item)
                print(f"Process Consumer: item {item} popped from queue by {self.name}")
                time.sleep(2)

@app.get("/start_producer/{items}", response_class=JSONResponse)
def start_producer(items: int = Path(..., description="Number of items to produce")):
    process_producer = Producer(queue, items)
    process_producer.start()
    process_producer.join()
    return {"status": "Producer started"}

@app.get("/start_consumer", response_class=JSONResponse)
def start_consumer():
    process_consumer = Consumer(queue, output_queue)
    process_consumer.start()
    process_consumer.join()
    return {"status": "Consumer started"}

@app.get("/queue_status", response_class=JSONResponse)
def queue_status():
    if queue.empty():
        return {"status": "Queue is empty"}
    else:
        size = queue.qsize()
        return {"status": "Queue has items", "size": size}

@app.get("/queue_items", response_class=JSONResponse)
def queue_items():
    items = []
    while not queue.empty():
        item = queue.get()
        items.append(item)
    return {"items": items}

@app.get("/start_process/{items}", response_model=List[int])
def start_process(items: int = Path(..., description="Number of items to produce")):
    queue = Queue()
    output_queue = Queue()  # Output queue to collect results from Consumer

    producer = Producer(queue, items)
    consumer = Consumer(queue, output_queue)

    producer.start()
    consumer.start()

    producer.join()
    consumer.join()

    # Collect results from the output queue
    results = []
    while not output_queue.empty():
        results.append(output_queue.get())

    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
