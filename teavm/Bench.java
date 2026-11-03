// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
/**
 * The kind of work Audiveris's slowest step does, as plain arrays: a chamfer distance transform of
 * a page-sized binary image, then template matching at many positions (as NoteHeadsBuilder does).
 */
public class Bench {
    static final int W = 2480, H = 3508;

    public static void main(String[] args) {
        // a page: staff-like lines and note-like blobs, deterministic
        byte[] img = new byte[W * H];
        for (int s = 0; s < 12; s++) for (int l = 0; l < 5; l++) {
            int y = 300 + s * 260 + l * 22;
            for (int x = 150; x < W - 150; x++) { img[y * W + x] = 1; img[(y + 1) * W + x] = 1; }
        }
        long seed = 42;
        for (int n = 0; n < 4000; n++) {
            seed = seed * 6364136223846793005L + 1442695040888963407L;
            int cx = 200 + (int) ((seed >>> 33) % (W - 400)), cy = 300 + (int) ((seed >>> 13) % (H - 600));
            for (int dy = -9; dy <= 9; dy++) for (int dx = -12; dx <= 12; dx++) if (dx * dx * 81 + dy * dy * 144 <= 11664) img[(cy + dy) * W + cx + dx] = 1;
        }
        // template: key points (x, y, kind) of an elliptic head, 0 fore, 1 back
        int n = 0;
        int[] kx = new int[2000], ky = new int[2000]; byte[] kk = new byte[2000];
        for (int dy = -14; dy <= 14; dy += 2) for (int dx = -18; dx <= 18; dx += 2) {
            int r = dx * dx * 81 + dy * dy * 144;
            kx[n] = dx + 18; ky[n] = dy + 14; kk[n] = (byte) (r <= 11664 ? 0 : 1); n++;
        }
        long best = Long.MAX_VALUE;
        double sum = 0;
        for (int round = 0; round < 5; round++) {
            long t0 = System.nanoTime();
            short[] dist = chamfer(img);
            sum += match(dist, kx, ky, kk, n);
            long ms = (System.nanoTime() - t0) / 1_000_000;
            best = Math.min(best, ms);
        }
        System.out.println("bench: best of 5 = " + best + " ms (check " + (long) sum + ")");
    }

    /** Two-pass 3-4 chamfer distance to the nearest foreground pixel. */
    static short[] chamfer(byte[] img) {
        short[] d = new short[W * H];
        for (int i = 0; i < d.length; i++) d[i] = img[i] != 0 ? 0 : Short.MAX_VALUE;
        for (int y = 1; y < H; y++) for (int x = 1; x < W - 1; x++) {
            int i = y * W + x, v = d[i];
            v = Math.min(v, d[i - 1] + 3); v = Math.min(v, d[i - W] + 3); v = Math.min(v, d[i - W - 1] + 4); v = Math.min(v, d[i - W + 1] + 4);
            d[i] = (short) Math.min(v, Short.MAX_VALUE);
        }
        for (int y = H - 2; y >= 0; y--) for (int x = W - 2; x >= 1; x--) {
            int i = y * W + x, v = d[i];
            v = Math.min(v, d[i + 1] + 3); v = Math.min(v, d[i + W] + 3); v = Math.min(v, d[i + W + 1] + 4); v = Math.min(v, d[i + W - 1] + 4);
            d[i] = (short) v;
        }
        return d;
    }

    /** Template matching along every staff line and space, as the heads step scans. */
    static double match(short[] d, int[] kx, int[] ky, byte[] kk, int n) {
        double total = 0;
        for (int s = 0; s < 12; s++) for (int p = -6; p <= 14; p++) {
            int y = 300 + s * 260 + p * 11;
            for (int x = 150; x < W - 190; x++) {
                double t = 0, w = 0;
                for (int i = 0; i < n; i++) {
                    int nx = x + kx[i] - 18, ny = y + ky[i] - 14;
                    if (nx >= 0 && nx < W && ny >= 0 && ny < H) {
                        int a = d[ny * W + nx];
                        double weight = kk[i] == 0 ? 4.0 : 1.0;
                        if ((a == 0) != (kk[i] == 0)) t += weight;
                        w += weight;
                    }
                }
                total += t / w;
            }
        }
        return total;
    }
}
