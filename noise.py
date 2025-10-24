import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)  # reproducibility

N = 2000  # number of time steps
alpha = 0.9  # red/CAM noise persistence
sigma_white = 1.0  # std for additive noise
beta = 0.5  # multiplicative strength for CAM noise

# --- White noise ---
white = np.random.normal(0, sigma_white, N)

# --- Red noise (AR(1)) ---
red = np.zeros(N)
for t in range(1, N):
    red[t] = alpha * red[t-1] + np.random.normal(0, sigma_white)

# --- CAM noise (Correlated Additive & Multiplicative) ---
cam = np.zeros(N)
for t in range(1, N):
    # multiplicative component: noise amplitude depends on |x_t|
    sigma_t = sigma_white * (1 + beta * np.abs(cam[t-1]))
    cam[t] = alpha * cam[t-1] + np.random.normal(0, sigma_t)

# --- Power spectra (FFT) ---
def power_spectrum(x):
    f = np.fft.rfftfreq(len(x), d=1)
    P = np.abs(np.fft.rfft(x - np.mean(x)))**2
    return f[1:], P[1:]  # skip zero frequency

fw, Pw = power_spectrum(white)
fr, Pr = power_spectrum(red)
fc, Pc = power_spectrum(cam)

# --- Plot results ---
fig, axs = plt.subplots(3, 2, figsize=(12, 8))

# Time series
axs[0, 0].plot(white, color='gray')
axs[0, 0].set_title("White Noise (no correlation)")

axs[1, 0].plot(red, color='firebrick')
axs[1, 0].set_title("Red Noise (AR(1) process)")

axs[2, 0].plot(cam, color='purple')
axs[2, 0].set_title("CAM Noise (Correlated Additive + Multiplicative)")

# Power spectra (log-log)
axs[0, 1].loglog(fw, Pw, color='gray')
axs[0, 1].set_title("White Noise Power Spectrum")

axs[1, 1].loglog(fr, Pr, color='firebrick')
axs[1, 1].set_title("Red Noise Power Spectrum")

axs[2, 1].loglog(fc, Pc, color='purple')
axs[2, 1].set_title("CAM Noise Power Spectrum")

for ax in axs[:, 0]:
    ax.set_xlim(0, 400)
for ax in axs[:, 1]:
    ax.set_xlabel("Frequency (1/timestep)")
    ax.set_ylabel("Power")

plt.tight_layout()
plt.show()