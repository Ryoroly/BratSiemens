import cv2
import numpy as np
from picamera2 import Picamera2
import time

class ArucoCropper:
    """
    O clasa pentru a detecta 4 markere ArUco de referinta, a decupa regiunea
    interioara si a o returna ca o imagine corectata din perspectiva.
    """
    def __init__(self, camera_resolution=(4608, 2592), reference_ids=[0, 1, 2, 3]):
        """
        Initializeaza camera si detectorul ArUco.
        :param camera_resolution: Rezolutia maxima a senzorului camerei.
        :param reference_ids: Lista cu ID-urile markerelor de colt.
        """
        # Constante pentru ArUco
        self.REFERENCE_IDS = reference_ids
        self.ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
        self.DETECTOR_PARAMS = cv2.aruco.DetectorParameters()
        self.DETECTOR = cv2.aruco.ArucoDetector(self.ARUCO_DICT, self.DETECTOR_PARAMS)

        # Initializare si configurare Picamera2
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": camera_resolution}
        )
        self.picam2.configure(config)
        self.picam2.start()
        print(f"📷 Camera initializata la rezolutia {camera_resolution}.")
        time.sleep(1)  # Timp pentru stabilizarea senzorului

        # Stocam ultima pozitie a colturilor gasite
        self._last_inner_corners_px = None

    def capture_frame(self):
        """Captureaza un singur cadru de la camera."""
        return self.picam2.capture_array()

    def get_cropped_image(self, frame):
        """
        Detecteaza cele 4 markere ArUco si returneaza o imagine decupata,
        corectata din perspectiva, a regiunii interioare.
        Returneaza np.array sau None.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        corners, ids, _ = self.DETECTOR.detectMarkers(gray)

        if ids is None or len(ids) < 4:
            self._last_inner_corners_px = None
            return None

        ids = ids.flatten()
        inner_corners = {}
        for i, marker_id in enumerate(ids):
            if marker_id not in self.REFERENCE_IDS:
                continue
            marker_corners = corners[i][0]
            if marker_id == self.REFERENCE_IDS[0]:  # TL
                inner_corners[0] = marker_corners[2]
            elif marker_id == self.REFERENCE_IDS[1]:  # TR
                inner_corners[1] = marker_corners[3]
            elif marker_id == self.REFERENCE_IDS[2]:  # BR
                inner_corners[2] = marker_corners[0]
            elif marker_id == self.REFERENCE_IDS[3]:  # BL
                inner_corners[3] = marker_corners[1]

        if len(inner_corners) != 4:
            self._last_inner_corners_px = None
            return None

        # Puncte sursa ordonate: TL, TR, BR, BL
        src = np.array([
            inner_corners[0], inner_corners[1],
            inner_corners[2], inner_corners[3]
        ], dtype="float32")
        self._last_inner_corners_px = inner_corners.copy()

        # Dimensiuni dinamice
        w_top = np.linalg.norm(src[0] - src[1])
        w_bot = np.linalg.norm(src[3] - src[2])
        h_left = np.linalg.norm(src[0] - src[3])
        h_right = np.linalg.norm(src[1] - src[2])
        W, H = int(max(w_top, w_bot)), int(max(h_left, h_right))
        if W == 0 or H == 0:
            self._last_inner_corners_px = None
            return None

        dst = np.array([[0,0], [W-1,0], [W-1,H-1], [0,H-1]], dtype="float32")
        M = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(frame, M, (W, H))
        return warped

    def get_aruco_inner_corners_px(self):
        """
        Returneaza coordonatele colturilor interioare din ultimul cadru detectat.
        """
        return self._last_inner_corners_px

    def flush(self, num_frames=3):
        """
        Flush any remaining frames from Picamera2 buffer by capturing and discarding.
        """
        for _ in range(num_frames):
            _ = self.picam2.capture_array()

    def stop(self):
        """Opreste camera si elibereaza resursele."""
        self.picam2.stop()
        print("📷 Camera oprita.")