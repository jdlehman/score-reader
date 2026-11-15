// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
// Photometric recovery pre-step: median denoise + Richardson-Lucy deconvolution, compiled to
// TeaVM WasmGC (teavm/deblur-build.sh).
//
// Mirrors the spike's recover.py exactly (same math, same edge handling):
//   - 3x3 median denoise (cv2.medianBlur, BORDER_REPLICATE) — optional
//   - RL with a Gaussian PSF (sigma, radius ceil(3*sigma)), float32,
//     scipy.ndimage convolve mode="nearest" (edge replicate), eps 1e-6,
//     clip u to [0,1] each iteration, output uint8 = trunc(u*255)
// The 2-D Gaussian PSF is separable, so each convolution is two 1-D
// passes (horizontal then vertical) with the same 1-D kernel; the kernel
// is symmetric, so each pass uses 7 multiplies per pixel instead of 13
// (c0*x[i] + sum_j c[j]*(x[i-j]+x[i+j])) — same sums up to float
// re-association, which the validation checks against the CPython
// reference (max abs diff must stay <= 2 levels).
//
// I/O mirrors TeavmMain: the Node runner sets JS globals
// (__deblurInput base64 grey bytes, __deblurW/H, __deblurSigma,
// __deblurIters, __deblurMedian) and reads back __deblurOutput
// (base64 grey bytes) and __deblurMs.
package teavm;

import java.util.Base64;
import org.teavm.jso.JSBody;

public class Deblur {
    @JSBody(params = {}, script = "return globalThis.__deblurInput;")
    private static native String inputB64();

    @JSBody(params = {}, script = "return globalThis.__deblurW;")
    private static native int inputW();

    @JSBody(params = {}, script = "return globalThis.__deblurH;")
    private static native int inputH();

    @JSBody(params = {}, script = "return globalThis.__deblurSigma;")
    private static native double inputSigma();

    @JSBody(params = {}, script = "return globalThis.__deblurIters;")
    private static native int inputIters();

    @JSBody(params = {}, script = "return globalThis.__deblurMedian;")
    private static native int inputMedian();

    @JSBody(params = { "s" }, script = "globalThis.__deblurOutput = s;")
    private static native void setOutput(String s);

    @JSBody(params = { "ms" }, script = "globalThis.__deblurMs = ms;")
    private static native void setMs(double ms);

    public static void main(String[] args) {
        long t0 = System.currentTimeMillis();
        byte[] in = Base64.getDecoder().decode(inputB64());
        int w = inputW();
        int h = inputH();
        double sigma = inputSigma();
        int iters = inputIters();
        boolean median = inputMedian() != 0;
        int n = w * h;

        // g: grey image as float in [0,1], median-denoised if requested.
        float[] g = new float[n];
        if (median) {
            median3(in, g, w, h);
        } else {
            for (int i = 0; i < n; i++) {
                g[i] = (in[i] & 0xFF) / 255.0f;
            }
        }

        // 1-D Gaussian kernel, radius ceil(3*sigma), normalised.
        int r = (int) Math.ceil(3.0 * sigma);
        int taps = 2 * r + 1;
        float[] k = new float[taps];
        double sum = 0.0;
        for (int j = 0; j < taps; j++) {
            double x = (j - r) / sigma;
            k[j] = (float) Math.exp(-0.5 * x * x);
            sum += k[j];
        }
        for (int j = 0; j < taps; j++) {
            k[j] = (float) (k[j] / sum);
        }

        float[] u = g.clone();
        float[] a = new float[n];
        float[] b = new float[n];
        float[] tmp = new float[n];
        float eps = 1e-6f;
        for (int it = 0; it < iters; it++) {
            sepConv(u, a, tmp, k, r, w, h);     // a = PSF (*) u
            for (int i = 0; i < n; i++) {       // a = g / max(a, eps)
                float c = a[i];
                a[i] = g[i] / (c < eps ? eps : c);
            }
            sepConv(a, b, tmp, k, r, w, h);     // b = PSF^T (*) ratio (symmetric)
            for (int i = 0; i < n; i++) {       // u = u * b, clipped
                float v = u[i] * b[i];
                u[i] = v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v);
            }
        }

        byte[] out = new byte[n];
        for (int i = 0; i < n; i++) {
            float v = u[i];
            if (v < 0.0f) {
                v = 0.0f;
            } else if (v > 1.0f) {
                v = 1.0f;
            }
            out[i] = (byte) (int) (v * 255.0f); // trunc, like numpy astype(uint8)
        }
        setOutput(Base64.getEncoder().encodeToString(out));
        setMs((double) (System.currentTimeMillis() - t0));
    }

    // 3x3 median with edge replication (cv2.medianBlur, BORDER_REPLICATE).
    // Writes float values in [0,1].
    private static void median3(byte[] in, float[] out, int w, int h) {
        int[] v = new int[9];
        for (int y = 0; y < h; y++) {
            int y0 = y > 0 ? y - 1 : 0;
            int y1 = y < h - 1 ? y + 1 : h - 1;
            for (int x = 0; x < w; x++) {
                int x0 = x > 0 ? x - 1 : 0;
                int x1 = x < w - 1 ? x + 1 : w - 1;
                v[0] = in[y0 * w + x0] & 0xFF;
                v[1] = in[y0 * w + x] & 0xFF;
                v[2] = in[y0 * w + x1] & 0xFF;
                v[3] = in[y * w + x0] & 0xFF;
                v[4] = in[y * w + x] & 0xFF;
                v[5] = in[y * w + x1] & 0xFF;
                v[6] = in[y1 * w + x0] & 0xFF;
                v[7] = in[y1 * w + x] & 0xFF;
                v[8] = in[y1 * w + x1] & 0xFF;
                // insertion sort, 9 elements; median is v[4]
                for (int i = 1; i < 9; i++) {
                    int t = v[i];
                    int j = i - 1;
                    while (j >= 0 && v[j] > t) {
                        v[j + 1] = v[j];
                        j--;
                    }
                    v[j + 1] = t;
                }
                out[y * w + x] = v[4] / 255.0f;
            }
        }
    }

    // Separable convolution with a symmetric 1-D kernel, edge replication
    // ("nearest"). Horizontal pass into tmp, vertical pass into dst.
    // tmp is caller-owned scratch (one image-sized buffer, reused).
    private static void sepConv(float[] src, float[] dst, float[] tmp, float[] k, int r, int w, int h) {
        float c0 = k[r];
        // horizontal
        for (int y = 0; y < h; y++) {
            int row = y * w;
            for (int x = 0; x < w; x++) {
                float s = c0 * src[row + x];
                for (int j = 1; j <= r; j++) {
                    float cj = k[r + j];
                    int xl = x - j;
                    if (xl < 0) {
                        xl = 0;
                    }
                    int xr = x + j;
                    if (xr > w - 1) {
                        xr = w - 1;
                    }
                    s += cj * (src[row + xl] + src[row + xr]);
                }
                tmp[row + x] = s;
            }
        }
        // vertical
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                float s = c0 * tmp[y * w + x];
                for (int j = 1; j <= r; j++) {
                    float cj = k[r + j];
                    int yt = y - j;
                    if (yt < 0) {
                        yt = 0;
                    }
                    int yb = y + j;
                    if (yb > h - 1) {
                        yb = h - 1;
                    }
                    s += cj * (tmp[yt * w + x] + tmp[yb * w + x]);
                }
                dst[y * w + x] = s;
            }
        }
    }
}
