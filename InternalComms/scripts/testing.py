import multiprocessing
import time

# Function to run in a separate process
class Test:

    def __init__ (self):
        pass

    def process_function(self, flag, queue):
        while not flag.is_set():
            data = f"Data {time.time()}"
            queue.put(data)
            print(f"Sent: {data}")
            time.sleep(1)  # Simulate some work

if __name__ == "__main__":
    # Create a multiprocessing queue
    data_queue = multiprocessing.Queue()

    # Create a multiprocessing flag
    exit_flag = multiprocessing.Event()
    t = Test()
    # Create a separate process
    process = multiprocessing.Process(target=t.process_function, args=(exit_flag, data_queue))

    # Start the process
    process.start()

    try:
        while True:
            if not data_queue.empty(): data = data_queue.get(timeout=1)  # Wait for 1 second to get data
            print(f"Received: {data}")
    except KeyboardInterrupt:
        # Set the exit flag to terminate the separate process
        exit_flag.set()
        process.join()  # Wait for the process to finish
        print("Main process finished.")
