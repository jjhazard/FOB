from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import matplotlib.pyplot as pyplot
import math
import time
import statistics as stats

RECEIVED_SIGNAL = [[], []] #[[time of reading], [signal reading]]
MAX_DURATION = 5
RECEIVE_PIN = 24

def main():
    try:
        collectCalculateTransmit()
    except(KeyboardInterrupt):
        pass

def collectCalculateTransmit():
    batch_names = ["Extended", "Long", "Short",
                   "Extended/Long", "Long/Short", "Extended/Short"]
    stop = False
    while not stop:
        original_sets = collectData()
        batch_lists = getBatchListsFromDataSets(original_sets)
        print("Original Signal: ", original_sets[0][3])
        original_means = findMeans(batch_names, batch_lists)
        stop = acceptData()


"""
Testing variable delays
    stop = False
    cycles = 0
    variable = [original_means[0],
                original_means[1],
                original_means[2]]
    variance = [original_means[0]/50,
                original_means[1]/50,
                original_means[2]/50]
    while not stop:
        transmit(original_sets[0][3],
                 variable[0],
                 original_means[1],
                 original_means[2])
        variable[0] = variable[0] - variance[0]
        stop = acceptData()
    diff = original_means[0]-variable[0]
    print("Original extended delay:", original_means[0])
    print("Accepted extended variance:", diff)
    print("Variance:", round(100*(diff/original_means[0]), 4), "%")
    stop = False
    cycles = 0
    while not stop:
        transmit(original_sets[0][3],
                 original_means[0],
                 variable[1],
                 original_means[2])
        variable[1] = variable[1] - variance[1]
        stop = acceptData()
    diff = original_means[1]-variable[1]
    print("Original long delay:", original_means[1])
    print("Accepted long variance:", diff)
    print("Variance:", round(100*(diff/original_means[1]), 4), "%")
    stop = False
    cycles = 0
    while not stop:
        transmit(original_sets[0][3],
                 original_means[0],
                 original_means[1],
                 variable[2])
        variable[2] = variable[2] - variance[2]
        stop = acceptData()
    diff = original_means[2]-variable[2]
    print("Original short delay:", original_means[2])
    print("Accepted short variance:", diff)
    print("Variance:", round(100*(diff/original_means[2]), 4), "%")
"""
"""
Testing maximum and minimum signal variance
    variance = [0, 0, 0]
    variable = [original_means[0]/100,
                original_means[1]/100,
                original_means[2]/100]
    stop = False
    cycles = 0
    while not stop:
        transmit(original_sets[0][3],
                 original_means[0] + variance[0],
                 original_means[1] + variance[1],
                 original_means[2] + variance[2])
        variance[0] = variance[0] + variable[0]
        variance[1] = variance[1] + variable[1]
        variance[2] = variance[2] + variable[2]
        cycles = cycles + 1
        stop = acceptData()
    print(cycles, "/100 deviation before increase failure.")
    print("Maximum extended delay is", original_means[0] + variance[0])
    variance = [0, 0, 0]
    stop = False
    cycles = 0
    while not stop:
        transmit(original_sets[0][3],
                 original_means[0] - variance[0],
                 original_means[1] - variance[1],
                 original_means[2] - variance[2])
        variance[0] = variance[0] + variable[0]
        variance[1] = variance[1] + variable[1]
        variance[2] = variance[2] + variable[2]
        cycles = cycles + 1
        stop = acceptData()
    print(cycles, "/100 deviation before decrease failure.")
    print("Minimum extended delay is", original_means[0] -  variance[0])
"""


"""
Asks for a number, collects that many data samples, and returns the data sets.
"""
def collectData():
    data_sets = []
    print("How many samples would you like?")
    for i in range(getNonNegativeInt()):
        input("Hold FOB button, then press Enter to record: ")
        data_sets.append(gatherDataSample())
    return data_sets

"""
Gets a non-negative integer input.
"""
def getNonNegativeInt():
    number = 0
    success = False
    while not success:
        try:
            number = int(input('Enter a non-negative int: '))
            if number < 0:
                print('Input is below 0.')
            else:
                success = True
        except(ValueError):
            print('Input is not an integer.')
    return number

"""
Collects reciever data and returns the results.
"""
def gatherDataSample():
    RECEIVED_SIGNAL = [[], []]
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RECEIVE_PIN, GPIO.IN)
    while True:
        cumulative_time = 0
        beginning_time = datetime.now()
        print('**Started recording**')
        while cumulative_time < MAX_DURATION:
            time_delta = datetime.now() - beginning_time
            RECEIVED_SIGNAL[0].append(time_delta)
            RECEIVED_SIGNAL[1].append(GPIO.input(RECEIVE_PIN))
            cumulative_time = time_delta.seconds
        print('**Ended recording**')
        GPIO.cleanup()
        
        print('**Processing results**')
        
        #Time differences of the swaps
        t_diffs = extractTimeDifferences(RECEIVED_SIGNAL)
        
        """
        Find the extended delay that starts a transmission segment.
        If no valid transmission segments are found, function has returned -1
            Plot the given data for analysis, then quit
        """
        
        extended_delay = findValidSegment(0, t_diffs)
        if extended_delay < 0:
            print("Plotting...")
            plot(RECEIVED_SIGNAL)
        
        #Get the binary key from the signal
        binary_key = extractBinaryKey(extended_delay, t_diffs)
        
        """
        Now we know the location of the first extended delay as well as the binary key.
        Every extended delay is located at the 50th position from the previous.
        The binary key tells us exactly where the short and long delays fall between those extended delays.
        Between these two pieces of information, we can extract all short and long delays easily.
        We will operate on the data to extract the average short, long, and extended delay.
        """
        
        extended_average = 0
        extended_count = 0
        long_average = 0
        long_count = 0
        short_average = 0
        short_count = 0
        delay_index = 0
        key_index = 0
        
        #loop through every complete signal
        while extended_delay < (len(t_diffs) - 50):
            """
            Verify that the following segment of 50 signals follows the expected pattern
            If not, skip the current segment and find the next valid segment
            """
            if not validSegment(extended_delay, t_diffs):
                extended_delay = findValidSegment(extended_delay + 1, t_diffs)
                #if no Valid Segments found, extended delay is below 0 
                if extended_delay < 0:
                    break
            #add extended delay to average
            extended_average = extended_average + t_diffs[extended_delay]
            extended_count = extended_count + 1
            delay_index = extended_delay + 1
            #ensure we have not reached the final digit of the signal
            while (delay_index - extended_delay) < 49:
                #if '1', add first delay to short average and second delay to long average
                if binary_key[key_index] == '1':
                    short_average = short_average + t_diffs[delay_index]
                    short_count = short_count + 1
                    long_average = long_average + t_diffs[delay_index + 1]
                    long_count = long_count + 1
                #if '0', add first delay to long average and second delay to short average
                else:
                    long_average = long_average + t_diffs[delay_index]
                    short_count = short_count + 1
                    short_average = short_average + t_diffs[delay_index + 1]
                    long_count = long_count + 1
                #increment delay index by 2 and key index by 1
                delay_index = delay_index + 2
                key_index = key_index + 1
            #if the final digit is '1', final delay is added to short index
            if binary_key[key_index] == '1':
                short_average = short_average + t_diffs[delay_index]
                short_count = short_count + 1
            #if the final digit is '0', final delay is added to long index
            else:
                long_average = long_average + t_diffs[delay_index]
                long_count = long_count + 1
            #set all indexes to operate on next set of keys
            extended_delay = extended_delay + 50
            delay_index = extended_delay + 1
            key_index = 0
        
        """
        Perform final computations for averages and proportions.
        """
        if not extended_count:
            return []
        else:
            return [extended_average/extended_count,
                long_average/long_count,
                short_average/short_count,
                binary_key]

"""
Returns a list of the time differences between transmitted 1s and 0s.
"""
def extractTimeDifferences(signal_list):
    #The starting index of the last swap between 1 and 0
    last_index = 0
    #Last recorded number, 1 or 0
    last_number = signal_list[1][0]
    #List of time differences
    t_diffs = []
    #For each recorded signal
    for i in range (len(signal_list[0])):
        #convert time to microseconds
        signal_list[0][i] = signal_list[0][i].seconds + signal_list[0][i].microseconds/1000000.0
        #if last recorded number does not equal current number
        if (signal_list[1][i] != last_number):
            #find time difference then save difference and number
            t_diffs.append(signal_list[0][i] - signal_list[0][last_index])
            #save index of number change and what the number changed to
            last_index = i
            last_number = signal_list[1][i]
    #ignore start and stop of recording for accuracy
    del(t_diffs[-1])
    del(t_diffs[0])
    #Send back completed list
    return t_diffs

"""
Returns the index of the next valid segment
"""
def findValidSegment(current_index, t_diffs):
    max_index = len(t_diffs) - 51
    #While the current index is less than the maximum allowed.
    while current_index < max_index:
        #Find the next extended delay
        while not validExtendedDelay(t_diffs[current_index], t_diffs[current_index + 1]):
            current_index = current_index + 1
            #If current index is maximum allowed, stop looking.
            if current_index == max_index:
                return -1
        #Extended delay found. If valid segment, return the index.
        if validSegment(current_index, t_diffs):
            return current_index
        #If segment fails, try again.
        current_index = current_index + 1
    #Maximum index reached, stop looking.
    return -1
"""
Returns true is the test delay is extended and the second delay is not.
Extended delays are about 10 times the long delays. ~e = ~10l
Long delays are about 3 times the short delays. ~l = ~3s
So it stands to reason that:
    ~e < ~6e
    ~l < ~6s
    ~e > ~6l
    ~e > ~6s
Therefore, the following function is only true when
    A: The test delay is an extended delay
    B: The second delay is not an extended delay
If one of these is not true, the test delay does not meet the qualifications of a valid extended delay
"""
def validExtendedDelay(test_delay, second_delay):
    if test_delay > (6 * second_delay):
        return True
    return False

"""
Returns true if segment is valid.
If any of the next 49 delays are closer to the extended delay than they should be, Segment is invalid
If the 50th delay is not also an extended delay, segment is invalid
"""
def validSegment(current_index, t_diffs):
    #if the intervening delays aren't long or short delays, failure
    for i in range(1, 50):
        if not validExtendedDelay(t_diffs[current_index], t_diffs[current_index + i]):
            return False
    #if the 50th delay is not extended, failure
    if not firstTermCloserToSecondThanThird(t_diffs[current_index + 50], t_diffs[current_index], t_diffs[current_index + 1]):
        return False
    #The next 50 delays have passed the validity test for the segment
    return True  

"""
Returns true if the first number is closer to the second number than the third number.
To deteremine if the first number is closer to the second or third.
    1. Subtract each term from the first
    2. Take the absolute value of the results
    3. Compare which is closer to 0
"""
def firstTermCloserToSecondThanThird(first, second, third):
    if abs(first - second) < abs(first - third):
        return True
    return False

"""
Returns the binary key being transmitted.
"""
def extractBinaryKey(extended_delay, t_diffs):
    binary_key = ''
    current_digit = extended_delay + 1
    while current_digit < (extended_delay + 49):
        #if short delay comes before long delay, signal is 1
        if (t_diffs[current_digit] < t_diffs[current_digit + 1]):
            binary_key = binary_key + '1'
        #if long delay comes before short delay, signal is 0
        else:
            binary_key = binary_key + '0'
        current_digit = current_digit + 2
    #Because the final digit is followed by an extended delay we use a different method.
    #The first transmitted signal is always a 1, thus:
    #If the current delay is closer to the first delay of the first signal, current delay is a '1'
    #If not, then it is closer to the second delay of the first signal, current delay is a '0'
    if firstTermCloserToSecondThanThird(t_diffs[current_digit], t_diffs[extended_delay + 1], t_diffs[extended_delay + 2]):
        binary_key = binary_key + '1'
    else:
        binary_key = binary_key + '0'
    return binary_key

"""
Reorganize data so each sample is added grouped with others in the same category.
"""
def getBatchListsFromDataSets(data_sets):
    batch_lists = [[],[],[],[],[],[]]
    for i in range(len(data_sets)):
        if not data_sets[i]:
            break
        batch_lists[0].append(data_sets[i][0])
        batch_lists[1].append(data_sets[i][1])
        batch_lists[2].append(data_sets[i][2])
        batch_lists[3].append(data_sets[i][0]/data_sets[i][1])
        batch_lists[4].append(data_sets[i][1]/data_sets[i][2])
        batch_lists[5].append(data_sets[i][0]/data_sets[i][2])
    return batch_lists

"""
Find the means of each set of data samples.
"""
def findMeans(batch_names, batch_lists):
    means = []
    for i in range(6):
        means.append(stats.mean(batch_lists[i]))
        stDev = stats.stdev(batch_lists[i])
        print("Mean Average of", batch_names[i], ":", means[i])
        print("Std Deviation of", batch_names[i], ":", stDev)
        print("Std Deviation/Mean:", stDev/means[i])
    return means

"""
A function to let user validate data before continuing.
"""
def acceptData():
    while True:
        accept = input("Is data valid? [y/n] ")
        if accept == 'y':
            return True
        elif accept == 'n':
            return False
        print("Please input 'y' for yes or 'n' for no.")
    
"""
Transmit the given key with the given delays.
"""
def transmit(code, extended_delay, long_delay, short_delay):
    input("Press Enter to begin transmit test: ")
    print("Transmitting...")
    NUM_ATTEMPS = 15
    TRANSMIT_PIN = 27

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRANSMIT_PIN, GPIO.OUT)
    for t in range(NUM_ATTEMPS):
        for i in str(code):
            if i == '1':
                GPIO.output(TRANSMIT_PIN, 1)
                time.sleep(short_delay)
                GPIO.output(TRANSMIT_PIN, 0)
                time.sleep(long_delay)
            elif i == '0':
                GPIO.output(TRANSMIT_PIN, 1)
                time.sleep(long_delay)
                GPIO.output(TRANSMIT_PIN, 0)
                time.sleep(short_delay)
        GPIO.output(TRANSMIT_PIN, 0)
        time.sleep(extended_delay)
    GPIO.cleanup()

def plot(RECEIVED_SIGNAL):
    pyplot.plot(RECEIVED_SIGNAL[0], RECEIVED_SIGNAL[1])
    pyplot.axis([0, MAX_DURATION, -1, 2])
    pyplot.show()

if __name__ == '__main__':
	main()
