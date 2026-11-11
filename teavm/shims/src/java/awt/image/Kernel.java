package java.awt.image;
/** Minimal java.awt.image.Kernel. */
public class Kernel implements Cloneable {
    private final int width, height;
    private final float[] data;
    public Kernel(int width, int height, float[] data) {
        this.width = width; this.height = height;
        this.data = data.clone();
    }
    public int getWidth() { return width; }
    public int getHeight() { return height; }
    public int getXOrigin() { return (width - 1) / 2; }
    public int getYOrigin() { return (height - 1) / 2; }
    public float[] getKernelData(float[] out) {
        if (out == null) return data.clone();
        System.arraycopy(data, 0, out, 0, data.length);
        return out;
    }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
}
