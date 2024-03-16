from jetson_inference import detectNet
from jetson_utils import videoSource, videoOutput
import RPi.GPIO as GPIO
import time
import serial

# -------------------------- Setup gpio peripherals --------------------------

# Pin Setup:
GPIO.setmode(GPIO.BCM)  # BCM pin-numbering scheme from Raspberry Pi

# Set related pin numbers
N_To_A = 9  # BCM pin 9, BOARD pin 21
A_To_N = 5 # D5

# Set pin as an output pin with optional initial state of HIGH
GPIO.setup(N_To_A, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(A_To_N, GPIO.IN)

# -------------------------- Setup serial communication peripherals --------------------------

serial_port = serial.Serial(
    port="/dev/ttyTHS1",
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)

# -------------------------- AI Initiate -------------------------- 

our_model = detectNet(model="/home/grup8/Desktop/ELE495/5_obj_model/ssd-mobilenet.onnx", labels="/home/grup8/Desktop/ELE495/5_obj_model/labels.txt", input_blob="input_0", output_cvg="scores", output_bbox="boxes", threshold=0.5)
net = detectNet("ssd-mobilenet-v2", threshold=0.5)

camera = videoSource("/dev/video0")  # '/dev/video0' for V4L2
#display = videoOutput("display://0") # 'my_video.mp4' for file

# Initiate gstreamer early

img = camera.Capture()

while img is None: # capture timeout
    img = camera.Capture()
    
detections = our_model.Detect(img)
not_detected = net.Detect(img)

# Wait a second to let the port initialize
time.sleep(1)

usleep = lambda x: time.sleep(x/1000000.0)

# -------------------------- Global Variables --------------------------
apple_count = 0
banana_count = 0
lemon_count = 0
orange_count = 0
pen_count = 0
unknown_count = 0

apple_change = 0
banana_change = 0
lemon_change = 0
orange_change = 0
pen_change = 0
unknown_change = 0

# FSM States
# 0 => Initial state
# 1 => Rotate motor till box is found
# 2 => Wait for Centering the box for camera
# 3 => Take picture
# 4 => Evaluate findings with our model
# 5 => Evaluate findings with general model
# 6 => Transmit findings
# 7 => Move the box out of the way

def detection_parser(input_detection):
    # First ai

    global apple_count
    global banana_count
    global lemon_count
    global orange_count
    global pen_count
    global unknown_count
    
    global apple_change
    global banana_change
    global lemon_change
    global orange_change
    global pen_change
    global unknown_change
    
    apple_change = 0
    banana_change = 0
    lemon_change = 0
    orange_change = 0
    pen_change = 0
    unknown_change = 0

    for detection in input_detection:
        if detection.ClassID == 1:
            apple_count += 1
            apple_change += 1
        elif detection.ClassID == 2:
            banana_count += 1 
            banana_change += 1 
        elif detection.ClassID == 3:
            lemon_count += 1
            lemon_change += 1
        elif detection.ClassID == 4:
            #TODO: Add aditional filter
            orange_count += 1
            orange_change += 1
        elif detection.ClassID == 5:
            pen_count += 1
            pen_change += 1
    
def fsm():

    fsm_state = 0
    A_Answer = 0

    while True:

        if fsm_state == 0:
            # Initial State
            fsm_state = 1
            
        elif fsm_state == 1:
            # Rotate motor
            #confirmation = input("Confirm to move forward:")
            print("Current fsm state: ", fsm_state)
            GPIO.output(N_To_A,GPIO.HIGH)
            time.sleep(0.1)    # wait for given time
            GPIO.output(N_To_A,GPIO.LOW)
            fsm_state = 2
            
        elif fsm_state == 2:
            # Wait for Center
            print("Current fsm state: ", fsm_state)
            A_Answer = GPIO.input(A_To_N)
            while(A_Answer == 0):
                A_Answer = GPIO.input(A_To_N)
            fsm_state = 3
            
        elif fsm_state == 3:
            
            #confirmation = input("Confirm to move forward:")
            time.sleep(1)
             
            img = camera.Capture()
            
            while img is None: # capture timeout
               img = camera.Capture()
            
            fsm_state = 4
        
        elif fsm_state == 4:
        
            #confirmation = input("Confirm to move forward:")
    
            print("Current fsm state: ", fsm_state)
        
            detections = our_model.Detect(img)
        
            print("detected {:d} objects in image".format(len(detections)))
        
            for detection in detections:
                print(detection)
            
            fsm_state = 5
        
        elif fsm_state == 5:
    
            #confirmation = input("Confirm to move forward:")
        
            print("Current fsm state: ", fsm_state)
            
            not_detected = net.Detect(img)
        
            print("detected {:d} objects in image".format(len(not_detected)))
        
            for detection in not_detected:
                print(detection)
        
            fsm_state = 6
        
        elif fsm_state == 6:
    
            #confirmation = input("Confirm to move forward:")
        
            print("Current fsm state: ", fsm_state)
            
            # Write parser for both ai model outputs:
            detection_parser(detections)
            # Combine saved data
            #bluetooth_message = '|' + str(apple_count) + '|' + str(banana_count) + '|' + str(lemon_count) + '|' + str(orange_count) + '|' + str(pen_count) + '|' + str(unknown_count) + '|' + str(apple_change) + '|' + str(banana_change) + '|' + str(lemon_change) + '|' + str(orange_change) + '|' + str(pen_change) + '|' + str(unknown_change)
            
            bluetooth_message = '|' + str(apple_count) + '|' + str(banana_count) + '|' + str(lemon_count) + '|' + str(orange_count) + '|' + str(pen_count) + '|' + str(unknown_count)
            
            #for x in range(6):
            #    time.sleep(0.3)
                # Transmit via UART
            #    serial_port.write(bluetooth_message.encode())
                
            # Transmit via UART
            serial_port.write(bluetooth_message.encode())
    
            fsm_state = 7

        elif fsm_state == 7:
            # Move box out of the way
            print("Current fsm state: ", fsm_state)
            GPIO.output(N_To_A,GPIO.HIGH)
            time.sleep(0.1)    # wait for given time
            GPIO.output(N_To_A,GPIO.LOW)
            
            # Wait for Arduino Answer
            A_Answer = GPIO.input(A_To_N)
            while(A_Answer == 0):
                A_Answer = GPIO.input(A_To_N)
            fsm_state = 1
        
        else:
            state = 0

def main():
    # Main loop startup
    try:
        fsm()

    except KeyboardInterrupt:
        print("Exiting Program")

    except Exception as exception_error:
        print("Error occurred. Exiting Program")
        print("Error: " + str(exception_error))

    finally:
        serial_port.close()
        GPIO.cleanup()
        pass

if __name__ == '__main__':
    main()
