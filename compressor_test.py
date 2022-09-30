import sys
import time
import random
import RPi.GPIO as GPIO

TRANSMIT_PIN = 17

def compressor_stress_test():
    
    #setup output pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRANSMIT_PIN, GPIO.OUT)
    
    #initiate time variables
    randomInterval = 0
    totalOnMinutes = 0
    offTime = 0
    
    print("Note: Run Time only tracks previous cycles. If")
    print("      the test is stopped while compressors are")
    print("      running, the current cycle is not tracked.") 
    
    #loop
    try:
        while True:
            #enable pin for 4 minutes
            GPIO.output(TRANSMIT_PIN, 1)
            time.sleep(240)
            totalOnMinutes = totalOnMinutes + 4
            
            #disable pin for 1-10 minutes
            GPIO.output(TRANSMIT_PIN, 0)
            randomInterval = random.randint(60, 300)
            time.sleep(randomInterval)
            offTime = offTime + randomInterval

    #halt test
    except KeyboardInterrupt:        
        GPIO.output(TRANSMIT_PIN, 0)
        print("")
        print("-----------")
        print("Test Halted")
        print("-----------")
        
        #find average off time
        if totalOnMinutes:
            offTime = (offTime / (totalOnMinutes/4))
            print("Total run time is " + str(totalOnMinutes) + " minutes.")
            print("Average down time is " + str(offTime // 60) + " minutes and " + str(offTime % 60) + " seconds.")
        else:
            print("Test halted in first cycle.")
    
        #cleanup Pi
        GPIO.cleanup()
    
if __name__ == '__main__':
    exec('compressor_stress_test()')