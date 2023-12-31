import cv2
import sys
import json
import time
import serial
import argparse
import tkinter as tk
from os.path import exists
from PIL import ImageTk, Image
from tkinter import StringVar
from urllib.parse import urlparse, parse_qs


parser = argparse.ArgumentParser(
    description="QR Code Scanner for Ploughing EI")
parser.add_argument('--serial-port', type=str, default='COM3',
                    help='Serial port for robot communication (e.g., COM3)')
parser.add_argument('--video-capture', type=int, default=1, choices=[
                    0, 1], help="Video capture source (0 for built-in webcam, 1 for external webcam)")
args = parser.parse_args()


SERIAL_PORT = args.serial_port
VIDEO_CAPTURE = args.video_capture


###
# Code starts below
###

global serial_available


try:
    # ser = serial.Serial('/dev/tty.usbmodem323103')  # open serial port
    ser = serial.Serial(SERIAL_PORT)
    serial_available = True
except:
    print("no serial device.. running in non-serial mode")
    serial_available = False

print(serial_available)


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

        self.current_time = 0
        self.timeout_timer = 0
        self.timeout_value = 5

        self.root.title("National Ploughing Championship 2023")

        # read image
        self.busy_image = ImageTk.PhotoImage(
            Image.open('busy.jpg').resize((600, 500)))
        self.ei = ImageTk.PhotoImage(Image.open('ei.png').resize((450, 200)))
        self.reedi = ImageTk.PhotoImage(
            Image.open('reedi.png').resize((300, 256)))

        # ei logos
        ###
        self.ei_frame = tk.Frame(root)
        self.ei_frame.pack()

        self.ei_label = tk.Label(self.ei_frame, image=self.ei)
        self.ei_label.pack(side=tk.LEFT, pady=10)

        # Message
        ###
        self.welcome_label = tk.Label(
            root, text='Welcome to National Ploughing Championship 2023', font=("Helvetica", 16), fg="#023662")
        self.welcome_label.pack()

        self.subtitle_label = tk.Label(
            root, text='Scan QR code to retrieve your ice cream', font=("Helvetica", 12), fg="#023662")
        self.subtitle_label.pack(pady=10)

        # create a canvas for displaying images
        ###
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(pady=10)

        self.canvas = tk.Canvas(self.canvas_frame, width=1080, height=550)
        self.canvas.pack()

        # string variable
        ###
        self.status_frame = tk.Frame(root)
        self.status_frame.pack(pady=25)

        self.status_var = StringVar()
        self.status_var.set('Ready for QR code scanning...')

        # create labels for displaying messages
        self.status_label = tk.Label(
            self.status_frame, textvariable=self.status_var, font=("Helvetica", 32))
        self.status_label.pack()

        # reedi label and created by
        ###
        self.reedi_frame = tk.Frame(root)
        self.reedi_frame.pack(pady=250)

        self.reedi_label = tk.Label(self.reedi_frame, image=self.reedi)
        self.reedi_label.pack(side=tk.TOP)

        self.created_label = tk.Label(
            self.reedi_frame, text='Developed by: De Jong Yeong, Anshul Awasthi, Krishna Panduru', font=("Helvetica", 12), fg="#023662")
        self.created_label.pack(side=tk.BOTTOM)

        # start the video capture
        self.cap = cv2.VideoCapture(VIDEO_CAPTURE)
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

        timeout_activated = False
        self.current_time = time.time()

        if (serial_available):
            if (ser.inWaiting()):
                inp_char = ser.read()

                if inp_char == b'H':
                    print("inp_char", inp_char)
                    robot.set_ready()
                    # self.update_status_label("Ready for QR code scanning...")
                    # call process_frame again to continue scanning
                    self.root.after(10, self.process_frame)  # Add this line

                if inp_char == b'L':
                    print("inp_char", inp_char)
                    robot.set_busy()

        if not self.robot.is_ready():
            self.display_busy_screen()
        else:
            try:
                decode, bbox, _ = self.detector.detectAndDecode(frame)
            except cv2.error:
                decode, bbox = None, None

            self.current_time = time.time()

            if decode:
                params = parse_qs(urlparse(decode).query)
                coupon = params.get('coupon', [None])[0]

                # check if coupon is empty from the qr code
                if coupon is not None and coupon != '':
                    print('current_time', self.current_time)

                    if (timeout_activated == False):
                        self.timeout_timer = self.current_time + self.timeout_value
                        timeout_activated = True
                        print('timeout_activated', self.timeout_timer)

                    # ! for testing used, we can remove the if statement for production?
                    # https://plough-ei.vercel.app/?coupon=49515f43-c28b-45a7-8edc-086340ff837b
                    # uuid is randomly generated, chances of repeated uuid is near 0 - negligible.
                    if coupon == '49515f43-c28b-45a7-8edc-086340ff837b':
                        if self.current_time < self.timeout_timer and timeout_activated:
                            self.update_status_label(
                                "Coupon accepted, preparing your ice cream...")

                        self.send_to_robot()
                    else:
                        # main if-statement for production
                        # check if coupon is present in the dictionary json file
                        if coupon in self.qr_codes:
                            # check the scanned_codes set, if coupon not found in the set
                            if coupon not in self.scanned_codes:
                                # handle the case where coupon not in the set but is already in the json dict
                                # and we check if the coupon has been used or not
                                if self.qr_codes[coupon]:
                                    if self.current_time < self.timeout_timer and timeout_activated:
                                        self.update_status_label(
                                            "Coupon code expired!!")
                                else:
                                    # coupon is in the json dict but is not used, update dict
                                    self.qr_codes[coupon] = True
                                    self.scanned_codes.add(coupon)
                                    with open(self.filename, "w") as file:
                                        json.dump(self.qr_codes, file)

                                    if self.current_time < self.timeout_timer and timeout_activated:
                                        self.update_status_label(
                                            "Coupon accepted, preparing your ice cream...")

                                    self.send_to_robot()
                            else:
                                if self.current_time < self.timeout_timer and timeout_activated:
                                    self.update_status_label(
                                        "Coupon code expired!!")
                        else:
                            # coupon is new, not stored previously in set or json dict
                            self.qr_codes[coupon] = True
                            self.scanned_codes.add(coupon)
                            with open(self.filename, "w") as file:
                                json.dump(self.qr_codes, file)

                            if self.current_time < self.timeout_timer and timeout_activated:
                                self.update_status_label(
                                    "Coupon accepted, preparing your ice cream...")

                            self.send_to_robot()

                else:
                    if self.current_time < self.timeout_timer and timeout_activated:
                        self.update_status_label(
                            "Unable to extract coupon code from QR code..")

                if bbox is not None and len(bbox) > 0:
                    bbox = bbox[0].astype(int)
                    cv2.polylines(frame, [bbox], True, (0, 0, 255), 2)

            if self.timeout_timer < self.current_time and not timeout_activated:
                timeout_activated = False
                self.display_waiting_screen()

        # display robot status on frame
        self.display_frame(frame)

        # ! might need to further check this
        # call process_frame again after a delay
        self.root.after(1, self.process_frame)

    def display_frame(self, frame):
        if not self.robot.is_ready():
            return

        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape

        # calculate the position to place the frame in the center of the canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = (canvas_width - w) // 2
        y = (canvas_height - h) // 2

        self.photo = tk.PhotoImage(
            data=cv2.imencode('.png', frame)[1].tobytes())
        self.canvas.create_image(x, 0, anchor=tk.NW, image=self.photo)

    def display_waiting_screen(self):
        self.update_status_label("Ready for QR code scanning...")
        self.canvas.delete("all")   # clear canvas

    def display_busy_screen(self):
        self.update_status_label(
            "Robot is busy preparing ice cream, please wait...")
        self.canvas.delete("all")   # clear canvas

        canvas_width = self.canvas.winfo_width()
        x = (canvas_width - self.busy_image.width()) // 2

        self.canvas.create_image(x, 0, anchor=tk.NW, image=self.busy_image)

    def send_to_robot(self):
        print('signal sent to robot')
        if (serial_available):
            ser.write(b'K')     # write a string - green light

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()

        if (serial_available):
            ser.close()

        self.root.destroy()


if __name__ == "__main__":
    filename = 'data.json'
    robot = Robot()

    if exists(filename):
        print('File exists')
    else:
        print('File does not exist')
        with open(filename, "w") as file:
            # create an empty dictionary to initialize the json file
            json.dump({}, file)

    # Create a tkinter window
    root = tk.Tk()
    app = QRCodeScannerApp(root, filename, robot)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()

    sys.exit()
