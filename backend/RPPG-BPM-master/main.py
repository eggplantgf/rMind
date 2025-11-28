import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.interpolate import interp1d
from typing import Tuple, List


# RPPG-BPM 모듈 경로 추가
CUR_DIR = os.path.dirname(__file__)
sys.path.append(CUR_DIR)

# 새로운 고급 rPPG 분석기 import
from advanced_rppg import advanced_analyze_and_plot

# 기존 모듈들 (폴백용)
from first_stage.chrom import chrom
from first_stage.pos import pos
from first_stage.ica import ica
from second_stage.fourier_analysis import fourier_analysis
from second_stage.interbeats_analysis import interbeats_analysis
from second_stage.wavelet_analysis import wavelet_analysis


def analyze_and_plot(
    rgb_csv_path: str,
    blink_csv_path: str,
    bpm_img_path: str,
    blink_img_path: str,
    fps: int = 15,
) -> Tuple[str, str, Tuple[List[float], List[float]], Tuple[List[float], List[float]]]:
    """
    개선된 rPPG 분석 함수
    새로운 고급 알고리즘을 먼저 시도하고, 실패 시 기존 방법으로 폴백
    Returns:
        (bpm_img_path, blink_img_path, bpm_data, blink_data)
        bpm_data: (time_axis, bpm_values)
        blink_data: (time_axis, blink_values)
    """
    
    print(f"🔄 rPPG 분석 시작 (고급 알고리즘 우선)")
    
    try:
        # 새로운 고급 rPPG 분석기 시도
        # advanced_analyze_and_plot도 데이터를 반환하도록 수정되었다고 가정
        result = advanced_analyze_and_plot(
            rgb_csv_path, blink_csv_path, bpm_img_path, blink_img_path, fps
        )
        print(f"고급 rPPG 분석 성공")
        return result
        
    except Exception as e:
        print(f"고급 rPPG 분석 실패: {e}")
        print(f"기존 방법으로 폴백...")
        
        # 기존 방법으로 폴백
        return _legacy_analyze_and_plot(
            rgb_csv_path, blink_csv_path, bpm_img_path, blink_img_path, fps
        )


def _legacy_analyze_and_plot(
    rgb_csv_path: str,
    blink_csv_path: str,
    bpm_img_path: str,
    blink_img_path: str,
    fps: int = 15,
) -> Tuple[str, str, Tuple[List[float], List[float]], Tuple[List[float], List[float]]]:
    """
    기존 rPPG 분석 방법 (폴백용)
    """
    
    # 스타일 설정
    mpl.rcParams['font.family'] = 'DejaVu Sans'
    mpl.rcParams['axes.edgecolor'] = '#DDDDDD'
    mpl.rcParams['axes.linewidth'] = 0.8
    mpl.rcParams['axes.titlesize'] = 16
    mpl.rcParams['axes.labelsize'] = 13

    # 데이터 로드
    BGR_data = np.loadtxt(rgb_csv_path, delimiter="\t")
    if BGR_data.ndim == 1:
        BGR_data = BGR_data.reshape(1, -1)

    # BGR → R,G,B 로 맞추기
    R = BGR_data[:, 0:1]
    G = BGR_data[:, 1:2]
    B = BGR_data[:, 2:3]

    blink_data = np.loadtxt(blink_csv_path, delimiter="\t")
    if blink_data.ndim:
        blink_data = blink_data.flatten()

    # 첫 21 프레임 제거(초기값 안정화) 나중에 제거.
    BGR_trim = BGR_data[21:]
    blink_trim = blink_data[21:]

    #신호 생성
    signal_chrom = chrom(BGR_trim, fps, 32)
    signal_pos = pos(BGR_trim, fps, 20)
    signal_ica = ica(BGR_trim, fps)

    # BPM 계산(Fourier, Wavelet, Interbeat 바꾸면서)
    hr_fourier_pos = fourier_analysis(signal_pos, fps) * 60
    print(f"Legacy POS + Fourier BPM : {hr_fourier_pos:.2f}")

    # BPM 시계열
    bpm_per_second = []
    time_bpm = []
    window_size = int(5 * fps)  # 5초 윈도우 (정수)
    step_size = int(fps)        # 1초 간격 (정수)
    
    for start in range(0, len(signal_pos) - window_size, step_size):  # 1초씩 이동
        window = signal_pos[start : start + window_size]
        bpm = fourier_analysis(window, fps) * 60
        if 40 <= bpm <= 180:  # 이상치 제거
            bpm_per_second.append(bpm)
            time_bpm.append(start / fps)  # 1초 단위

    # 그래프
    # [CODE_REVIEW] BPM 그래프 생성 위치
    # x축: time_bpm (초 단위, 21프레임 이후 기준)
    # y축: bpm_per_second (분당 심박수)
    plt.figure(figsize=(12, 5), dpi=120)
    plt.plot(time_bpm, bpm_per_second, color='#007AFF', linewidth=2.2, label='Heart Rate', alpha=0.9)
    plt.axhspan(60, 100, color='lightgreen', alpha=0.2, label='Normal range')
    
    # 스타일
    # 제목 및 축 라벨 제거
    plt.title("")
    plt.xlabel("")
    plt.ylabel("")
    if len(time_bpm) > 0:
        plt.xticks(range(0, max(time_bpm)+1, max(1, len(time_bpm)//10)))
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.legend(loc='upper right', frameon=False)
    plt.tight_layout()
    plt.savefig(bpm_img_path, dpi=300)
    plt.close()

    # 그래프
    # [CODE_REVIEW] Blink 그래프 생성 위치
    # x축: time_blink (초 단위, 21프레임 이후 기준)
    # y축: blink_counts (초당 눈깜박임 횟수)
    blink_counts, time_blink = [], []
    blink_step = int(fps)
    
    for start in range(0, len(blink_trim), blink_step):
        window_end = start + blink_step
        if window_end > len(blink_trim):
            break
            
        window = blink_trim[start : window_end]
        blink_counts.append(np.sum(window))
        time_blink.append(start / fps)  # 1초 단위

    plt.figure(figsize=(12, 5), dpi=120)
    plt.plot(time_blink, blink_counts, color='#34C759', linewidth=2.2, label='Blink Rate', alpha=0.9)
    
    # 평균 blink rate 라인 추가
    if len(blink_counts) > 0:
        avg_blink = np.mean(blink_counts)
        plt.axhline(y=avg_blink, color='gray', linestyle='--', linewidth=1.4, label='Average')
    
    # 스타일
    # 제목 및 축 라벨 제거
    plt.title("")
    plt.xlabel("")
    plt.ylabel("")
    if len(time_blink) > 0:
        plt.xticks(range(0, max(time_blink)+1, max(1, len(time_blink)//10)))
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.legend(loc='upper right', frameon=False)
    plt.tight_layout()
    plt.savefig(blink_img_path, dpi=300)
    plt.close()

    return bpm_img_path, blink_img_path, (time_bpm, bpm_per_second), (time_blink, blink_counts)


# 단독 실행 시 CLI 기능
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BPM / Blink 분석 및 시각화")
    parser.add_argument("--rgb_csv", required=True, help="RGB CSV 경로")
    parser.add_argument("--blink_csv", required=True, help="Blink CSV 경로")
    parser.add_argument("--bpm_img", default="./bpm.png", help="BPM 이미지 저장 경로")
    parser.add_argument("--blink_img", default="./blink.png", help="Blink 이미지 저장 경로")
    args = parser.parse_args()

    analyze_and_plot(args.rgb_csv, args.blink_csv, args.bpm_img, args.blink_img)
    print("그래프 저장 완료!")