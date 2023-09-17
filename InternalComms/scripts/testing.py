import pandas as pd
import threading
import multiprocessing
from tabulate import tabulate
import time

def print_table(df, process_name):
    while True:
        # Print the table
        print(f"{process_name} Table:")
        print(tabulate(df, headers='keys', tablefmt='psql'))
        print("\n" * 5)  # Add blank lines for separation
        time.sleep(0.5)  # Adjust the delay based on your needs

def update_dataframe(df):
    while True:
        # Update the dataframe (replace this with your actual update logic)
        df.iloc[0, 0] += 1
        time.sleep(0.5)  # Adjust the delay based on your needs

if __name__ == "__main__":
    # Create two sample dataframes
    df1 = pd.DataFrame({'A': [1]})
    df2 = pd.DataFrame({'X': ['a']})

    # Define two processes for printing tables
    process1 = multiprocessing.Process(target=print_table, args=(df1, "Process 1"))
    process2 = multiprocessing.Process(target=print_table, args=(df2, "Process 2"))

    # Start the processes concurrently
    process1.start()
    process2.start()

    # Define threads for updating dataframes
    thread1 = threading.Thread(target=update_dataframe, args=(df1,))
    thread2 = threading.Thread(target=update_dataframe, args=(df2,))

    # Start the threads
    thread1.start()
    thread2.start()

    # Wait for the processes and threads to finish (you can use a termination condition)
    process1.join()
    process2.join()