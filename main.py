import cv2
import sys
import json
from os.path import exists


def read_qr_code(filename):
    cap = cv2.VideoCapture(1)
    detector = cv2.QRCodeDetector()

    with open(filename, "r") as file:
        qr_codes = json.load(file)

    while True:
        _, frame = cap.read()
        decode, bbox, _ = detector.detectAndDecode(frame)

        if decode:
            # print("QR found: ", decode)

            if decode not in qr_codes:
                qr_codes.append(decode)
                with open(filename, "w") as file:
                    json.dump(qr_codes, file)
                print("QR code is stored and marked as unused.")

                # Send the Boolean value to the robot application
                send_to_robot(True)
            else:
                print("QR Code is already used.")

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
            # Create an empty list to initialize the json file
            json.dump([], file)

    read_qr_code(filename)

    sys.exit()
