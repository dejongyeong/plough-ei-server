import cv2
import sys
import json
import time
from os.path import exists


def read_qr_code(filename):
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    # tracked scanned qr codes in run time so that it send signal only once for each scan
    scanned_codes = set()

    with open(filename, "r") as file:
        qr_codes = json.load(file)

    while True:
        _, frame = cap.read()
        decode, bbox, _ = detector.detectAndDecode(frame)

        if decode:

            # check if code is present in the dictionary
            if decode in qr_codes:
                if decode not in scanned_codes:
                    if qr_codes[decode]:
                        # not giving ice cream (show message on screen)
                        send_to_robot(False)
                    else:
                        # qr code is stored bot not used
                        qr_codes[decode] = True
                        scanned_codes.add(decode)
                        with open(filename, "w") as file:
                            json.dump(qr_codes, file)

                        # send signal to robot and give ice cream
                        send_to_robot(True)
                else:
                    # not giving ice cream (show message on screen)
                    send_to_robot(False)
                    print('QR code has already been processed')
            else:
                # qr code is new, not stored and send ice cream
                qr_codes[decode] = True
                scanned_codes.add(decode)
                with open(filename, "w") as file:
                    json.dump(qr_codes, file)

                send_to_robot(True)  # send signal to robot

        if bbox is not None and len(bbox) > 0:
            bbox = bbox[0].astype(int)
            cv2.polylines(frame, [bbox], True, color=(255, 0, 0), thickness=2)

        cv2.imshow("QR Code Reader", frame)

        if cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def send_to_robot(value):
    # Code to send the Boolean value to the robot application
    # Replace with your actual implementation
    print("Sending value to robot:", value)


if __name__ == "__main__":
    filename = 'data.json'
    if exists(filename):
        print('File exists')
    else:
        print('File does not exist')
        with open(filename, "w") as file:
            # Create an empty dictionary to initialize the json file
            json.dump({}, file)

    read_qr_code(filename)

    sys.exit()
