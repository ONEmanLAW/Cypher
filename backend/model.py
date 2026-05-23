#!/usr/bin/env python3
import os
import time
import wave
import queue
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd

from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib


# ---------------- MFCC helpers (numpy-only) ----------------

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


# ---------------- Audio utilities ----------------

def peak_normalize(x: np.ndarray) -> np.ndarray:
    """Normalise l'amplitude pour que le modèle apprenne le timbre, pas le volume."""
    peak = np.max(np.abs(x))
    if peak > 1e-6:
        return x / peak
    return x

def center_on_onset(x: np.ndarray, sr: int, window_s: float = 0.5) -> np.ndarray:
    """Centre le signal sur son pic d'énergie. Sortie de longueur fixe = window_s * sr."""
    n = int(window_s * sr)
    if len(x) <= n:
        # pad si trop court
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


# ---------------- IO WAV ----------------

def float_to_int16(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -1.0, 1.0)
    return (x * 32767.0).astype(np.int16)

def save_wav_int16(path: Path, x_float: np.ndarray, sr: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    x_i16 = float_to_int16(x_float)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(x_i16.tobytes())

def load_wav_as_float(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n_ch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"WAV non supporté (sampwidth={sampwidth}). Utilise du PCM 16-bit.")
    x = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if n_ch > 1:
        x = x.reshape(-1, n_ch)[:, 0]
    return x, sr


# ---------------- Feature extraction ----------------

@dataclass
class MFCCConfig:
    sr: int
    nfft: int = 1024
    hop: int = 256
    n_mels: int = 40
    n_mfcc: int = 13
    fmin: float = 20.0
    fmax: float = 20000.0
    # paramètres d'extraction de features
    normalize: bool = True
    onset_center: bool = True
    onset_window_s: float = 0.5

class MFCCExtractor:
    def __init__(self, cfg: MFCCConfig):
        self.cfg = cfg
        self.window = np.hanning(cfg.nfft).astype(np.float32)
        self.mel_fb = mel_filterbank(
            sr=cfg.sr,
            n_fft=cfg.nfft,
            n_mels=cfg.n_mels,
            fmin=cfg.fmin,
            fmax=min(cfg.fmax, cfg.sr / 2),
        )
        self.dct = dct_matrix(cfg.n_mfcc, cfg.n_mels)

    def mfcc_frames(self, x: np.ndarray) -> np.ndarray:
        """Retourne [T, n_mfcc]"""
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
        """
        Features fixes: mean+std de MFCC + mean+std de delta MFCC.
        Dimension = 4 * n_mfcc
        """
        # 1) Onset centering (aligne le son dans la fenêtre)
        if self.cfg.onset_center:
            x = center_on_onset(x, self.cfg.sr, window_s=self.cfg.onset_window_s)

        # 2) Peak normalization (rend le modèle invariant au volume)
        if self.cfg.normalize:
            x = peak_normalize(x)

        # 3) MFCC frames
        m = self.mfcc_frames(x)  # [T, n_mfcc]

        # 4) Delta MFCC (dynamique temporelle)
        delta = np.diff(m, axis=0, prepend=m[:1])

        mu_m = m.mean(axis=0)
        sd_m = m.std(axis=0)
        mu_d = delta.mean(axis=0)
        sd_d = delta.std(axis=0)

        return np.concatenate([mu_m, sd_m, mu_d, sd_d], axis=0).astype(np.float32)


# ---------------- App ----------------

class App(QtWidgets.QMainWindow):
    def __init__(
        self,
        dataset_dir="dataset",
        model_path="model.joblib",
        samplerate=48000,
        channels=1,
        blocksize=1024,
        wave_seconds=0.2,
        fft_size=4096,
        stft_nfft=1024,
        stft_hop=256,
        spec_seconds=5.0,
        spec_max_freq=20000,
        n_mels=40,
        n_mfcc=13,
        # Nouveaux paramètres
        confidence_threshold=0.6,
        rms_threshold=0.01,
    ):
        super().__init__()
        self.setWindowTitle("Beatbox recognizer · v2")

        self.dataset_dir = Path(dataset_dir)
        self.model_path = Path(model_path)

        self.sr = int(samplerate)
        self.channels = int(channels)
        self.blocksize = int(blocksize)

        # Nouveaux seuils
        self.confidence_threshold = float(confidence_threshold)
        self.rms_threshold = float(rms_threshold)

        # --- buffers waveform ---
        self.wave_seconds = float(wave_seconds)
        self.wave_n = max(1, int(self.sr * self.wave_seconds))
        self.wave_ring = np.zeros(self.wave_n, dtype=np.float32)
        self.wave_t = np.linspace(-self.wave_seconds, 0, self.wave_n, endpoint=False)

        # --- fft ---
        self.fft_size = max(256, int(fft_size))
        self.fft_buf = np.zeros(self.fft_size, dtype=np.float32)
        self.fft_win = np.hanning(self.fft_size).astype(np.float32)
        self.fft_freqs = np.fft.rfftfreq(self.fft_size, d=1.0 / self.sr)
        self.fft_db = np.full(self.fft_freqs.shape, -120.0, dtype=np.float32)

        # --- stft spectrogram ---
        self.stft_nfft = int(stft_nfft)
        self.stft_hop = int(stft_hop)
        self.spec_seconds = float(spec_seconds)
        self.spec_max_freq = float(spec_max_freq)

        self.stft_win = np.hanning(self.stft_nfft).astype(np.float32)
        self.stft_pending = np.zeros(0, dtype=np.float32)

        self.spec_freqs = np.fft.rfftfreq(self.stft_nfft, d=1.0 / self.sr)
        self.spec_fmask = self.spec_freqs <= min(self.spec_max_freq, self.sr / 2)
        self.spec_freqs_view = self.spec_freqs[self.spec_fmask]
        self.spec_cols = max(10, int((self.spec_seconds * self.sr) / self.stft_hop))
        self.spec_img = np.full((self.spec_freqs_view.size, self.spec_cols), -120.0, dtype=np.float32)

        # --- mfcc spectrogram ---
        self.mfcc_cfg = MFCCConfig(
            sr=self.sr,
            nfft=self.stft_nfft,
            hop=self.stft_hop,
            n_mels=int(n_mels),
            n_mfcc=int(n_mfcc),
            fmin=20.0,
            fmax=min(20000.0, self.sr / 2),
            normalize=True,
            onset_center=True,
            onset_window_s=0.5,
        )
        self.mfcc_extractor = MFCCExtractor(self.mfcc_cfg)
        self.mfcc_img = np.full((self.mfcc_cfg.n_mfcc, self.spec_cols), 0.0, dtype=np.float32)

        # --- state ---
        self.model = None
        self.last_prediction = "-"
        self.recognition_on = False

        self.recording_on = False
        self.record_label = ""
        self.record_target_n = int(self.sr * 1.0)
        self.record_buf = []

        self.recog_seconds = 1.0
        self.recog_buf_max = int(self.sr * 5.0)
        self.recog_buf = np.zeros(self.recog_buf_max, dtype=np.float32)

        self.q = queue.Queue(maxsize=500)

        # ---------------- UI ----------------
        central = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(central)

        self.fig = Figure(figsize=(11, 11), dpi=100)
        self.canvas = FigureCanvas(self.fig)

        self.ax_wave = self.fig.add_subplot(411)
        self.ax_fft = self.fig.add_subplot(412)
        self.ax_spec = self.fig.add_subplot(413)
        self.ax_mfcc = self.fig.add_subplot(414)

        # Wave
        self.ax_wave.set_xlabel("Temps (s)")
        self.ax_wave.set_ylabel("Amplitude")
        self.ax_wave.grid(True)
        (self.line_wave,) = self.ax_wave.plot(self.wave_t, self.wave_ring, linewidth=1.0)
        self.ax_wave.set_xlim(self.wave_t[0], self.wave_t[-1] if self.wave_t.size > 1 else 0.0)
        self.ax_wave.set_ylim(-1.0, 1.0)

        # FFT
        self.ax_fft.set_xlabel("Fréquence (Hz)")
        self.ax_fft.set_ylabel("Magnitude (dB)")
        self.ax_fft.grid(True)
        (self.line_fft,) = self.ax_fft.plot(self.fft_freqs, self.fft_db, linewidth=1.0)
        self.ax_fft.set_xlim(0, min(20000, self.sr / 2))
        self.ax_fft.set_ylim(-120, 0)

        # STFT spec
        self.ax_spec.set_xlabel("Temps (s)")
        self.ax_spec.set_ylabel("Fréquence (Hz)")
        spec_extent = (-self.spec_seconds, 0.0, 0.0, float(self.spec_freqs_view[-1]) if self.spec_freqs_view.size else 0.0)
        self.im_spec = self.ax_spec.imshow(
            self.spec_img, origin="lower", aspect="auto",
            extent=spec_extent, interpolation="nearest",
        )
        self.ax_spec.set_ylim(0, min(self.spec_max_freq, self.sr / 2))
        self.im_spec.set_clim(-100, 0)

        # MFCC spec
        self.ax_mfcc.set_xlabel("Temps (s)")
        self.ax_mfcc.set_ylabel("MFCC index")
        mfcc_extent = (-self.spec_seconds, 0.0, 0.0, float(self.mfcc_cfg.n_mfcc))
        self.im_mfcc = self.ax_mfcc.imshow(
            self.mfcc_img, origin="lower", aspect="auto",
            extent=mfcc_extent, interpolation="nearest",
        )
        self.im_mfcc.set_clim(-50, 50)

        self.fig.tight_layout()
        root.addWidget(self.canvas)

        # Controls
        controls = QtWidgets.QGridLayout()

        controls.addWidget(QtWidgets.QLabel("Label:"), 0, 0)
        self.label_edit = QtWidgets.QLineEdit()
        self.label_edit.setPlaceholderText("kick / snare / hihat / speech / silence")
        controls.addWidget(self.label_edit, 0, 1, 1, 2)

        controls.addWidget(QtWidgets.QLabel("Durée enreg. (s):"), 0, 3)
        self.rec_dur = QtWidgets.QDoubleSpinBox()
        self.rec_dur.setRange(0.2, 10.0)
        self.rec_dur.setSingleStep(0.1)
        self.rec_dur.setValue(1.0)
        controls.addWidget(self.rec_dur, 0, 4)

        self.btn_record = QtWidgets.QPushButton("Enregistrer")
        self.btn_record.clicked.connect(self.on_record)
        controls.addWidget(self.btn_record, 1, 0)

        self.btn_train = QtWidgets.QPushButton("Entraîner")
        self.btn_train.clicked.connect(self.on_train)
        controls.addWidget(self.btn_train, 1, 1)

        self.btn_load = QtWidgets.QPushButton("Charger modèle")
        self.btn_load.clicked.connect(self.on_load_model)
        controls.addWidget(self.btn_load, 1, 2)

        self.btn_recog = QtWidgets.QPushButton("Reconnaissance: OFF")
        self.btn_recog.clicked.connect(self.on_toggle_recognition)
        controls.addWidget(self.btn_recog, 1, 3)

        controls.addWidget(QtWidgets.QLabel("Fenêtre reco (s):"), 1, 4)
        self.recog_dur = QtWidgets.QDoubleSpinBox()
        self.recog_dur.setRange(0.2, 5.0)
        self.recog_dur.setSingleStep(0.1)
        self.recog_dur.setValue(1.0)
        controls.addWidget(self.recog_dur, 1, 5)

        # Seuil de confiance
        controls.addWidget(QtWidgets.QLabel("Seuil confiance:"), 2, 0)
        self.conf_spin = QtWidgets.QDoubleSpinBox()
        self.conf_spin.setRange(0.0, 1.0)
        self.conf_spin.setSingleStep(0.05)
        self.conf_spin.setValue(self.confidence_threshold)
        controls.addWidget(self.conf_spin, 2, 1)

        # Seuil RMS
        controls.addWidget(QtWidgets.QLabel("Seuil RMS:"), 2, 2)
        self.rms_spin = QtWidgets.QDoubleSpinBox()
        self.rms_spin.setRange(0.0, 1.0)
        self.rms_spin.setSingleStep(0.005)
        self.rms_spin.setDecimals(4)
        self.rms_spin.setValue(self.rms_threshold)
        controls.addWidget(self.rms_spin, 2, 3)

        self.status = QtWidgets.QLabel("Prêt.")
        controls.addWidget(self.status, 3, 0, 1, 6)

        # Prediction label
        self.pred_label = QtWidgets.QLabel("-")
        self.pred_label.setStyleSheet(
            "font-size: 48px; font-weight: bold; color: #FF6B1A; padding: 10px;"
        )
        self.pred_label.setAlignment(QtCore.Qt.AlignCenter)
        root.addWidget(self.pred_label)

        # Confidence bar
        self.conf_label = QtWidgets.QLabel("confiance: —")
        self.conf_label.setStyleSheet("font-family: monospace; color: #9C9CA4;")
        self.conf_label.setAlignment(QtCore.Qt.AlignCenter)
        root.addWidget(self.conf_label)

        root.addLayout(controls)
        self.setCentralWidget(central)

        # timer
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_ui)

        # stream
        self.stream = sd.InputStream(
            samplerate=self.sr,
            channels=self.channels,
            blocksize=self.blocksize,
            dtype="float32",
            callback=self.audio_callback,
        )
        self.stream.start()
        self.timer.start()

    # ---------------- Audio callback ----------------

    def audio_callback(self, indata, frames, time_info, status):
        x = indata[:, 0].copy() if self.channels > 1 else indata.reshape(-1).copy()
        try:
            self.q.put_nowait(x)
        except queue.Full:
            pass

    # ---------------- Actions ----------------

    def on_record(self):
        label = self.label_edit.text().strip()
        if not label:
            self.status.setText("⚠️ Entre un label avant d'enregistrer.")
            return

        dur = float(self.rec_dur.value())
        self.record_target_n = int(self.sr * dur)
        self.record_label = label
        self.record_buf = []
        self.recording_on = True
        self.status.setText(f"⏺️ Enregistrement '{label}' ({dur:.1f}s)...")

    def on_train(self):
        X, y = self.load_dataset_features()
        if X is None:
            return

        # Vérifie qu'on a au moins 2 classes et assez d'échantillons
        labels, counts = np.unique(y, return_counts=True)
        if len(labels) < 2:
            self.status.setText("⚠️ Il faut au moins 2 classes pour entraîner.")
            return
        if counts.min() < 2:
            self.status.setText(f"⚠️ Classe '{labels[counts.argmin()]}' a trop peu d'échantillons.")
            return

        # Train/test split
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, stratify=y, random_state=42
            )
        except ValueError:
            # fallback sans stratify si trop peu d'échantillons
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

        clf = Pipeline([
            ("scaler", StandardScaler()),
            ("svm", SVC(kernel="rbf", C=10, gamma="scale", probability=True)),
        ])
        clf.fit(X_train, y_train)

        # Évaluation
        y_pred = clf.predict(X_test)
        report = classification_report(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred, labels=labels)

        print("\n" + "=" * 50)
        print("CLASSIFICATION REPORT")
        print("=" * 50)
        print(report)
        print("CONFUSION MATRIX (rows=true, cols=pred)")
        print("Labels:", list(labels))
        print(cm)
        print("=" * 50 + "\n")

        # Sauvegarde
        joblib.dump(clf, self.model_path)
        self.model = clf

        summary = ", ".join([f"{lab}:{cnt}" for lab, cnt in zip(labels, counts)])
        acc = (y_pred == y_test).mean()
        self.status.setText(
            f"✅ Modèle entraîné. Acc test={acc:.2%}. Dataset: {summary}. "
            f"Détails dans la console."
        )

    def on_load_model(self):
        if not self.model_path.exists():
            self.status.setText(f"⚠️ Modèle introuvable: {self.model_path}")
            return
        self.model = joblib.load(self.model_path)
        self.status.setText(f"✅ Modèle chargé: {self.model_path}")

    def on_toggle_recognition(self):
        self.recognition_on = not self.recognition_on
        self.btn_recog.setText(f"Reconnaissance: {'ON' if self.recognition_on else 'OFF'}")
        if self.recognition_on and self.model is None:
            self.status.setText("⚠️ Aucun modèle chargé.")
        else:
            self.status.setText(
                "Reconnaissance activée." if self.recognition_on else "Reconnaissance désactivée."
            )

    def load_dataset_features(self):
        if not self.dataset_dir.exists():
            self.status.setText(f"⚠️ Dossier '{self.dataset_dir}' introuvable.")
            return None, None

        X_list, y_list = [], []
        for label_dir in self.dataset_dir.iterdir():
            if not label_dir.is_dir():
                continue
            label = label_dir.name
            for wav_file in label_dir.glob("*.wav"):
                try:
                    x, sr = load_wav_as_float(wav_file)
                    if sr != self.sr:
                        continue
                    feat = self.mfcc_extractor.features(x)
                    X_list.append(feat)
                    y_list.append(label)
                except Exception as e:
                    print(f"Erreur lecture {wav_file}: {e}")

        if len(X_list) == 0:
            self.status.setText("⚠️ Aucun WAV trouvé dans le dataset.")
            return None, None

        return np.stack(X_list, axis=0), np.array(y_list)

    # ---------------- UI Update ----------------

    def update_ui(self):
        chunks = []
        while True:
            try:
                chunks.append(self.q.get_nowait())
            except queue.Empty:
                break
        if not chunks:
            return

        new_audio = np.concatenate(chunks)

        # Recording
        if self.recording_on:
            self.record_buf.append(new_audio)
            total = sum(len(c) for c in self.record_buf)
            if total >= self.record_target_n:
                audio_data = np.concatenate(self.record_buf)[:self.record_target_n]
                label_dir = self.dataset_dir / self.record_label
                label_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{int(time.time() * 1000)}.wav"
                save_wav_int16(label_dir / filename, audio_data, self.sr)
                self.status.setText(f"✅ Enregistré: {label_dir / filename}")
                self.recording_on = False
                self.record_buf = []

        # Waveform ring
        n = len(new_audio)
        if n >= self.wave_n:
            self.wave_ring[:] = new_audio[-self.wave_n:]
        else:
            self.wave_ring = np.roll(self.wave_ring, -n)
            self.wave_ring[-n:] = new_audio

        # Recognition buffer
        if n >= self.recog_buf_max:
            self.recog_buf[:] = new_audio[-self.recog_buf_max:]
        else:
            self.recog_buf = np.roll(self.recog_buf, -n)
            self.recog_buf[-n:] = new_audio

        # FFT
        if n >= self.fft_size:
            self.fft_buf[:] = new_audio[-self.fft_size:]
        else:
            self.fft_buf = np.roll(self.fft_buf, -n)
            self.fft_buf[-n:] = new_audio

        windowed = self.fft_buf * self.fft_win
        spectrum = np.fft.rfft(windowed)
        mag = np.maximum(np.abs(spectrum), 1e-12)
        self.fft_db = 20 * np.log10(mag / self.fft_size)

        # STFT + MFCC spectrograms
        self.stft_pending = np.concatenate([self.stft_pending, new_audio])
        while len(self.stft_pending) >= self.stft_nfft:
            frame = self.stft_pending[:self.stft_nfft] * self.stft_win
            self.stft_pending = self.stft_pending[self.stft_hop:]
            spectrum = np.fft.rfft(frame)
            mag = np.maximum(np.abs(spectrum), 1e-12)
            db = 20 * np.log10(mag)
            db_view = db[self.spec_fmask]

            self.spec_img = np.roll(self.spec_img, -1, axis=1)
            self.spec_img[:, -1] = db_view

            power = np.clip(np.nan_to_num((mag ** 2).astype(np.float32)), 0.0, 1e10)
            mel_energy = np.maximum(self.mfcc_extractor.mel_fb @ power, 1e-12)
            log_mel = np.log(mel_energy).astype(np.float32)
            mfcc_frame = (self.mfcc_extractor.dct @ log_mel).astype(np.float32)

            self.mfcc_img = np.roll(self.mfcc_img, -1, axis=1)
            self.mfcc_img[:, -1] = mfcc_frame

        # Recognition (avec seuils)
        if self.recognition_on and self.model is not None:
            self.recog_seconds = float(self.recog_dur.value())
            self.confidence_threshold = float(self.conf_spin.value())
            self.rms_threshold = float(self.rms_spin.value())

            recog_n = int(self.recog_seconds * self.sr)
            window = self.recog_buf[-recog_n:]

            # 1) Filtre énergie
            rms = compute_rms(window)
            if rms < self.rms_threshold:
                self.pred_label.setText("—")
                self.conf_label.setText(f"silence · rms={rms:.4f}")
            else:
                feat = self.mfcc_extractor.features(window).reshape(1, -1)
                probas = self.model.predict_proba(feat)[0]
                classes = self.model.classes_
                top_idx = int(np.argmax(probas))
                top_class = classes[top_idx]
                top_proba = float(probas[top_idx])

                # 2) Filtre confiance
                if top_proba < self.confidence_threshold:
                    self.pred_label.setText("?")
                    self.conf_label.setText(
                        f"incertain · {top_class} {top_proba:.2f} (< {self.confidence_threshold:.2f})"
                    )
                else:
                    self.last_prediction = top_class
                    self.pred_label.setText(str(top_class))
                    # affiche top-2 pour debug
                    sorted_idx = np.argsort(probas)[::-1][:2]
                    debug = " · ".join(
                        f"{classes[i]} {probas[i]:.2f}" for i in sorted_idx
                    )
                    self.conf_label.setText(debug)
                    print(f"[PREDICTION] {top_class} ({top_proba:.2f})")

        # Redraw
        self.line_wave.set_ydata(self.wave_ring)
        self.line_fft.set_ydata(self.fft_db)
        self.im_spec.set_data(self.spec_img)
        self.im_mfcc.set_data(self.mfcc_img)
        self.canvas.draw_idle()

    def closeEvent(self, event):
        self.timer.stop()
        self.stream.stop()
        self.stream.close()
        event.accept()


# ---------------- Main ----------------

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())