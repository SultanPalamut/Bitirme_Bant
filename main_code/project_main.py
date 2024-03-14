from jetson_inference import detectNet
from jetson_utils import videoSource, videoOutput
import RPi.GPIO as GPIO
import time
import serial

# -------------------------- AI Initiate -------------------------- 

our_model = detectNet(model="/home/grup8/Desktop/ELE495/5_obj_model/ssd-mobilenet.onnx", labels="/home/grup8/Desktop/ELE495/5_obj_model/labels.txt", input_blob="input_0", output_cvg="scores", output_bbox="boxes", threshold=0.5)
camera = videoSource("/dev/video0")  # '/dev/video0' for V4L2
#display = videoOutput("display://0") # 'my_video.mp4' for file

# Initiate gstreamer early

img = camera.Capture()

while img is None: # capture timeout
    img = camera.Capture()
    
detections = our_model.Detect(img)

# -------------------------- Setup serial communication peripherals --------------------------

serial_port = serial.Serial(
    port="/dev/ttyTHS1",
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)

# Wait a second to let the port initialize
time.sleep(1)

# -------------------------- Setup gpio peripherals --------------------------

# Pin Setup:
GPIO.setmode(GPIO.BCM)  # BCM pin-numbering scheme from Raspberry Pi

# Set related pin numbers
N_To_A = 18  # BCM pin 18, BOARD pin 12
A_To_N = 23 # D23

# Set pin as an output pin with optional initial state of HIGH
GPIO.setup(N_To_A, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(A_To_N, GPIO.IN)

usleep = lambda x: time.sleep(x/1000000.0)

# FSM States
# 0 => Initial state
# 1 => Rotate motor till box is found
# 2 => Wait for Centering the box for camera
# 3 => Take picture
# 4 => Evaluate findings with our model
# 5 => Evaluate findings with general model
# 6 => Transmit findings
# 7 => Move the box out of the way
    
def fsm():

    fsm_state = 0
    A_Answer = 0

    while True:

        if fsm_state == 0:
            # Initial State
            fsm_state = 1
            
        elif fsm_state == 1:
            # Rotate motor
            confirmation = input("Confirm to move forward:")
            print("Current fsm state: ", fsm_state)
            GPIO.output(N_To_A,GPIO.HIGH)
            time.sleep(0.5)    # wait for given time
            GPIO.output(N_To_A,GPIO.LOW)
            
        elif fsm_state == 2:
            # Wait for Center
            print("Current fsm state: ", fsm_state)
            A_Answer = GPIO.input(A_To_N)
            while(A_Answer == 0):
                A_Answer = GPIO.input(A_To_N)
            fsm_state = 3
            
        elif fsm_state == 3:
            
            confirmation = input("Confirm to move forward:")
        
            img = camera.Capture()
            
            while img is None: # capture timeout
               img = camera.Capture()
            
            fsm_state = 4
        
        elif fsm_state == 4:
        
            confirmation = input("Confirm to move forward:")
    
            print("Current fsm state: ", fsm_state)
        
            detections = our_model.Detect(img)
        
            print("detected {:d} objects in image".format(len(detections)))
        
            for detection in detections:
                print(detection)
            
            fsm_state = 5
        
        elif fsm_state == 5:
    
            confirmation = input("Confirm to move forward:")
        
            print("Current fsm state: ", fsm_state)
        
            fsm_state = 6
        
        elif fsm_state == 6:
    
            confirmation = input("Confirm to move forward:")
        
            print("Current fsm state: ", fsm_state)
            
            # Transmit via UART
    
            fsm_state = 7

        elif fsm_state == 7:
            # Move box out of the way
            print("Current fsm state: ", fsm_state)
            GPIO.output(N_To_A,GPIO.HIGH)
            time.sleep(0.5)    # wait for given time
            GPIO.output(N_To_A,GPIO.LOW)
            
            # Wait for Arduino Answer
            A_Answer = GPIO.input(A_To_N)
            while(A_Answer == 0):
                A_Answer = GPIO.input(A_To_N)
            time.sleep(0.5)
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
