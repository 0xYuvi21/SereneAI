import os
import numpy as np
import torch
import torch.nn as nn
import cv2
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights

# ======================
# LOAD MODEL
# ======================
DEVICE = torch.device("cpu")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "emotion_resnet18_finetuned.pth")

model = resnet18(weights=ResNet18_Weights.DEFAULT)
model.fc = nn.Linear(model.fc.in_features, 7)

model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()

# ======================
# LABELS
# ======================
emotion_labels = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]

# ======================
# TRANSFORM
# ======================
transform = transforms.Compose(
    [
        transforms.ToPILImage(),
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)

# ======================
# FACE DETECTOR
# ======================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# ======================
# INFERENCE FUNCTION
# ======================
def predict_emotion_from_bytes(image_bytes: bytes) -> str:
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return "None"

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) == 0:
            return "None"

        x, y, w, h = faces[0]
        face = frame[y : y + h, x : x + w]

        input_tensor = transform(face).unsqueeze(0)

        with torch.inference_mode():
            outputs = model(input_tensor)
            _, pred = torch.max(outputs, 1)

        return emotion_labels[pred.item()]
    except Exception as e:
        print(f"Error predicting emotion: {e}")
        return "None"


# ======================
# WEBCAM
# ======================
def run_webcam():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    print("Camera opened:", cap.isOpened())

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Failed to grab frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        # If no face
        if len(faces) == 0:
            cv2.putText(
                frame,
                "No face detected",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )

        for x, y, w, h in faces:
            face = frame[y : y + h, x : x + w]

            input_tensor = transform(face).unsqueeze(0)

            with torch.inference_mode():
                outputs = model(input_tensor)
                _, pred = torch.max(outputs, 1)

            emotion = emotion_labels[pred.item()]

            # Draw box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Draw label
            cv2.putText(
                frame,
                emotion,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )

        cv2.imshow("Emotion Detector", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_webcam()
