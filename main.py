import cv2
import sys
import json
import serial
import tkinter as tk
from os.path import exists
from PIL import ImageTk, Image
from tkinter import PhotoImage, StringVar
from urllib.parse import urlparse, parse_qs


# ! change the serial port number based on what you see
# ser = serial.Serial('/dev/tty.usbmodem323103')  # open serial port


class Robot:
    def __init__(self):
        self.busy = False
        self.ready_event = True    # initial state: ready

    def set_busy(self):
        self.busy = True
        self.ready_event = False

    def set_ready(self):
        self.busy = False
        self.ready_event = True

    def is_ready(self):
        return self.ready_event


class QRCodeScannerApp:
    def __init__(self, root, filename, robot):
        self.root = root
        self.filename = filename
        self.robot = robot

        self.root.title("QR Code Scanner")

        # logos
        self.ei = ImageTk.PhotoImage(Image.open(
            'ei.png').resize((350, 256)))

        self.reedi = ImageTk.PhotoImage(Image.open(
            'reedi.png').resize((300, 256)))

        self.image_frame = tk.Frame(root)
        self.image_frame.pack()

        self.ei_label = tk.Label(self.image_frame, image=self.ei)
        self.ei_label.pack(side=tk.LEFT)

        self.reedi_label = tk.Label(self.image_frame, image=self.reedi)
        self.reedi_label.pack(side=tk.LEFT)

        ###
        ###

        # create a string variable to dynamically update label text
        self.status_var = StringVar()
        self.status_var.set('Ready for QR code scanning...')

        # create labels for displaying messages
        self.status_label = tk.Label(
            root, textvariable=self.status_var, font=("Helvetica", 16))
        self.status_label.pack(pady=10)

        # create images for waiting and busy screens
        self.waiting_image = PhotoImage(file="waiting.png")
        self.busy_image = PhotoImage(file="busy.png")

        # create a canvas for displaying images
        self.canvas = tk.Canvas(root, width=800, height=500)
        self.canvas.pack()

        # start the video capture
        self.cap = cv2.VideoCapture(1)
        self.detector = cv2.QRCodeDetector()

        self.scanned_codes = set()

        with open(filename, "r") as file:
            self.qr_codes = json.load(file)

        # Start processing frames
        self.process_frame()

    ###
    ###
    ###

    def update_status_label(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def process_frame(self):
        _, frame = self.cap.read()

        # ! uncomment below in production
        # if(ser.inWaiting()):
        #     inp_char = ser.read()

        #     if inp_char == b'H':
        #         print("inp_char", inp_char)
        #         robot.set_ready()
        #         self.update_status_label("Ready for QR code scanning...")
        #         # call process_frame again to continue scanning
        #         self.root.after(10, self.process_frame)  # Add this line

        #     if inp_char == b'L':
        #         print("inp_char", inp_char)
        #         robot.set_busy()

        if not self.robot.is_ready():
            self.display_busy_screen()
        else:
            try:
                decode, bbox, _ = self.detector.detectAndDecode(frame)
            except cv2.error:
                decode, bbox = None, None

            if decode:
                params = parse_qs(urlparse(decode).query)
                coupon = params.get('coupon', [None])[0]

                if coupon is not None and coupon != '':
                    if coupon in self.qr_codes:
                        if coupon not in self.scanned_codes:
                            if self.qr_codes[coupon]:
                                self.update_status_label(
                                    "Coupon code expired!!")
                            else:
                                self.qr_codes[coupon] = True
                                self.scanned_codes.add(coupon)
                                with open(self.filename, "w") as file:
                                    json.dump(self.qr_codes, file)

                                self.send_to_robot()
                                self.update_status_label(
                                    "Coupon accepted, preparing your ice cream...")
                        else:
                            self.update_status_label("Coupon code expired!!")
                    else:
                        self.qr_codes[coupon] = True
                        self.scanned_codes.add(coupon)
                        with open(self.filename, "w") as file:
                            json.dump(self.qr_codes, file)

                        self.send_to_robot()
                        self.update_status_label(
                            "Coupon accepted, preparing your ice cream...")
                else:
                    self.update_status_label(
                        "Unable to extract coupon code from QR code..")

                if bbox is not None and len(bbox) > 0:
                    bbox = bbox[0].astype(int)
                    cv2.polylines(frame, [bbox], True, (0, 0, 255), 2)

            self.display_waiting_screen()

        # display robot status on frame
        self.display_frame(frame)

        # ! have to test this
        # call process_frame again after a delay
        self.root.after(10, self.process_frame)

    def display_frame(self, frame):
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape

        # Calculate the position to place the frame in the center of the canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = (canvas_width - w) // 2
        y = (canvas_height - h) // 2

        self.photo = tk.PhotoImage(
            data=cv2.imencode('.png', frame)[1].tobytes())
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)

    def display_waiting_screen(self):
        self.update_status_label("Ready for QR code scanning...")
        self.canvas.delete("all")

    def display_busy_screen(self):
        self.update_status_label(
            "Robot is busy preparing ice cream, please wait...")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.busy_image)

    def send_to_robot(self):
        print('signal sent to robot')
        # ! uncomment below for production
        # ser.write(b'K')     # write a string

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()
        # ! uncomment below for production
        # ser.close()
        self.root.destroy()


if __name__ == "__main__":
    filename = 'data.json'
    robot = Robot()

    if exists(filename):
        print('File exists')
    else:
        print('File does not exist')
        with open(filename, "w") as file:
            # Create an empty dictionary to initialize the json file
            json.dump({}, file)

    # Create a tkinter window
    root = tk.Tk()
    app = QRCodeScannerApp(root, filename, robot)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()

    # read_qr_code(filename, robot)

    sys.exit()


# https://www.freepik.com/free-vector/robot-thinking-cube-isometric-composition_4300553.htm#query=robot%20waiting&position=8&from_view=search&track=ais


# def display_message_on_frame(frame, message):
#     cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
#                 1, (0, 0, 255), 2)


# def send_to_robot(robot):
#     print('signal sent to robot')

#     time.sleep(2)
#     SIGNAL_PIN_TO_ROBOT = 17
#     SIGNAL_PIN_FROM_ROBOT = 27  # feedback signal from robot

#     # GPIO.setmode(GPIO.BCM)
#     # GPIO.setup(SIGNAL_PIN_TO_ROBOT, GPIO.OUT)
#     # GPIO.setup(SIGNAL_PIN_FROM_ROBOT, GPIO.IN)

#     # # set robot as busy
#     # robot.set_busy()

#     # # sending signals to the robot
#     # GPIO.output(SIGNAL_PIN_TO_ROBOT, GPIO.HIGH)

#     # # wait for robot's completion signal
#     # while not GPIO.input(SIGNAL_PIN_FROM_ROBOT):
#     #     pass       # wait until the signal is received, could do time.sleep()??

#     # # set output pin to low after sending the signal to robot
#     # GPIO.output(SIGNAL_PIN_TO_ROBOT, GPIO.LOW)

#     # # signal received, set robot as ready
#     # robot.set_ready()

#     # GPIO.cleanup()


# def read_qr_code(filename, robot):
#     cap = cv2.VideoCapture(0)
#     detector = cv2.QRCodeDetector()
#     # tracked scanned qr codes in run time so that it send signal only once for each scan
#     scanned_codes = set()
#     display_message = "Ready for QR code scanning..."    # initialize the message
#     robot.set_busy()

#     with open(filename, "r") as file:
#         qr_codes = json.load(file)

#     while True:
#         _, frame = cap.read()

#         if not robot.is_ready():
#             display_message = "Robot is busy preparing ice cream, please wait..."
#         else:
#             display_message = "Ready for QR code scanning..."

#             try:
#                 decode, bbox, _ = detector.detectAndDecode(frame)
#             except cv2.error:
#                 decode, bbox = None, None

#             if decode:
#                 params = parse_qs(urlparse(decode).query)
#                 coupon = params.get('coupon', [None])[0]

#                 # check if coupon is not empty
#                 if coupon is not None and coupon != '':
#                     # check if code is present in the dictionary
#                     if coupon in qr_codes:
#                         if coupon not in scanned_codes:
#                             if qr_codes[coupon]:
#                                 # not giving ice cream (show message on screen)
#                                 display_message = "Coupon code expired!!"
#                             else:
#                                 # qr code is stored bot not used, update dict
#                                 qr_codes[coupon] = True
#                                 scanned_codes.add(coupon)
#                                 with open(filename, "w") as file:
#                                     json.dump(qr_codes, file)

#                                 # send signal to robot and give ice cream
#                                 display_message = "Coupon accepted, preparing your ice cream..."
#                                 send_to_robot(robot)
#                         else:
#                             # not giving ice cream (show message on screen)
#                             display_message = "Coupon code expired!!"
#                     else:
#                         # qr code is new, not stored and send ice cream
#                         qr_codes[coupon] = True
#                         scanned_codes.add(coupon)
#                         with open(filename, "w") as file:
#                             json.dump(qr_codes, file)

#                         # send signal to robot
#                         send_to_robot(robot)
#                         display_message = "Coupon accepted, preparing your ice cream..."
#                 else:
#                     display_message = "Unable to extract coupon code from QR code.."

#                 if bbox is not None and len(bbox) > 0:
#                     bbox = bbox[0].astype(int)
#                     cv2.polylines(frame, [bbox], True, (255, 0, 0), 2)

#         # display robot status on frame
#         display_message_on_frame(frame, display_message)
#         cv2.imshow("QR Code Reader", frame)

#         if cv2.waitKey(1) == ord("q"):
#             break

#         if cv2.waitKey(1) == ord("r"):
#             robot.set_ready()
#             print('Robot is ready')

#     cap.release()
#     cv2.destroyAllWindows()
