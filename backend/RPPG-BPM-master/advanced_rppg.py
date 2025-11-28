#!/usr/bin/env python3
"""
Advanced rPPG Heart Rate Analyzer
개선된 비디오 기반 심박수 분석 도구
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, filtfilt
from scipy import signal as sp_signal
from scipy.ndimage import gaussian_filter1d
import cv2
from typing import Tuple, Optional, List


class AdvancedRPPGAnalyzer:
    def __init__(self, fps: int = 30):
        self.fps = fps
        self.sample_rate = fps
    
    def extract_rppg_from_rgb(self, rgb_signals: List[List[float]]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """RGB 신호에서 rPPG 신호 추출"""
        if len(rgb_signals) < self.fps:
            print(f"  신호가 너무 짧습니다 (최소 {self.fps}개 필요, 현재 {len(rgb_signals)}개)")
            return None, None
        
        # CHROM과 POS 알고리즘 시도
        rppg_chrom = self.apply_improved_chrom(rgb_signals, self.fps)
        rppg_pos = self.apply_improved_pos(rgb_signals, self.fps)
        
        # 더 나은 신호 선택
        if rppg_chrom is not None and rppg_pos is not None:
            # 신호 품질 평가 (SNR 기반)
            snr_chrom = self.calculate_snr(rppg_chrom)
            snr_pos = self.calculate_snr(rppg_pos)
            
            if snr_chrom > snr_pos:
                rppg_signal = rppg_chrom
                algorithm_used = "CHROM"
            else:
                rppg_signal = rppg_pos
                algorithm_used = "POS"
        elif rppg_chrom is not None:
            rppg_signal = rppg_chrom
            algorithm_used = "CHROM"
        elif rppg_pos is not None:
            rppg_signal = rppg_pos
            algorithm_used = "POS"
        else:
            print(f"  두 알고리즘 모두 실패")
            return None, None
        
        print(f"  사용된 알고리즘: {algorithm_used}")
        print(f"  추출된 신호 길이: {len(rppg_signal)}개 샘플")
        
        # 시간 축 생성
        duration = len(rgb_signals) / self.fps
        t = np.linspace(0, duration, len(rppg_signal))
        
        return rppg_signal, t
    
    def apply_improved_chrom(self, rgb_signals, fps):
        """개선된 CHROM 알고리즘"""
        if len(rgb_signals) < fps:
            return None
        
        rgb_array = np.array(rgb_signals)
        
        # 정규화 (분모가 0이 되지 않도록 보호)
        rgb_mean = np.mean(rgb_array, axis=0)
        rgb_mean = np.where(rgb_mean == 0, 1e-6, rgb_mean)
        rgb_norm = rgb_array / rgb_mean
        
        # 크로미넌스 신호 생성
        X = 3 * rgb_norm[:, 0] - 2 * rgb_norm[:, 1]  # 3R - 2G
        Y = 1.5 * rgb_norm[:, 0] + rgb_norm[:, 1] - 1.5 * rgb_norm[:, 2]  # 1.5R + G - 1.5B
        
        # 슬라이딩 윈도우 기반 처리
        window_duration = 2.0  # 2초 윈도우
        window_size = int(window_duration * fps)
        step_size = window_size // 4  # 75% 오버랩
        
        chrom_signals = []
        
        for i in range(0, len(X) - window_size + 1, step_size):
            x_window = X[i:i + window_size]
            y_window = Y[i:i + window_size]
            
            # 윈도우 내 디트렌딩
            x_detrend = sp_signal.detrend(x_window)
            y_detrend = sp_signal.detrend(y_window)
            
            # 적응적 가중치
            std_x = np.std(x_detrend)
            std_y = np.std(y_detrend)
            
            if std_x > 1e-6 and std_y > 1e-6:
                alpha = std_x / std_y
                alpha = np.clip(alpha, 0.1, 10.0)  # alpha 값 제한
                
                chrom_signal = x_detrend - alpha * y_detrend
                chrom_signals.extend(chrom_signal)
        
        if len(chrom_signals) == 0:
            return None
        
        rppg_signal = np.array(chrom_signals)
        
        # 후처리
        rppg_signal = self.enhanced_postprocess(rppg_signal, fps)
        
        return rppg_signal
    
    def apply_improved_pos(self, rgb_signals, fps):
        """개선된 POS 알고리즘"""
        if len(rgb_signals) < fps:
            return None
        
        rgb_array = np.array(rgb_signals)
        
        # 정규화
        rgb_mean = np.mean(rgb_array, axis=0)
        rgb_mean = np.where(rgb_mean == 0, 1e-6, rgb_mean)
        rgb_norm = rgb_array / rgb_mean
        
        # 슬라이딩 윈도우 처리
        window_duration = 2.0
        window_size = int(window_duration * fps)
        step_size = window_size // 4
        
        pos_signals = []
        
        for i in range(0, len(rgb_norm) - window_size + 1, step_size):
            window = rgb_norm[i:i + window_size]
            
            # 윈도우 내 평균 제거
            window_centered = window - np.mean(window, axis=0)
            
            # POS 투영 행렬
            S1 = window_centered[:, 0] - window_centered[:, 1]  # R - G
            S2 = window_centered[:, 0] + window_centered[:, 1] - 2 * window_centered[:, 2]  # R + G - 2B
            
            # 표준편차 기반 가중치
            std_s1 = np.std(S1)
            std_s2 = np.std(S2)
            
            if std_s1 > 1e-6 and std_s2 > 1e-6:
                alpha = std_s1 / std_s2
                alpha = np.clip(alpha, 0.1, 10.0)
                
                pos_signal = S1 - alpha * S2
                pos_signals.extend(pos_signal)
        
        if len(pos_signals) == 0:
            return None
        
        rppg_signal = np.array(pos_signals)
        
        # 후처리
        rppg_signal = self.enhanced_postprocess(rppg_signal, fps)
        
        return rppg_signal
    
    def enhanced_postprocess(self, signal, fps):
        """향상된 신호 후처리"""
        if len(signal) == 0:
            return signal
        
        # 1. 디트렌딩
        signal_detrend = sp_signal.detrend(signal)
        
        # 2. 대역통과 필터 (0.7-4.0 Hz, 42-240 BPM)
        nyquist = fps / 2.0
        low = 0.7 / nyquist
        high = 4.0 / nyquist
        
        # 경계값 체크
        if high >= 1.0:
            high = 0.99
        if low <= 0:
            low = 0.01
        
        try:
            b, a = butter(4, [low, high], btype='band')
            signal_filtered = filtfilt(b, a, signal_detrend)
        except:
            # 필터링 실패 시 원본 신호 사용
            signal_filtered = signal_detrend
        
        # 3. 가우시안 스무딩
        sigma = fps * 0.1  # 0.1초 상당
        signal_smooth = gaussian_filter1d(signal_filtered, sigma=sigma)
        
        return signal_smooth
    
    def calculate_snr(self, signal):
        """신호 대 잡음비 계산"""
        if len(signal) == 0:
            return 0
        
        # 주파수 도메인에서 SNR 계산
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/self.fps)
        
        # 심박수 범위 (0.7-4.0 Hz)
        heart_rate_mask = (freqs >= 0.7) & (freqs <= 4.0)
        
        if not np.any(heart_rate_mask):
            return 0
        
        signal_power = np.mean(np.abs(fft[heart_rate_mask])**2)
        noise_power = np.mean(np.abs(fft[~heart_rate_mask])**2)
        
        if noise_power == 0:
            return float('inf')
        
        snr = signal_power / noise_power
        return snr
    
    def calculate_bpm_metrics(self, rppg_signal, time_axis):
        """BPM 메트릭 계산"""
        if rppg_signal is None or len(rppg_signal) == 0:
            return {
                'fft_bpm': 0,
                'peak_bpm': 0,
                'time_bpms': [],
                'peaks': []
            }
        
        # FFT 기반 BPM
        fft_bpm = self.calculate_fft_bpm(rppg_signal)
        
        # 피크 기반 BPM
        peak_bpm, peaks = self.calculate_peak_bpm(rppg_signal, time_axis)
        
        # 시간별 BPM (윈도우 기반)
        time_bpms = self.calculate_windowed_bpm(rppg_signal)
        
        return {
            'fft_bpm': fft_bpm,
            'peak_bpm': peak_bpm,
            'time_bpms': time_bpms,
            'peaks': peaks
        }
    
    def calculate_fft_bpm(self, signal):
        """FFT 기반 BPM 계산"""
        # FFT 계산
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/self.fps)
        
        # 양의 주파수만 사용
        positive_freqs = freqs[:len(freqs)//2]
        positive_fft = np.abs(fft[:len(fft)//2])
        
        # 심박수 범위 필터링 (0.7-4.0 Hz, 42-240 BPM)
        heart_rate_mask = (positive_freqs >= 0.7) & (positive_freqs <= 4.0)
        
        if not np.any(heart_rate_mask):
            return 0
        
        # 최대 파워를 가진 주파수 찾기
        hr_freqs = positive_freqs[heart_rate_mask]
        hr_fft = positive_fft[heart_rate_mask]
        
        peak_freq = hr_freqs[np.argmax(hr_fft)]
        bpm = peak_freq * 60
        
        return bpm
    
    def calculate_peak_bpm(self, signal, time_axis):
        """피크 기반 BPM 계산"""
        if len(signal) < self.fps:
            return 0, []
        
        # 피크 검출
        height = np.std(signal) * 0.3  # 동적 임계값
        distance = int(self.fps * 0.4)  # 최소 0.4초 간격 (150 BPM 제한)
        
        peaks, _ = find_peaks(signal, height=height, distance=distance)
        
        if len(peaks) < 2:
            return 0, peaks
        
        # 피크 간 간격을 이용한 BPM 계산
        peak_intervals = np.diff(peaks) / self.fps  # 초 단위
        
        # 이상치 제거 (0.4-1.4초 범위, 43-150 BPM)
        valid_intervals = peak_intervals[(peak_intervals >= 0.4) & (peak_intervals <= 1.4)]
        
        if len(valid_intervals) == 0:
            return 0, peaks
        
        avg_interval = np.mean(valid_intervals)
        bpm = 60 / avg_interval
        
        return bpm, peaks
    
    def calculate_windowed_bpm(self, signal):
        """윈도우 기반 시간별 BPM 계산"""
        window_size = int(5 * self.fps)  # 5초 윈도우 (정수 변환)
        step_size = int(self.fps)  # 1초씩 이동 (정수 변환)
        
        time_bpms = []
        
        for start in range(0, len(signal) - window_size + 1, step_size):
            window = signal[start:start + window_size]
            bpm = self.calculate_fft_bpm(window)
            
            # 이상치 필터링
            if 40 <= bpm <= 180:
                time_bpms.append(bpm)
        
        return time_bpms


def advanced_analyze_and_plot(
    rgb_csv_path: str,
    blink_csv_path: str,
    bpm_img_path: str,
    blink_img_path: str,
    fps: int = 15,
) -> Tuple[str, str, Tuple[List[float], List[float]], Tuple[List[float], List[float]]]:
    """개선된 분석 및 시각화 함수 - 기존 인터페이스 유지
    Returns:
        (bpm_img_path, blink_img_path, bpm_data, blink_data)
    """
    
    # 스타일 설정
    import matplotlib as mpl
    mpl.rcParams['font.family'] = 'DejaVu Sans'
    mpl.rcParams['axes.edgecolor'] = '#DDDDDD'
    mpl.rcParams['axes.linewidth'] = 0.8
    mpl.rcParams['axes.titlesize'] = 16
    mpl.rcParams['axes.labelsize'] = 13

    # 데이터 로드
    BGR_data = np.loadtxt(rgb_csv_path, delimiter="\t")
    if BGR_data.ndim == 1:
        BGR_data = BGR_data.reshape(1, -1)

    # BGR → RGB로 변환
    rgb_data = BGR_data[:, [2, 1, 0]]  # B,G,R → R,G,B
    
    blink_data = np.loadtxt(blink_csv_path, delimiter="\t")
    if blink_data.ndim:
        blink_data = blink_data.flatten()

    # 첫 21 프레임 제거(초기값 안정화)
    rgb_trim = rgb_data[21:]
    blink_trim = blink_data[21:]

    # 새로운 고급 rPPG 분석기 사용
    analyzer = AdvancedRPPGAnalyzer(fps=fps)
    
    # RGB 신호에서 rPPG 신호 추출
    rppg_signal, time_axis = analyzer.extract_rppg_from_rgb(rgb_trim.tolist())
    
    if rppg_signal is None:
        print("rPPG 신호 추출 실패 - 기존 방법 사용")
        # 기존 방법으로 폴백
        from first_stage.pos import pos
        signal_pos = pos(rgb_trim, fps, 20)
        rppg_signal = signal_pos
        time_axis = np.linspace(0, len(rppg_signal)/fps, len(rppg_signal))
    
    # BPM 메트릭 계산
    bpm_metrics = analyzer.calculate_bpm_metrics(rppg_signal, time_axis)
    
    print(f"새로운 rPPG 분석 결과:")
    print(f"  FFT BPM: {bpm_metrics['fft_bpm']:.2f}")
    print(f"  Peak BPM: {bpm_metrics['peak_bpm']:.2f}")

    # BPM 시계열 생성 (실제 시간 축 계산)
    if len(bpm_metrics['time_bpms']) > 0:
        bpm_per_second = bpm_metrics['time_bpms']
        # 윈도우 기반으로 1초마다 계산되므로, 실제 시간 축 생성
        video_duration = len(rgb_data) / fps
        time_step = video_duration / len(bpm_per_second) if len(bpm_per_second) > 0 else 1
        time_bpm = [i * time_step for i in range(len(bpm_per_second))]
    else:
        # 폴백: 윈도우 기반 계산
        bpm_per_second = []
        time_bpm = []
        window_size = int(5 * fps)  # 5초 윈도우
        step_size = int(fps)        # 1초 간격
        
        for start in range(0, len(rppg_signal) - window_size, step_size):  # 1초씩 이동
            window = rppg_signal[start : start + window_size]
            bpm = analyzer.calculate_fft_bpm(window)
            if 40 <= bpm <= 180:  # 이상치 제거
                bpm_per_second.append(bpm)
                time_bpm.append(start / fps)  # 정확한 시간 계산 (정수 나눗셈 → 실수 나눗셈)

    # BPM 그래프 생성
    plt.figure(figsize=(12, 5), dpi=120)
    if len(time_bpm) > 0:
        plt.plot(time_bpm, bpm_per_second, color='#007AFF', linewidth=2.2, label='Heart Rate', alpha=0.9)
    plt.axhspan(60, 100, color='lightgreen', alpha=0.2, label='Normal range')
    
    # 스타일 및 x축 설정
    # 제목 및 축 라벨 제거
    plt.title("")
    plt.xlabel("")
    plt.ylabel("")
    
    # 실제 영상 길이에 맞게 x축 설정
    if len(time_bpm) > 0:
        video_duration = len(rgb_data) / fps  # 실제 영상 길이 (초)
        
        # x축 범위를 영상 길이로 제한
        plt.xlim(0, video_duration)
        
        # x축 틱을 적절히 설정 (5초 간격 또는 적절한 간격)
        tick_interval = max(1, int(video_duration / 8))  # 최대 8개 정도의 틱
        ticks = list(range(0, int(video_duration) + 1, tick_interval))
        if int(video_duration) not in ticks:  # 마지막 시간점 추가
            ticks.append(int(video_duration))
        plt.xticks(ticks)
    
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.legend(loc='upper right', frameon=False)
    plt.tight_layout()
    plt.savefig(bpm_img_path, dpi=300)
    plt.close()

    # 눈 깜빡임 그래프 (기존 방식 유지)
    blink_counts, time_blink = [], []
    blink_step = int(fps)  # 1초 간격 (정수)
    
    for start in range(0, len(blink_trim), blink_step):
        window_end = start + blink_step
        if window_end > len(blink_trim):
            break
            
        window = blink_trim[start : window_end]
        blink_counts.append(np.sum(window))
        time_blink.append(start / fps)  # 정확한 시간 계산

    plt.figure(figsize=(12, 5), dpi=120)
    plt.plot(time_blink, blink_counts, color='#34C759', linewidth=2.2, label='Blink Rate', alpha=0.9)
    
    # 평균 blink rate 라인 추가
    if len(blink_counts) > 0:
        avg_blink = np.mean(blink_counts)
        plt.axhline(y=avg_blink, color='gray', linestyle='--', linewidth=1.4, label='Average')
    
    # 스타일 및 x축 설정
    # 제목 및 축 라벨 제거
    plt.title("")
    plt.xlabel("")
    plt.ylabel("")
    
    # 실제 영상 길이에 맞게 x축 설정
    if len(time_blink) > 0:
        video_duration = len(blink_trim) / fps  # 실제 영상 길이 (초)
        
        # x축 범위를 영상 길이로 제한
        plt.xlim(0, video_duration)
        
        # x축 틱을 적절히 설정
        tick_interval = max(1, int(video_duration / 8))  # 최대 8개 정도의 틱
        ticks = list(range(0, int(video_duration) + 1, tick_interval))
        if int(video_duration) not in ticks:  # 마지막 시간점 추가
            ticks.append(int(video_duration))
        plt.xticks(ticks)
    
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.legend(loc='upper right', frameon=False)
    plt.tight_layout()
    plt.savefig(blink_img_path, dpi=300)
    plt.close()

    return bpm_img_path, blink_img_path, (time_bpm, bpm_per_second), (time_blink, blink_counts)
