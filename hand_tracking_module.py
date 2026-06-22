import cv2
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandDetector:
    def __init__(self, model_path: str, max_hands: int = 1):
        self.lm_list = []
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def find_hands(self, image, draw: bool = True, timestamp_ms: int = 0):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = self.detector.detect_for_video(mp_img, timestamp_ms)

        self.lm_list = []
        h, w, _ = image.shape

        if results.hand_landmarks:
            for hand in results.hand_landmarks:
                for idx, lm in enumerate(hand):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.lm_list.append([idx, cx, cy])
                    if draw:
                        cv2.circle(image, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

        return image

    def fingers_up(self) -> list:
        if not self.lm_list:
            return [0, 0, 0, 0, 0]
        fingers = []
        
        fingers.append(1 if self.lm_list[4][1] > self.lm_list[3][1] else 0)
        
        for tip in [8, 12, 16, 20]:
            fingers.append(1 if self.lm_list[tip][2] < self.lm_list[tip - 2][2] else 0)
        return fingers

    def find_distance(self, p1: int, p2: int, img, draw: bool = True):
        if not self.lm_list:
            return 0, img, None
        x1, y1 = self.lm_list[p1][1:]
        x2, y2 = self.lm_list[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)
        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            for pt in [(x1, y1), (x2, y2), (cx, cy)]:
                cv2.circle(img, pt, 10, (255, 0, 255), cv2.FILLED)
        return length, img, [x1, y1, x2, y2, cx, cy]
