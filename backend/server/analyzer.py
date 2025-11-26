from __future__ import annotations

import importlib.util
import sys
import os
import cv2
import dlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
from types import ModuleType
from typing import Callable

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


def _load_module(module_name: str, file_path: Path) -> ModuleType:
    # 주어진 파일 경로에서 모듈을 동적으로 로드
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"Unable to load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # 캐시에 등록
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# 1) extract_features_from_video – test_data/save_data_demo.py
# ---------------------------------------------------------------------------
save_data_path = BASE_DIR / "test_data" / "save_data_demo.py"
_save_data_mod = _load_module("_save_data", save_data_path)
extract_features_from_video: Callable = _save_data_mod.extract_features_from_video


# ---------------------------------------------------------------------------
# 2) analyze_and_plot – RPPG-BPM-master/main.py
#    하이픈(-)이 포함된 디렉터리는 파이썬 패키지로 바로 임포트할 수 없으므로
#    파일 경로 기반 동적 로딩을 사용한다.
# ---------------------------------------------------------------------------
main_path = BASE_DIR / "RPPG-BPM-master" / "main.py"
_rppg_main_mod = _load_module("_rppg_main", main_path)
analyze_and_plot: Callable = _rppg_main_mod.analyze_and_plot


# ---------------------------------------------------------------------------
# 3) analyze_motion – Motion detection functionality
# ---------------------------------------------------------------------------
def analyze_motion(
    video_path: str,
    motion_img_path: str,
    stability_threshold: float = 2.0,
    second_interval: int = 1
) -> tuple[str, list, list]:
    """
    Parameters
    ----------
    video_path : str
        분석할 영상 파일 경로
    motion_img_path : str
        저장할 움직임 그래프 이미지 경로
    stability_threshold : float
        안정성 임계값 (기본값: 2.0)
    second_interval : int
        초 단위 간격 (기본값: 1초)
    """
    # 스타일
    mpl.rcParams['font.family'] = 'DejaVu Sans'
    mpl.rcParams['axes.edgecolor'] = '#DDDDDD'
    mpl.rcParams['axes.linewidth'] = 0.8
    mpl.rcParams['axes.titlesize'] = 16
    mpl.rcParams['axes.labelsize'] = 13

    # 모델 불러오기
    predictor_local = BASE_DIR / "Eye_detection" / "shape_predictor_68_face_landmarks.dat"
    predictor_path = str(predictor_local) if predictor_local.exists() else "shape_predictor_68_face_landmarks.dat"
    
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    # 랜드마크 추출 함수
    def get_landmarks(gray, rect):
        shape = predictor(gray, rect)
        coords = np.zeros((68, 2), dtype="float")
        for i in range(68):
            coords[i] = (shape.part(i).x, shape.part(i).y)
        return coords

    # 영상 처리
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * second_interval)

    # [CODE_REVIEW] 초기 21프레임 스킵 (BPM/Blink 분석과 싱크 맞추기 위함)
    # set(cv2.CAP_PROP_POS_FRAMES, 21)을 사용하거나 루프에서 스킵
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 21)
    except:
        # set이 동작하지 않는 경우를 대비해 읽어서 버림
        for _ in range(21):
            cap.read()

    prev_landmarks = None
    motions_per_second = []
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
    # [CODE_REVIEW] Motion 그래프 생성 위치
    # x축: x (초 단위, 영상 시작(0초)부터 기준)
    # y축: motions_per_second (초당 평균 움직임 강도)
    plt.figure(figsize=(12, 5), dpi=120)
    plt.plot(x, motions_per_second, color='#FF6B6B', linewidth=2.2, label='Movement', alpha=0.9)
    plt.axhline(y=stability_threshold, color='gray', linestyle='--', linewidth=1.4, label='Threshold')

    # 스타일
    plt.title("Motion Intensity Over Time", pad=15)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Avg Movement Intensity")
    if len(x) > 0:
        plt.xticks(x[::max(1, len(x)//10)])  # 최대 10개 눈금만 표시
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.legend(loc='upper right', frameon=False)
    plt.tight_layout()
    plt.savefig(motion_img_path, dpi=300)
    plt.close()

    return motion_img_path, x, motions_per_second


def create_combined_plot(
    bpm_data: tuple[list[float], list[float]],
    blink_data: tuple[list[float], list[float]],
    motion_data: tuple[list[float], list[float]],
    combined_img_path: str
) -> str:
    """
    3가지 지표(BPM, Blink, Motion)를 하나의 그래프에 겹쳐서 그린다.
    각 지표는 0~1 사이로 정규화(Normalization)하여 스케일을 맞춘다.
    모두 동일한 회색 + 높은 투명도로 디자인한다.
    """
    
    # 데이터 언패킹
    t_bpm, y_bpm = bpm_data
    t_blink, y_blink = blink_data
    t_motion, y_motion = motion_data
    
    # 정규화 함수
    def normalize(data):
        arr = np.array(data)
        if len(arr) == 0:
            return arr
        mn, mx = np.min(arr), np.max(arr)
        if mx - mn == 0:
            return np.zeros_like(arr)
        return (arr - mn) / (mx - mn)

    norm_bpm = normalize(y_bpm)
    norm_blink = normalize(y_blink)
    norm_motion = normalize(y_motion)

    plt.figure(figsize=(12, 5), dpi=120)
    
    # Plotting
    # 회색, 투명도 높게 (alpha=0.5 정도)
    if len(t_bpm) > 0:
        plt.plot(t_bpm, norm_bpm, color='gray', alpha=0.5, linewidth=2, label='Heart Rate (Norm)')
    if len(t_blink) > 0:
        plt.plot(t_blink, norm_blink, color='gray', alpha=0.5, linewidth=2, linestyle='--', label='Blink Rate (Norm)')
    if len(t_motion) > 0:
        plt.plot(t_motion, norm_motion, color='gray', alpha=0.5, linewidth=2, linestyle=':', label='Motion (Norm)')

    plt.title("Combined Analysis (Normalized)", pad=15)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Normalized Intensity (0-1)")
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.legend(loc='upper right', frameon=False)
    plt.tight_layout()
    
    plt.savefig(combined_img_path, dpi=300)
    plt.close()
    
    return combined_img_path


__all__ = [
    "extract_features_from_video",
    "analyze_and_plot",
    "analyze_motion",
    "create_combined_plot",
] 