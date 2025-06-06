from scipy.signal import periodogram
import numpy as np

# 푸리에 분석(Fourier Analysis)
def fourier_analysis(ppg_signal, fps):
    
    def find_idx_bigger(arr, thr):
        return next(f[0] for f in enumerate(arr) if f[1] > thr)
    
    MinFreq = 45   # 최소 심박수 (bpm)
    MaxFreq = 100  # 최대 심박수 (bpm)
    freqs, psd = periodogram(ppg_signal, fs=fps, window=None, detrend='constant', return_onesided=True, scaling='density')
    min_idx = find_idx_bigger(freqs, MinFreq/60.0) - 1
    max_idx = find_idx_bigger(freqs, MaxFreq/60.0) + 1
    hr_estimated = freqs[ min_idx + np.argmax(psd[min_idx : max_idx]) ]
    
    return hr_estimated
