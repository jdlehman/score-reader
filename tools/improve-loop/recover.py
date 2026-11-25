#!/usr/bin/env python3
"""Photometric recovery for degraded page images (median + Richardson-Lucy).

Vendored, trimmed, from the photometric spike in the local workspace.
Only the recovery methods and the single-image CLI are kept here; the
spike's batch commands (`all-hard`, `all`) and its hard-coded local
page list are not — they were tied to the local test set. The loop
calls this one image at a time.

Shipped method is `median+rl`: a 3x3 median denoise, then
Richardson-Lucy deconvolution with a Gaussian PSF sigma=1.8 for 15
iterations. It is the only method with a full safety record across
the benchmark (see EXPERIMENTS.md); plain `rl` is stronger on some
hard pages but unsafe ungated, and every other method in METHODS is
a documented NO-GO. Dependencies: cv2, numpy, Pillow, scipy
(requirements.txt).

Usage: python3 recover.py <method> <in.png> <out.png>
"""
import sys
import time

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage, signal


def _u8(a):
    return np.clip(a, 0, 255).astype(np.uint8)


def shadow_gauss(img):
    f = img.astype(np.float32)
    small = cv2.resize(f, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    bg_small = cv2.GaussianBlur(small, (0, 0), 20)
    bg = cv2.resize(bg_small, (img.shape[1], img.shape[0]),
                    interpolation=cv2.INTER_CUBIC)
    bg = np.maximum(bg, 8.0)
    return _u8(f / bg * 255.0)


def shadow_close(img):
    f = img.astype(np.float32)
    small = cv2.resize(f, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    bg_small = cv2.morphologyEx(small, cv2.MORPH_CLOSE, k)
    bg = cv2.resize(bg_small, (img.shape[1], img.shape[0]),
                    interpolation=cv2.INTER_CUBIC)
    bg = np.maximum(bg, 8.0)
    return _u8(f / bg * 255.0)


def unsharp(img, sigma=1.5, amount=1.5):
    blur = cv2.GaussianBlur(img, (0, 0), sigma)
    return _u8(img.astype(np.float32) + amount * (img.astype(np.float32) - blur))


def wiener5(img):
    return _u8(signal.wiener(img.astype(np.float64), mysize=5, noise=None))


def rl(img, sigma=1.8, iters=15):
    # Richardson-Lucy with a Gaussian PSF; float32, scipy.ndimage convolve.
    r = int(np.ceil(3 * sigma))
    ax = np.arange(-r, r + 1, dtype=np.float32)
    psf1 = np.exp(-0.5 * (ax / sigma) ** 2)
    psf1 /= psf1.sum()
    psf = np.outer(psf1, psf1).astype(np.float32)
    psf_t = psf[::-1, ::-1]
    g = img.astype(np.float32) / 255.0
    u = g.copy()
    eps = 1e-6
    for _ in range(iters):
        conv = ndimage.convolve(u, psf, mode="nearest")
        ratio = g / np.maximum(conv, eps)
        u = u * ndimage.convolve(ratio, psf_t, mode="nearest")
        u = np.clip(u, 0.0, 1.0)
    return _u8(u * 255.0)


def clahe(img, clip=2.0):
    return cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8)).apply(img)


def contrast(img):
    lo, hi = np.percentile(img, [1, 99])
    if hi - lo < 1:
        return img
    return _u8((img.astype(np.float32) - lo) * 255.0 / (hi - lo))


def median3(img):
    return cv2.medianBlur(img, 3)


METHODS = {
    "shadow-gauss": lambda im: shadow_gauss(im),
    "shadow-close": lambda im: shadow_close(im),
    "unsharp": lambda im: unsharp(im),
    "wiener5": lambda im: wiener5(im),
    "rl": lambda im: rl(im),
    "clahe": lambda im: clahe(im),
    "contrast": lambda im: contrast(im),
    "shadow+unsharp": lambda im: unsharp(shadow_gauss(im)),
    "shadow+clahe": lambda im: clahe(shadow_gauss(im)),
    "shadow+unsharp+clahe": lambda im: clahe(unsharp(shadow_gauss(im))),
    "shadow+rl": lambda im: rl(shadow_gauss(im)),
    "shadow+wiener": lambda im: wiener5(shadow_gauss(im)),
    "median+shadow+unsharp": lambda im: unsharp(shadow_gauss(median3(im))),
    # RL tuning round 2 (added after hard screen 1)
    "rl5": lambda im: rl(im, iters=5),
    "rl25": lambda im: rl(im, iters=25),
    "rl-s12": lambda im: rl(im, sigma=1.2),
    "rl-s25": lambda im: rl(im, sigma=2.5),
    "median+rl": lambda im: rl(median3(im)),
    "rl+shadow": lambda im: shadow_gauss(rl(im)),
    # RL tuning round 3 (after rl5 >> rl15 >> rl25 on Lindenbaum)
    "rl3": lambda im: rl(im, iters=3),
    "median+rl5": lambda im: rl(median3(im), iters=5),
}


def run_one(method, src, dst):
    img = np.asarray(Image.open(src).convert("L"))
    t0 = time.time()
    out = METHODS[method](img)
    dt = time.time() - t0
    Image.fromarray(out).save(dst)
    print(f"{method} {src.split('/')[-1]} {dt:.1f}s", flush=True)
    return dt


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in METHODS:
        print("usage: recover.py <method> <in.png> <out.png>")
        print("methods: " + ", ".join(sorted(METHODS)))
        sys.exit(2)
    method, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    run_one(method, src, dst)


if __name__ == "__main__":
    main()
