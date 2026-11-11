package java.awt.image;
import java.awt.Point;
import java.awt.Rectangle;
/** Minimal java.awt.image.Raster (read-only view over a DataBuffer). */
public class Raster {
    protected SampleModel sampleModel;
    protected DataBuffer dataBuffer;
    protected Rectangle bounds;
    protected int minX, minY, width, height;
    protected int numBands;
    protected Raster(SampleModel sampleModel, DataBuffer dataBuffer, Rectangle bounds, Point origin) {
        this.sampleModel = sampleModel; this.dataBuffer = dataBuffer; this.bounds = bounds;
        minX = bounds.x; minY = bounds.y; width = bounds.width; height = bounds.height;
        numBands = sampleModel.getNumBands();
    }
    protected Raster(SampleModel sampleModel, DataBuffer dataBuffer, Point origin) {
        this(sampleModel, dataBuffer, new Rectangle(origin.x, origin.y, sampleModel.getWidth(), sampleModel.getHeight()), origin);
    }
    public static WritableRaster createInterleavedRaster(DataBuffer db, int w, int h, int scanlineStride,
                                                         int pixelStride, int[] bandOffsets, Point location) {
        // TEAVM §13: mirror the JDK, which defaults a null location to
        // (0,0) — same family as the §12 createWritableRaster fix.
        if (location == null) {
            location = new Point(0, 0);
        }
        SampleModel sm = new ComponentSampleModel(db.getDataType(), w, h, pixelStride, scanlineStride, bandOffsets);
        return new WritableRaster(sm, db, new Rectangle(location.x, location.y, w, h), location);
    }
    public static WritableRaster createInterleavedRaster(int dataType, int w, int h, int bands, Point location) {
        int[] offs = new int[bands];
        for (int i = 0; i < bands; i++) offs[i] = i;
        DataBuffer db = dataType == DataBuffer.TYPE_INT ? new DataBufferInt(w * h * bands) : new DataBufferByte(w * h * bands);
        return createInterleavedRaster(db, w, h, w * bands, bands, offs, location);
    }
    public static WritableRaster createBandedRaster(int dataType, int w, int h, int bands, Point location) {
        // TEAVM §13: mirror the JDK, which defaults a null location to
        // (0,0) — same family as the §12 createWritableRaster fix.
        if (location == null) {
            location = new Point(0, 0);
        }
        int[] offs = new int[bands];
        DataBuffer db = new DataBufferByte(w * h * bands);
        SampleModel sm = new ComponentSampleModel(dataType, w, h, 1, w, offs);
        return new WritableRaster(sm, db, new Rectangle(location.x, location.y, w, h), location);
    }
    public static WritableRaster createPackedRaster(int dataType, int w, int h, int[] bandMasks, Point location) {
        throw new UnsupportedOperationException("createPackedRaster not implemented in TeaVM shim");
    }
    public final int getMinX() { return minX; }
    public final int getMinY() { return minY; }
    public final int getWidth() { return width; }
    public final int getHeight() { return height; }
    public final int getNumBands() { return numBands; }
    public final int getNumDataElements() { return sampleModel.getNumDataElements(); }
    public final DataBuffer getDataBuffer() { return dataBuffer; }
    public final SampleModel getSampleModel() { return sampleModel; }
    public Rectangle getBounds() { return new Rectangle(bounds); }
    public int getSample(int x, int y, int b) { return sampleModel.getSample(x - minX, y - minY, b, dataBuffer); }
    public int[] getPixel(int x, int y, int[] iArray) {
        return sampleModel.getPixel(x - minX, y - minY, iArray, dataBuffer);
    }
    public int[] getPixels(int x, int y, int w, int h, int[] iArray) {
        int[] out = iArray == null ? new int[w * h * numBands] : iArray;
        int k = 0;
        for (int yy = y; yy < y + h; yy++)
            for (int xx = x; xx < x + w; xx++)
                for (int b = 0; b < numBands; b++) out[k++] = getSample(xx, yy, b);
        return out;
    }
    public Object getDataElements(int x, int y, Object obj) {
        return sampleModel.getDataElements(x - minX, y - minY, obj, dataBuffer);
    }
    public Object getDataElements(int x, int y, int w, int h, Object obj) {
        byte[] out = (obj instanceof byte[] b) ? b : new byte[w * h * numBands];
        int k = 0;
        for (int yy = y; yy < y + h; yy++)
            for (int xx = x; xx < x + w; xx++) {
                byte[] px = (byte[]) getDataElements(xx, yy, null);
                for (int b = 0; b < numBands; b++) out[k++] = px[b];
            }
        return out;
    }
    public static WritableRaster createWritableRaster(SampleModel sm, DataBuffer db, Point origin) {
        // TEAVM §12: mirror the JDK, which defaults a null origin to (0,0).
        // ij ByteProcessor.createBufferedImage passes null here; without the
        // default the 3-arg Raster ctor dereferences origin.x and traps
        // under TeaVM WasmGC (GRID step, Picture.buildNoStaffBuffer, first
        // seen in full-out18).
        if (origin == null) {
            origin = new Point(0, 0);
        }
        return new WritableRaster(sm, db, origin);
    }
    public Raster createChild(int x, int y, int w, int h, int x0, int y0, int[] bands) {
        return this;
    }
    public Raster getParent() { return null; }
}
