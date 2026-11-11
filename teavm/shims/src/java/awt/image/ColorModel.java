package java.awt.image;
/** Minimal java.awt.image.ColorModel. */
public abstract class ColorModel {
    protected int pixel_bits;
    protected int transferType;
    protected ColorModel(int pixel_bits) { this.pixel_bits = pixel_bits; }
    public int getPixelSize() { return pixel_bits; }
    public int getTransferType() { return transferType; }
    public int getNumComponents() { return 4; }
    public int getNumColorComponents() { return 3; }
    public abstract int getRed(int pixel);
    public abstract int getGreen(int pixel);
    public abstract int getBlue(int pixel);
    public abstract int getAlpha(int pixel);
    public int getRGB(int pixel) {
        return (getAlpha(pixel) << 24) | (getRed(pixel) << 16) | (getGreen(pixel) << 8) | getBlue(pixel);
    }
    public int getRGB(Object inData) {
        int[] a = (int[]) inData;
        return getRGB(a[0]);
    }
    public boolean hasAlpha() { return true; }
    public boolean isAlphaPremultiplied() { return false; }
    public SampleModel createCompatibleSampleModel(int w, int h) {
        return new ComponentSampleModel(DataBuffer.TYPE_BYTE, w, h, 1, w, new int[]{0});
    }
    public WritableRaster createCompatibleWritableRaster(int w, int h) {
        return new WritableRaster(createCompatibleSampleModel(w, h), createCompatibleSampleModel(w, h).createDataBuffer(), new java.awt.Point(0, 0));
    }
    public boolean isCompatibleRaster(Raster r) { return true; }
    public boolean isCompatibleSampleModel(SampleModel sm) { return true; }
    public java.awt.color.ColorSpace getColorSpace() { return null; }
    public String toString() { return getClass().getName(); }
}
