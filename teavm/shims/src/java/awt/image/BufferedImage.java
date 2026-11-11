package java.awt.image;
import java.awt.Graphics2D;
import java.awt.Point;
import java.awt.Rectangle;
import java.util.Hashtable;
/** Minimal java.awt.image.BufferedImage with real grey/int pixel storage. */
public class BufferedImage extends java.awt.Image {
    public static final int TYPE_CUSTOM = 0;
    public static final int TYPE_INT_RGB = 1;
    public static final int TYPE_INT_ARGB = 2;
    public static final int TYPE_INT_ARGB_PRE = 3;
    public static final int TYPE_INT_BGR = 4;
    public static final int TYPE_3BYTE_BGR = 5;
    public static final int TYPE_4BYTE_ABGR = 6;
    public static final int TYPE_4BYTE_ABGR_PRE = 7;
    public static final int TYPE_USHORT_565_RGB = 8;
    public static final int TYPE_USHORT_555_RGB = 9;
    public static final int TYPE_BYTE_GRAY = 10;
    public static final int TYPE_USHORT_GRAY = 11;
    public static final int TYPE_BYTE_BINARY = 12;
    public static final int TYPE_BYTE_INDEXED = 13;
    private final int imageType;
    private final int width, height;
    private final ColorModel colorModel;
    private final WritableRaster raster;
    private static ColorModel grayModel() {
        byte[] ramp = new byte[256];
        for (int i = 0; i < 256; i++) ramp[i] = (byte) i;
        return new IndexColorModel(8, 256, ramp, ramp, ramp);
    }
    public BufferedImage(int width, int height, int imageType) {
        this.imageType = imageType;
        this.width = width; this.height = height;
        if (imageType == TYPE_BYTE_GRAY || imageType == TYPE_BYTE_BINARY || imageType == TYPE_BYTE_INDEXED) {
            colorModel = grayModel();
            SampleModel sm = new ComponentSampleModel(DataBuffer.TYPE_BYTE, width, height, 1, width, new int[]{0});
            raster = new WritableRaster(sm, new DataBufferByte(width * height), new Point(0, 0));
        } else if (imageType == TYPE_INT_RGB || imageType == TYPE_INT_ARGB || imageType == TYPE_INT_ARGB_PRE || imageType == TYPE_INT_BGR) {
            colorModel = new IntColorModel(imageType == TYPE_INT_RGB);
            SampleModel sm = new ComponentSampleModel(DataBuffer.TYPE_INT, width, height, 1, width, new int[]{0});
            raster = new WritableRaster(sm, new DataBufferInt(width * height), new Point(0, 0));
        } else {
            throw new IllegalArgumentException("Unsupported BufferedImage type " + imageType + " in TeaVM shim");
        }
    }
    public BufferedImage(ColorModel cm, WritableRaster raster, boolean isRasterPremultiplied, Hashtable<?, ?> properties) {
        this.imageType = TYPE_CUSTOM;
        this.colorModel = cm;
        this.raster = raster;
        this.width = raster.getWidth(); this.height = raster.getHeight();
    }
    public BufferedImage(int width, int height, int imageType, IndexColorModel cm) {
        this.imageType = imageType;
        this.width = width; this.height = height;
        this.colorModel = cm;
        SampleModel sm = new ComponentSampleModel(DataBuffer.TYPE_BYTE, width, height, 1, width, new int[]{0});
        raster = new WritableRaster(sm, new DataBufferByte(width * height), new Point(0, 0));
    }
    @Override public int getWidth() { return width; }
    @Override public int getHeight() { return height; }
    @Override public int getWidth(java.awt.image.ImageObserver o) { return width; }
    @Override public int getHeight(java.awt.image.ImageObserver o) { return height; }
    public int getType() { return imageType; }
    public ColorModel getColorModel() { return colorModel; }
    public java.awt.image.SampleModel getSampleModel() { return raster.getSampleModel(); }
    public WritableRaster getRaster() { return raster; }
    public Raster getData() { return raster; }
    public Raster getData(Rectangle rect) { return raster; }
    public WritableRaster copyData(WritableRaster out) {
        if (out == null) out = (WritableRaster) raster;
        out.setRect(raster);
        return out;
    }
    // TEAVM §13: getRGB/setRGB branch on the raster's actual DataBuffer
    // runtime type, NOT on imageType. The (ColorModel, WritableRaster,
    // ...) ctor sets imageType = TYPE_CUSTOM unconditionally, so a
    // byte-backed raster (e.g. ij ByteProcessor.createBufferedImage, the
    // §12 trap in Picture.buildNoStaffBuffer) used to fall into the
    // DataBufferInt branch and trap with an illegal cast under WasmGC.
    // Behaviour for correctly-typed images is unchanged: byte rasters
    // take the sample path they always took (grey ramp via the colour
    // model — for TYPE_BYTE_GRAY and ImageJ's grey IndexColorModel the
    // palette lookup returns exactly the old 0xff000000|(v<<16)|(v<<8)|v;
    // for a non-grey indexed palette it returns the palette colour, which
    // the old grey ramp got wrong), and int rasters take the raw packed-
    // pixel path they always took (TemplateFactory's getRGB == FORE/BACK/
    // HOLE comparisons rely on the stored value, alpha included).
    // No DataBufferUShort/SHORT/FLOAT/DOUBLE shims exist; the fallback
    // below takes the sample path for any such buffer rather than casting.
    public int getRGB(int x, int y) {
        DataBuffer db = raster.getDataBuffer();
        if (db instanceof DataBufferByte) {
            if (raster.getNumBands() == 1) {
                int sample = raster.getSample(x, y, 0);
                return colorModel != null ? colorModel.getRGB(sample)
                        : 0xff000000 | (sample << 16) | (sample << 8) | sample;
            }
            // Multi-band byte: samples in stored band order. No such
            // raster occurs on the Audiveris grey path (all byte rasters
            // here are 1-band); a BGR-ordered raster would need a
            // ColorModel.getDataElements conversion, which the shim lacks.
            int[] px = raster.getPixel(x, y, (int[]) null);
            if (px.length == 2) {
                return (px[1] << 24) | (px[0] << 16) | (px[0] << 8) | px[0];
            }
            int a = px.length > 3 ? px[3] : 0xff;
            return (a << 24) | (px[0] << 16) | (px[1] << 8) | px[2];
        }
        if (db instanceof DataBufferInt) {
            return ((DataBufferInt) db).getElem(y * width + x);
        }
        int sample = raster.getSample(x, y, 0);
        return colorModel != null ? colorModel.getRGB(sample)
                : 0xff000000 | (sample << 16) | (sample << 8) | sample;
    }
    public void setRGB(int x, int y, int rgb) {
        DataBuffer db = raster.getDataBuffer();
        if (db instanceof DataBufferByte) {
            if (raster.getNumBands() == 1) {
                // Single-band byte: store the grey value, as before.
                // Correct for the grey ramp / grey indexed palette on
                // this path; for a colour indexed palette the JDK would
                // store the nearest palette index, which the shim cannot
                // do cheaply (a 256-entry nearest search per pixel).
                int r = (rgb >> 16) & 0xff, g = (rgb >> 8) & 0xff, b = rgb & 0xff;
                raster.setSample(x, y, 0, (r + g + b) / 3);
                return;
            }
            // Multi-band byte: write components in stored band order.
            raster.setSample(x, y, 0, (rgb >> 16) & 0xff);
            if (raster.getNumBands() > 1) raster.setSample(x, y, 1, (rgb >> 8) & 0xff);
            if (raster.getNumBands() > 2) raster.setSample(x, y, 2, rgb & 0xff);
            if (raster.getNumBands() > 3) raster.setSample(x, y, 3, (rgb >> 24) & 0xff);
            return;
        }
        if (db instanceof DataBufferInt) {
            ((DataBufferInt) db).setElem(y * width + x, rgb);
            return;
        }
        int r = (rgb >> 16) & 0xff, g = (rgb >> 8) & 0xff, b = rgb & 0xff;
        raster.setSample(x, y, 0, (r + g + b) / 3);
    }
    public int[] getRGB(int x, int y, int w, int h, int[] rgbArray, int offset, int scansize) {
        int[] out = rgbArray == null ? new int[w * h] : rgbArray;
        for (int yy = 0; yy < h; yy++)
            for (int xx = 0; xx < w; xx++) out[offset + yy * scansize + xx] = getRGB(x + xx, y + yy);
        return out;
    }
    public void setRGB(int x, int y, int w, int h, int[] rgbArray, int offset, int scansize) {
        for (int yy = 0; yy < h; yy++)
            for (int xx = 0; xx < w; xx++) setRGB(x + xx, y + yy, rgbArray[offset + yy * scansize + xx]);
    }
    public BufferedImage getSubimage(int x, int y, int w, int h) {
        BufferedImage sub = new BufferedImage(w, h, imageType == TYPE_CUSTOM ? TYPE_BYTE_GRAY : imageType);
        for (int yy = 0; yy < h; yy++)
            for (int xx = 0; xx < w; xx++) sub.setRGB(xx, yy, getRGB(x + xx, y + yy));
        return sub;
    }
    public java.awt.Graphics getGraphics() { return createGraphics(); }
    public Graphics2D createGraphics() { return new BufferedImageGraphics(this); }
    public Object getProperty(String name) { return null; }
    @Override public java.awt.image.ImageProducer getSource() { return null; }
    @Override public Object getProperty(String name, java.awt.image.ImageObserver observer) { return null; }
    public String[] getPropertyNames() { return null; }
    public boolean isAlphaPremultiplied() { return false; }
    public WritableRaster getAlphaRaster() { return null; }
    public void setData(Raster r) {}
    public int getTransparency() { return 1; } // Transparency.OPAQUE
    @Override public String toString() {
        return "BufferedImage[" + width + "x" + height + " type=" + imageType + "]";
    }
    /** Grey ramp color model is IndexColorModel; int images use this. */
    static final class IntColorModel extends ColorModel {
        private final boolean opaque;
        IntColorModel(boolean opaque) { super(32); this.opaque = opaque; transferType = DataBuffer.TYPE_INT; }
        @Override public int getRed(int p) { return (p >> 16) & 0xff; }
        @Override public int getGreen(int p) { return (p >> 8) & 0xff; }
        @Override public int getBlue(int p) { return p & 0xff; }
        @Override public int getAlpha(int p) { return opaque ? 0xff : (p >> 24) & 0xff; }
        @Override public boolean hasAlpha() { return !opaque; }
    }
}
