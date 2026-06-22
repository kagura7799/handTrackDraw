# Virtual Painter — DearPyGui (Python 3.13+)

Десктопная версия проекта рисования жестами.  
Стек: **Python 3.13+ · DearPyGui · OpenCV · MediaPipe**

---

## Структура проекта

```
handtrack_mobile/
├── main.py                  # Главное приложение (DearPyGui)
├── hand_tracking_module.py  # Детектор руки (MediaPipe Tasks)
├── hand_landmarker.task     # Модель MediaPipe (скачать — см. ниже)
```
## Установка

```bash
pip install dearpygui opencv-python mediapipe numpy
```

---

## Скачать модель MediaPipe (обязательно)

Положите файл в корень проекта рядом с `main.py`:

```bash
# Windows (PowerShell)
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "hand_landmarker.task"

# Linux / macOS
wget https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

---

## Запуск

```bash
python main.py
```

---

## Частые проблемы

| Ошибка | Решение |
|--------|---------|
| `hand_landmarker.task not found` | Скачайте модель (см. выше), положите рядом с `main.py` |
| Камера не открывается | Попробуйте изменить `cv2.VideoCapture(0)` на `cv2.VideoCapture(1)` |
| Низкий FPS | Уменьшите `CAM_W, CAM_H` в `main.py` (например до 320×240) |
| Чёрное окно | Обновите драйверы видеокарты / DirectX |
