import cv2
import sys
import json
from os.path import exists
from urllib.parse import urlparse, parse_qs


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


def display_message_on_frame(frame, message):
    cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 0, 255), 2)


def send_to_robot(robot):
    print('signal sent to robot')

    SIGNAL_PIN_TO_ROBOT = 17
    SIGNAL_PIN_FROM_ROBOT = 27  # feedback signal from robot

    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(SIGNAL_PIN_TO_ROBOT, GPIO.OUT)
    # GPIO.setup(SIGNAL_PIN_FROM_ROBOT, GPIO.IN)

    # # set robot as busy
    # robot.set_busy()

    # # sending signals to the robot
    # GPIO.output(SIGNAL_PIN_TO_ROBOT, GPIO.HIGH)

    # # wait for robot's completion signal
    # while not GPIO.input(SIGNAL_PIN_FROM_ROBOT):
    #     pass       # wait until the signal is received, could do time.sleep()??

    # # set output pin to low after sending the signal to robot
    # GPIO.output(SIGNAL_PIN_TO_ROBOT, GPIO.LOW)

    # # signal received, set robot as ready
    # robot.set_ready()

    # GPIO.cleanup()


def read_qr_code(filename, robot):
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    # tracked scanned qr codes in run time so that it send signal only once for each scan
    scanned_codes = set()
    display_message = "Ready for QR code scanning..."    # initialize the message

    with open(filename, "r") as file:
        qr_codes = json.load(file)

    while True:
        _, frame = cap.read()

        if not robot.is_ready():
            display_message = "Robot is busy preparing ice cream, please wait..."
        else:
            display_message = "Ready for QR code scanning..."

            try:
                decode, bbox, _ = detector.detectAndDecode(frame)
            except cv2.error:
                decode, bbox = None, None

            if decode:
                params = parse_qs(urlparse(decode).query)
                coupon = params.get('coupon', [None])[0]

                # check if coupon is not empty
                if coupon is not None and coupon != '':
                    # check if code is present in the dictionary
                    if coupon in qr_codes:
                        if coupon not in scanned_codes:
                            if qr_codes[coupon]:
                                # not giving ice cream (show message on screen)
                                display_message = "Coupon code expired!!"
                            else:
                                # qr code is stored bot not used, update dict
                                qr_codes[coupon] = True
                                scanned_codes.add(coupon)
                                with open(filename, "w") as file:
                                    json.dump(qr_codes, file)

                                # send signal to robot and give ice cream
                                display_message = "Coupon accepted, preparing your ice cream..."
                                send_to_robot(robot)
                        else:
                            # not giving ice cream (show message on screen)
                            display_message = "Coupon code expired!!"
                    else:
                        # qr code is new, not stored and send ice cream
                        qr_codes[coupon] = True
                        scanned_codes.add(coupon)
                        with open(filename, "w") as file:
                            json.dump(qr_codes, file)

                        # send signal to robot
                        send_to_robot(robot)
                        display_message = "Coupon accepted, preparing your ice cream..."
                else:
                    display_message = "Unable to extract coupon code from QR code.."

                if bbox is not None and len(bbox) > 0:
                    bbox = bbox[0].astype(int)
                    cv2.polylines(frame, [bbox], True, (255, 0, 0), 2)

        # display robot status on frame
        display_message_on_frame(frame, display_message)
        cv2.imshow("QR Code Reader", frame)

        if cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


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

    read_qr_code(filename, robot)

    sys.exit()
