import cv2
import numpy as np
import os

def nothing(x):
    pass

def detect(image, hsv):
    hsv_frame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Primary object mask using slider-controlled HSV thresholds
    object_mask = cv2.inRange(
        hsv_frame,
        np.array([hsv["lh"], hsv["ls"], hsv["lv"]]),
        np.array([hsv["uh"], hsv["us"], hsv["uv"]])
    )

    # Shadow mask — low saturation and value
    shadow_mask = cv2.inRange(hsv_frame, (0, 0, 0), (180, 60, 80))

    # Subtract shadows from object mask
    mask = cv2.bitwise_and(object_mask, cv2.bitwise_not(shadow_mask))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) > 1000:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return image, mask, shadow_mask

def main():
    folder_path = "./my_photos"
    files = [file for file in os.listdir(folder_path) if file.endswith(('.png', '.jpg', '.jpeg'))]
    index = 0

    cv2.namedWindow("Trackbars")
    cv2.createTrackbar("L - H", "Trackbars", 0, 179, nothing)
    cv2.createTrackbar("L - S", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("L - V", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("U - H", "Trackbars", 179, 179, nothing)
    cv2.createTrackbar("U - S", "Trackbars", 255, 255, nothing)
    cv2.createTrackbar("U - V", "Trackbars", 255, 255, nothing)

    while True:
        image = cv2.imread(os.path.join(folder_path, files[index]))
        image = cv2.resize(image, (640, 480))

        hsv = {
            "lh": cv2.getTrackbarPos("L - H", "Trackbars"),
            "ls": cv2.getTrackbarPos("L - S", "Trackbars"),
            "lv": cv2.getTrackbarPos("L - V", "Trackbars"),
            "uh": cv2.getTrackbarPos("U - H", "Trackbars"),
            "us": cv2.getTrackbarPos("U - S", "Trackbars"),
            "uv": cv2.getTrackbarPos("U - V", "Trackbars")
        }

        result, mask, shadow_mask = detect(image.copy(), hsv)

        cv2.imshow("Image", result)
        cv2.imshow("Mask", mask)
        cv2.imshow("Shadow Mask (Debug)", shadow_mask)

        key = cv2.waitKey(0)

        if key == ord('q'):
            break
        elif key == ord('n'):
            index = (index + 1) % len(files)
        elif key == ord('p'):
            index = (index - 1) % len(files)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
