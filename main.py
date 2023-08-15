import cv2
import sys
import json
from os.path import exists
from urllib.parse import urlparse, parse_qs


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
            params = parse_qs(urlparse(decode).query)
            coupon = params.get('coupon', [None])[0]

            print(coupon)

            # check if coupon is not empty
            if coupon is not None and coupon != '':
                # check if code is present in the dictionary
                if coupon in qr_codes:
                    if coupon not in scanned_codes:
                        if qr_codes[coupon]:
                            # not giving ice cream (show message on screen)
                            send_to_robot(False)
                        else:
                            # qr code is stored bot not used, update dict
                            qr_codes[coupon] = True
                            scanned_codes.add(coupon)
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
                    qr_codes[coupon] = True
                    scanned_codes.add(coupon)
                    with open(filename, "w") as file:
                        json.dump(qr_codes, file)

                    send_to_robot(True)  # send signal to robot
            else:
                print('Unable to extract coupon code')

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
