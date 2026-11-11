package java.awt.image;
/** Minimal java.awt.image.IndexColorModel. */
public class IndexColorModel extends ColorModel {
    private final int mapSize;
    private final byte[] r, g, b, a;
    public IndexColorModel(int bits, int size, byte[] r, byte[] g, byte[] b) {
        super(bits);
        transferType = DataBuffer.TYPE_BYTE;
        mapSize = size;
        this.r = r.clone(); this.g = g.clone(); this.b = b.clone();
        this.a = new byte[size];
        for (int i = 0; i < size; i++) this.a[i] = (byte) 0xff;
    }
    public IndexColorModel(int bits, int size, byte[] r, byte[] g, byte[] b, byte[] a) {
        super(bits);
        transferType = DataBuffer.TYPE_BYTE;
        mapSize = size;
        this.r = r.clone(); this.g = g.clone(); this.b = b.clone(); this.a = a.clone();
    }
    public IndexColorModel(int bits, int size, byte[] cmap, int start, boolean hasAlpha) {
        super(bits);
        transferType = DataBuffer.TYPE_BYTE;
        mapSize = size;
        r = new byte[size]; g = new byte[size]; this.b = new byte[size]; a = new byte[size];
        for (int i = 0; i < size; i++) {
            r[i] = cmap[start + i * (hasAlpha ? 4 : 3)];
            g[i] = cmap[start + i * (hasAlpha ? 4 : 3) + 1];
            b[i] = cmap[start + i * (hasAlpha ? 4 : 3) + 2];
            a[i] = hasAlpha ? cmap[start + i * 4 + 3] : (byte) 0xff;
        }
    }
    public IndexColorModel(int bits, int size, byte[] r, byte[] g, byte[] b, int trans) {
        super(bits);
        transferType = DataBuffer.TYPE_BYTE;
        mapSize = size;
        this.r = r.clone(); this.g = g.clone(); this.b = b.clone();
        this.a = new byte[size];
        for (int i = 0; i < size; i++) this.a[i] = (i == trans) ? (byte) 0 : (byte) 0xff;
    }
    public int getMapSize() { return mapSize; }
    @Override public int getRed(int pixel) { return r[pixel & 0xff] & 0xff; }
    @Override public int getGreen(int pixel) { return g[pixel & 0xff] & 0xff; }
    @Override public int getBlue(int pixel) { return b[pixel & 0xff] & 0xff; }
    @Override public int getAlpha(int pixel) { return a[pixel & 0xff] & 0xff; }
    public void getReds(byte[] out) { System.arraycopy(r, 0, out, 0, Math.min(mapSize, out.length)); }
    public void getGreens(byte[] out) { System.arraycopy(g, 0, out, 0, Math.min(mapSize, out.length)); }
    public void getBlues(byte[] out) { System.arraycopy(b, 0, out, 0, Math.min(mapSize, out.length)); }
    public void getAlphas(byte[] out) { System.arraycopy(a, 0, out, 0, Math.min(mapSize, out.length)); }
    public int getTransparentPixel() { return -1; }
}
