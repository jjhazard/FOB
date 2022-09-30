import sys
import time
import digitalio
import board

code = '1010101010101010000000111'
short_delay = 0.0003
long_delay = 0.0009
extended_delay = 0.009

NUM_ATTEMPS = 100
TRANSMIT_PIN = 27

def main():
    print(code)
    pin = digitalio.DigitalInOut(board.D14)
    pin.switch_to_output()
    for t in range(NUM_ATTEMPS):
        for i in str(code):
            if i == '1':
                pin.value = 1
                time.sleep(short_delay)
                pin.value = 0
                time.sleep(long_delay)
            elif i == '0':
                pin.value = 1
                time.sleep(long_delay)
                pin.value = 0
                time.sleep(short_delay)
        pin.value = 0
        time.sleep(extended_delay)

if __name__ == '__main__':
    main()
