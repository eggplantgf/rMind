import cv2
import dlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

VIDEO_PATH = 'test_30.mp4'
OUTPUT_PNG = 'output/motion_smooth_plot.png'
STABILITY_THRESHOLD = 50.0
SECOND_INTERVAL = 1

# 폰트 및 그래프 설정
mpl.rcParams['font.family'] = 'Segoe UI Emoji'
mpl.rcParams['axes.edgecolor'] = '#DDDDDD'
mpl.rcParams['axes.linewidth'] = 0.8
mpl.rcParams['axes.titlesize'] = 16
mpl.rcParams['axes.labelsize'] = 13

# 모델 불러오기
predictor_local = os.path.join(
    os.path.dirname(__file__),
    "../Eye_detection/shape_predictor_68_face_landmarks.dat",
)
predictor_path = predictor_local if os.path.exists(predictor_local) else (
    "shape_predictor_68_face_landmarks.dat"
)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

# 폴더 준비
os.makedirs("output", exist_ok=True)

# 랜드마크 추출 함수
def get_landmarks(gray, rect):
    shape = predictor(gray, rect)
    coords = np.zeros((68, 2), dtype="float")
    for i in range(68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords

# 영상 처리
cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps * SECOND_INTERVAL)

prev_landmarks = None
motions_per_second = []
motion_buffer = []
frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if frame_idx % frame_interval == 0:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if len(faces) > 0:
            landmarks = get_landmarks(gray, faces[0])
            if prev_landmarks is not None:
                motion = np.linalg.norm(landmarks - prev_landmarks, axis=1).mean()
                motions_per_second.append(motion)
            else:
                motions_per_second.append(0)
            prev_landmarks = landmarks
        else:
            motions_per_second.append(0)

    frame_idx += 1

cap.release()

# 시간축 데이터 만들기
x = np.arange(len(motions_per_second))  # 1초 단위

# 그래프 그리기
plt.figure(figsize=(12, 5), dpi=120)
plt.plot(x, motions_per_second, color='#FF6B6B', linewidth=2.2, label='Movement', alpha=0.9)
plt.axhline(y=STABILITY_THRESHOLD, color='gray', linestyle='--', linewidth=1.4, label='Threshold')

# 스타일
plt.title("📈 Motion Intensity Over Time", pad=15)
plt.xlabel("Time (seconds)")
plt.ylabel("Avg Movement Intensity")
plt.xticks(x)
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.legend(loc='upper left', prop={'size': 18, 'weight': 'bold'}, frameon=False)
plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=300)

print(f"✅ 곡선 스타일 그래프 저장 완료: {OUTPUT_PNG}")

