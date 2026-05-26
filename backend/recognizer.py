# backend/recognizer.py
import numpy as np
from dataclasses import dataclass


def hz_to_mel(f_hz: np.ndarray) -> np.ndarray:
    return 2595.0 * np.log10(1.0 + f_hz / 700.0)


def mel_to_hz(m: np.ndarray) -> np.ndarray:
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)


def mel_filterbank(sr: int, n_fft: int, n_mels: int, fmin: float, fmax: float) -> np.ndarray:
    n_freqs = n_fft // 2 + 1
    fmax = min(float(fmax), sr / 2.0)

    m_min = hz_to_mel(np.array([fmin], dtype=np.float64))[0]
    m_max = hz_to_mel(np.array([fmax], dtype=np.float64))[0]
    m_points = np.linspace(m_min, m_max, n_mels + 2, dtype=np.float64)
    f_points = mel_to_hz(m_points)

    bins = np.floor((n_fft + 1) * f_points / sr).astype(int)
    bins = np.clip(bins, 0, n_freqs - 1)

    fb = np.zeros((n_mels, n_freqs), dtype=np.float32)
    for i in range(n_mels):
        left, center, right = bins[i], bins[i + 1], bins[i + 2]
        if center <= left:
            center = min(left + 1, n_freqs - 1)
        if right <= center:
            right = min(center + 1, n_freqs - 1)
        if center > left:
            fb[i, left:center] = (np.arange(left, center) - left) / (center - left)
        if right > center:
            fb[i, center:right] = (right - np.arange(center, right)) / (right - center)
    return fb


def dct_matrix(n_mfcc: int, n_mels: int) -> np.ndarray:
    n = np.arange(n_mels, dtype=np.float64)
    k = np.arange(n_mfcc, dtype=np.float64)[:, None]
    return np.cos(np.pi / n_mels * (n + 0.5) * k).astype(np.float32)


def peak_normalize(x: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(x))
    if peak > 1e-6:
        return x / peak
    return x


def center_on_onset(x: np.ndarray, sr: int, window_s: float = 0.5) -> np.ndarray:
    n = int(window_s * sr)
    if len(x) <= n:
        pad = n - len(x)
        return np.pad(x, (0, pad), mode="constant")
    energy = np.abs(x)
    peak_idx = int(np.argmax(energy))
    half = n // 2
    start = max(0, peak_idx - half)
    end = start + n
    if end > len(x):
        end = len(x)
        start = end - n
    return x[start:end]


def compute_rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2)))


@dataclass
class MFCCConfig:
    sr: int
    nfft: int = 1024
    hop: int = 256
    n_mels: int = 40
    n_mfcc: int = 13
    fmin: float = 20.0
    fmax: float = 20000.0
    normalize: bool = True
    onset_center: bool = True
    onset_window_s: float = 0.5


class MFCCExtractor:
    def __init__(self, cfg: MFCCConfig):
        self.cfg = cfg
        self.window = np.hanning(cfg.nfft).astype(np.float32)
        self.mel_fb = mel_filterbank(
            sr=cfg.sr, n_fft=cfg.nfft, n_mels=cfg.n_mels,
            fmin=cfg.fmin, fmax=min(cfg.fmax, cfg.sr / 2),
        )
        self.dct = dct_matrix(cfg.n_mfcc, cfg.n_mels)

    def mfcc_frames(self, x: np.ndarray) -> np.ndarray:
        nfft = self.cfg.nfft
        hop = self.cfg.hop
        if x.size < nfft:
            x = np.pad(x, (0, nfft - x.size), mode="constant")

        n_frames = 1 + (x.size - nfft) // hop if x.size >= nfft else 1
        if n_frames <= 0:
            n_frames = 1

        mfcc_list = []
        for i in range(n_frames):
            start = i * hop
            frame = x[start:start + nfft]
            if frame.size < nfft:
                frame = np.pad(frame, (0, nfft - frame.size), mode="constant")
            frame = frame * self.window
            X = np.fft.rfft(frame)
            power = (np.abs(X) ** 2).astype(np.float32)
            power = np.nan_to_num(power, nan=0.0, posinf=1e10, neginf=0.0)
            power = np.clip(power, 0.0, 1e10)
            mel_energy = self.mel_fb @ power
            mel_energy = np.maximum(mel_energy, 1e-12)
            log_mel = np.log(mel_energy).astype(np.float32)
            mfcc = (self.dct @ log_mel).astype(np.float32)
            mfcc_list.append(mfcc)
        return np.stack(mfcc_list, axis=0)

    def features(self, x: np.ndarray) -> np.ndarray:
        if self.cfg.onset_center:
            x = center_on_onset(x, self.cfg.sr, window_s=self.cfg.onset_window_s)
        if self.cfg.normalize:
            x = peak_normalize(x)
        m = self.mfcc_frames(x)
        delta = np.diff(m, axis=0, prepend=m[:1])
        mu_m, sd_m = m.mean(axis=0), m.std(axis=0)
        mu_d, sd_d = delta.mean(axis=0), delta.std(axis=0)
        return np.concatenate([mu_m, sd_m, mu_d, sd_d], axis=0).astype(np.float32)