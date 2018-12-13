import RPi.GPIO as GPIO
import Adafruit_MCP3008
import time
from timeit import default_timer as timer
import math
import pygame



#Define pushbutton pins
mode_button = 21
start_or_stop_button = 20
set_code_button = 16 #set the desired code

#Define LED pins
unlocked_LED = 19
locked_LED = 26


CLK = 11
MOSI = 10
MISO = 9
CS = 8
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

read_pot = 0 # read from channel 0 of the MCP

begin = 0.0
end = 0.0
duration = []
user_code = []

c_duration = [1000, 1000, 1000]
combocode = ["L", "R", "L"] # code needed to unlock the system


pot_tol = 50
tolerance = 50 # deviation allowed from the actual value
start = False
secure = True
code_length = 3
lock_status = "locked" #initial status


 #setting up buttons, potentiometer and LEDs   
def setup():
    print("System initially locked")
    GPIO.setmode(GPIO.BCM) #use BCM pinout
    GPIO.setup(mode_button, GPIO.IN, pull_up_down = GPIO.PUD_UP)#Pushbutton1 as input
    GPIO.setup(set_code_button, GPIO.IN, pull_up_down = GPIO.PUD_UP)#pushbutton 3 as input
    GPIO.setup(start_or_stop_button, GPIO.IN, pull_up_down = GPIO.PUD_UP)#Pushbutton 2 as input
    GPIO.setup(set_code_button, GPIO.IN, pull_up_down = GPIO.PUD_UP)#pushbutton 3 as input

    GPIO.setup(unlocked_LED, GPIO.OUT)#set red LEd as output
    GPIO.setup(locked_LED, GPIO.OUT)#set green LEd as output
    
    GPIO.setup(MOSI, GPIO.OUT)
    GPIO.setup(MISO, GPIO.IN)
    GPIO.setup(CLK, GPIO.OUT)
    GPIO.setup(CS, GPIO.OUT)

    GPIO.add_event_detect(start_or_stop_button, GPIO.FALLING, callback=start_or_stop_callback, bouncetime=300)
    GPIO.add_event_detect(mode_button, GPIO.FALLING, callback=secure_or_insecure_callback, bouncetime=300)
    GPIO.add_event_detect(set_code_button, GPIO.FALLING, callback=set_code_callback, bouncetime=300)

    reset()

def clear():
    global begin, duration, user_code
    begin = timer()
    duration = []
    user_code = []
#function to reset to intial values
def reset():
    global start, secure, set_code
    clear()
    set_code = False
    start = False
    secure = True
    print("Initialising SECURE mode")
#function to start/stop
def start_or_stop_callback(channel):
    global start 
    if start:
        start = False
    else:
        start = True
        print("Ready")
        print("Start")
    clear()
#set user desired code     
def set_code_callback(channel):
    global set_code, start, combocode, c_duration, length
    if set_code == False:
        set_code = True
        combocode = []
        c_duration = []
        length = input("Enter the  length of the new code:\n")
        print("\nSet the new code:")
        start = True
    else:
        set_Code = False
#secure mode  or insecure mode function
def secure_or_insecure_callback(channel):
    global secure
    if secure:
        secure = False
        print("INSECURE mode activated")
    else:
        secure = True
        print("SECURE mode Activated")
    clear()


#getting directions
def read_turns(start_voltage, end_voltage):
    if start_voltage > end_voltage:
        return "R" # right direction relative to start voltage
    else:
        return "L"

def compare_times(): #compare times
    global duration, c_duration, secure
    if secure == False:
        duration.sort()
        c_duration.sort()
    for i in range(0, len(duration)):
        if abs(duration[i] - c_duration[i]) > tolerance:
            return False 
    return True

def compare_positions():#compare directions
    global user_code, combocode, secure
    if secure == False:
        return True
    for i in range(0, len(user_code)):
        if user_code[i] != combocode[i]:
            return False 
    return True

def unlocked(): #method to show status after succesfully entring a code
    global lock_status

    GPIO.output(unlocked_LED, GPIO.HIGH)
    time.sleep(4)
    GPIO.output(unlocked_LED, GPIO.LOW)
      
    lock_status = "unlocked"
    print("System UnLocked Congrats!!")

""" you finished here with locked and unlocked LEDs"""


def fail(): # Message after a failed attempt at unlocking
    print("Ooops try again")
    GPIO.output(locked_LED, GPIO.HIGH)
    time.sleep(4)
    GPIO.output(locked_LED, GPIO.LOW)
    lock_status = "locked"
    print("System Locked!!")    
   

def main():
    global start, begin, end, secure,length, set_code
    setup()

    try:
        while True:
            start_voltage = mcp.read_adc(read_pot)
            end_voltage = mcp.read_adc(read_pot)
            value = True
            time.sleep(0.5)
            while start:
                begin = timer()
                timeout = False
                while abs(end_voltage - start_voltage) < pot_tol:
                    end_voltage = mcp.read_adc(read_pot)
                    end = timer()#restart timer in the event of an input at the pot
                    if (end-begin) > 5:#Wait for input for 5 seconds
                        timeout = True
                        break
                    value = False
                    time.sleep(0.5)

                if timeout:
                    clear()
                    print("Timeout press start to continue")
                    start = False
                    break
                begin = timer()

                start_pos = mcp.read_adc(read_pot)
                end_pos = mcp.read_adc(read_pot)

                while abs(start_voltage-start_pos) > pot_tol:
                    end_pos = mcp.read_adc(read_pot)
                    value = True
                    time.sleep(0.5)
                    start_pos = mcp.read_adc(read_pot)
                    if abs(end_pos-start_pos) < pot_tol:
                        break
                    
                end = timer() 
                if value:
                    if set_code:
                        c_duration.append((end-begin)*100)
                        combocode.append(read_turns(start_voltage, end_voltage))
                    else:
                        duration.append((end-begin)*100)
                        user_code.append(read_turns(start_voltage, end_voltage))
                    value = False
                    start_voltage = mcp.read_adc(read_pot)
                    end_voltage = mcp.read_adc(read_pot)
                if set_code:
                    if len(c_duration) == length:
                        print("Succesfully entered custom code")
                        print(combocode)
                        reset()
                        break
                else:
                    if (len(user_code) == len(combocode)) or len(user_code) >= 16:
                        print("Time spent entering code!")
                        print(c_duration)
                        print("Code entered by user!")
                        print(combocode)
                        if (compare_times() and compare_positions()):
                            unlocked()
                        else:
                            fail()
                        clear()
                        start = False
                        break
    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
