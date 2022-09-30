from datetime import datetime
import matplotlib.pyplot as pyplot
import RPi.GPIO as GPIO
import digitalio
import board

RECEIVED_SIGNAL = [[], []] #[[time of reading], [signal reading]]
MAX_DURATION = 2

def main():
    pin = digitalio.DigitalInOut(board.D16)
    pin.switch_to_input(digitalio.Pull.DOWN)
    cumulative_time = 0
    beginning_time = datetime.now()
    print('**Started recording**')
    while cumulative_time < MAX_DURATION:
        time_delta = datetime.now() - beginning_time
        RECEIVED_SIGNAL[0].append(time_delta)
        RECEIVED_SIGNAL[1].append(pin.value)
        cumulative_time = time_delta.seconds
    print('**Ended recording**')
    print(len(RECEIVED_SIGNAL[0]), 'samples recorded')
    print('**Processing results**')
    for i in range (len(RECEIVED_SIGNAL[0])):
        RECEIVED_SIGNAL[0][i] = RECEIVED_SIGNAL[0][i].seconds + RECEIVED_SIGNAL[0][i].microseconds/1000000.0
    print('**Plotting results**')
    pyplot.plot(RECEIVED_SIGNAL[0], RECEIVED_SIGNAL[1])
    pyplot.axis([0, MAX_DURATION, -1, 2])
    pyplot.show()

if __name__ == '__main__':
	main()
