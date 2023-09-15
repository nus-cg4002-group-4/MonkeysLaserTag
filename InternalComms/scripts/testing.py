from keyboard import is_pressed
import time

if __name__ == "__main__":
    count = 0
    debounce_time = 0.5  # Adjust this debounce time as needed
    last_press_time = 0

    while True:
        if is_pressed('a'):
            current_time = time.time()
            print(current_time)
            if current_time - last_press_time >= debounce_time:
                count += 1
                print(f'{count}: You Pressed A Key!')
                last_press_time = current_time