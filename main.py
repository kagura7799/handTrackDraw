import cv2
import numpy as np
import dearpygui.dearpygui as dpg
import time
import os

from hand_tracking_module import HandDetector

WIN_W, WIN_H = 1280, 780
CAM_W, CAM_H = 640, 480
BRUSH  = 18
ERASER = 80
MODEL_PATH = "hand_landmarker.task"

COLORS = {
    "Purple": {"bgr": (255,   0, 255), "rgba": (255,   0, 255, 255)},
    "Blue":   {"bgr": (255,   0,   0), "rgba": ( 50, 100, 255, 255)},
    "Green":  {"bgr": (  0, 255,   0), "rgba": (  0, 200,  50, 255)},
    "Eraser": {"bgr": (  0,   0,   0), "rgba": ( 90,  90,  90, 255)},
}
COLOR_KEYS = list(COLORS.keys())


def frame_to_dpg(frame_bgr: np.ndarray) -> np.ndarray:
    rgba = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGBA)
    return rgba.flatten().astype(np.float32) / 255.0


def find_cyrillic_font() -> str | None:
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def load_overlays(folder: str, w: int, h: int) -> list:
    result = []
    if not os.path.isdir(folder):
        return result
    for fname in sorted(os.listdir(folder)):
        if fname.lower().endswith((".jpg", ".png")):
            img = cv2.imread(os.path.join(folder, fname))
            if img is not None:
                result.append(cv2.resize(img, (w, h)))
    return result


class App:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

        self.detector      = HandDetector(MODEL_PATH, max_hands=1)
        self.timestamp_ms  = 0
        self.canvas        = np.zeros((CAM_H, CAM_W, 3), dtype=np.uint8)
        self.draw_color    = COLORS["Purple"]["bgr"]
        self.xp, self.yp   = 0, 0

        self.header_h = CAM_H // 7
        self.overlays = load_overlays("Header", CAM_W, self.header_h)
        self.header   = self.overlays[0] if self.overlays else None

        self.status = "Ready — draw!"
        self._t     = time.time()

        self._build_ui()

    def _cb_set_purple(self, s, a, u): self._set_color("Purple")
    def _cb_set_blue  (self, s, a, u): self._set_color("Blue")
    def _cb_set_green (self, s, a, u): self._set_color("Green")
    def _cb_set_eraser(self, s, a, u): self._set_color("Eraser")
    def _cb_clear     (self, s, a, u): self._clear()

    def _set_color(self, key: str):
        self.draw_color = COLORS[key]["bgr"]
        self.status = f"Color: {key}"

    def _clear(self):
        self.canvas[:] = 0
        self.status = "Canvas cleared"

    def _build_ui(self):
        dpg.create_context()

        font_path = find_cyrillic_font()
        if font_path:
            with dpg.font_registry():
                fnt = dpg.add_font(font_path, 16, tag="main_font")
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=fnt)

        dpg.create_viewport(title="Virtual Painter",
                            width=WIN_W, height=WIN_H, resizable=False)
        dpg.setup_dearpygui()

        if font_path:
            dpg.bind_font("main_font")

        blank = np.zeros((CAM_H, CAM_W, 4), dtype=np.float32)
        with dpg.texture_registry():
            dpg.add_raw_texture(
                width=CAM_W, height=CAM_H,
                default_value=blank.flatten().tolist(),
                format=dpg.mvFormat_Float_rgba,
                tag="cam_tex",
            )

        with dpg.window(tag="main_win", no_title_bar=True, no_resize=True,
                        no_move=True, no_scrollbar=True,
                        width=WIN_W, height=WIN_H):

            dpg.add_image("cam_tex", width=CAM_W, height=CAM_H)
            dpg.add_spacer(height=6)

            with dpg.group(horizontal=True):
                self.status_tag = dpg.add_text(self.status, color=(180, 255, 180))
                dpg.add_spacer(width=40)
                self.fps_tag = dpg.add_text("FPS: --", color=(255, 220, 100))

            dpg.add_spacer(height=8)
            dpg.add_text("Brush color:")
            dpg.add_spacer(height=4)

            callbacks = [
                ("Purple", self._cb_set_purple),
                ("Blue",   self._cb_set_blue),
                ("Green",  self._cb_set_green),
                ("Eraser", self._cb_set_eraser),
            ]
            with dpg.group(horizontal=True):
                for key, cb in callbacks:
                    c = COLORS[key]["rgba"]
                    
                    with dpg.theme() as btn_theme:
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Button,        c)
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,
                                                tuple(min(v+30,255) for v in c))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,
                                                tuple(max(v-30,0)   for v in c))
                            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
                    btn = dpg.add_button(label=f"  {key}  ",
                                         callback=cb,
                                         width=130, height=38)
                    dpg.bind_item_theme(btn, btn_theme)
                    dpg.add_spacer(width=6)

            dpg.add_spacer(height=8)

            with dpg.theme() as clear_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button,        (200, 50, 50, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (230, 80, 80, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  (160, 30, 30, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_Text,          (255,255,255,255))
            clear_btn = dpg.add_button(label="  Clear canvas  ",
                                        callback=self._cb_clear,
                                        width=160, height=38)
            dpg.bind_item_theme(clear_btn, clear_theme)

            dpg.add_spacer(height=8)
            dpg.add_separator()
            dpg.add_text(
                "Gestures: [1 finger] draw  |  [2 fingers] pick color  |  [5 fingers] clear",
                color=(150, 150, 150),
            )

        dpg.show_viewport()
        dpg.set_primary_window("main_win", True)

    def _process_frame(self):
        ok, img = self.cap.read()
        if not ok:
            return None

        img = cv2.flip(img, 1)
        self.timestamp_ms += 1
        img = self.detector.find_hands(img, draw=True, timestamp_ms=self.timestamp_ms)
        lm  = self.detector.lm_list

        if lm:
            x1, y1  = lm[8][1],  lm[8][2]
            x2, y2  = lm[12][1], lm[12][2]
            fingers = self.detector.fingers_up()

            if fingers[1] and fingers[2]:
                self.xp, self.yp = 0, 0
                if y1 < self.header_h and self.overlays:
                    zone = CAM_W // len(self.overlays)
                    idx  = min(x1 // zone, len(self.overlays) - 1)
                    self.header     = self.overlays[idx]
                    key             = COLOR_KEYS[idx]
                    self.draw_color = COLORS[key]["bgr"]
                    self.status     = f"Color: {key}"
                cv2.rectangle(img, (x1, y1-20), (x2, y2+20), self.draw_color, cv2.FILLED)

            elif fingers[1] and not fingers[2]:        
                cv2.circle(img, (x1, y1), 12, self.draw_color, cv2.FILLED)
                if self.xp == 0 and self.yp == 0:
                    self.xp, self.yp = x1, y1
                thick = ERASER if self.draw_color == (0, 0, 0) else BRUSH
                cv2.line(self.canvas, (self.xp, self.yp), (x1, y1), self.draw_color, thick)
                self.xp, self.yp = x1, y1

            elif sum(fingers) == 5:                   
                self._clear()

            else:
                self.xp, self.yp = 0, 0
        else:
            self.xp, self.yp = 0, 0

        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, inv = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        inv = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, inv)
        img = cv2.bitwise_or(img, self.canvas)

        if self.header is not None:
            img[0:self.header_h, 0:CAM_W] = self.header

        return img

    def run(self):
        while dpg.is_dearpygui_running():
            frame = self._process_frame()
            if frame is not None:
                dpg.set_value("cam_tex", frame_to_dpg(frame))

            now = time.time()
            fps = 1.0 / max(now - self._t, 1e-6)
            self._t = now

            dpg.set_value(self.status_tag, self.status)
            dpg.set_value(self.fps_tag,    f"FPS: {fps:.1f}")

            dpg.render_dearpygui_frame()

        self.cap.release()
        dpg.destroy_context()


if __name__ == "__main__":
    App().run()
