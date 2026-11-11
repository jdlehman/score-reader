package java.awt.image;
import java.awt.Point;
import java.awt.Rectangle;
/** Minimal java.awt.image.WritableRaster. */
public class WritableRaster extends Raster {
    public WritableRaster(SampleModel sampleModel, DataBuffer dataBuffer, Rectangle bounds, Point origin) {
        super(sampleModel, dataBuffer, bounds, origin);
    }
    public WritableRaster(SampleModel sampleModel, DataBuffer dataBuffer, Point origin) {
        super(sampleModel, dataBuffer, origin);
    }
    public void setDataElements(int x, int y, Object obj) {
        sampleModel.setDataElements(x - minX, y - minY, obj, dataBuffer);
    }
    public void setDataElements(int x, int y, int w, int h, Object obj) {
        byte[] in = (byte[]) obj;
        int k = 0;
        for (int yy = y; yy < y + h; yy++)
            for (int xx = x; xx < x + w; xx++) {
                byte[] px = new byte[numBands];
                for (int b = 0; b < numBands; b++) px[b] = in[k++];
                setDataElements(xx, yy, px);
            }
    }
    public void setPixel(int x, int y, int[] iArray) {
        sampleModel.setPixel(x - minX, y - minY, iArray, dataBuffer);
    }
    public void setPixels(int x, int y, int w, int h, int[] iArray) {
        int k = 0;
        for (int yy = y; yy < y + h; yy++)
            for (int xx = x; xx < x + w; xx++) {
                int[] px = new int[numBands];
                for (int b = 0; b < numBands; b++) px[b] = iArray[k++];
                setPixel(xx, yy, px);
            }
    }
    public void setSample(int x, int y, int b, int s) {
        sampleModel.setSample(x - minX, y - minY, b, s, dataBuffer);
    }
    public void setRect(Raster src) {
        for (int y = 0; y < src.getHeight(); y++)
            for (int x = 0; x < src.getWidth(); x++)
                setDataElements(x + src.getMinX(), y + src.getMinY(), src.getDataElements(x, y, null));
    }
    public void setRect(int dx, int dy, Raster src) {
        for (int y = 0; y < src.getHeight(); y++)
            for (int x = 0; x < src.getWidth(); x++)
                setDataElements(x + dx, y + dy, src.getDataElements(x, y, null));
    }
    public WritableRaster createWritableChild(int x, int y, int w, int h, int x0, int y0, int[] bands) {
        return this;
    }
    public float[] getPixel(int x, int y, float[] fArray) {
        float[] f = (fArray != null) ? fArray : new float[numBands];
        for (int b = 0; b < numBands; b++) f[b] = getSample(x, y, b);
        return f;
    }
    public void setPixel(int x, int y, float[] fArray) {
        for (int b = 0; b < numBands && b < fArray.length; b++) setSample(x, y, b, (int) fArray[b]);
    }
    public int[] getSamples(int x, int y, int w, int h, int b, int[] iArray) {
        int[] out = (iArray != null) ? iArray : new int[w * h];
        int k = 0;
        for (int yy = y; yy < y + h; yy++) for (int xx = x; xx < x + w; xx++) out[k++] = getSample(xx, yy, b);
        return out;
    }
    public float[] getSamples(int x, int y, int w, int h, int b, float[] fArray) {
        float[] out = (fArray != null) ? fArray : new float[w * h];
        int k = 0;
        for (int yy = y; yy < y + h; yy++) for (int xx = x; xx < x + w; xx++) out[k++] = getSample(xx, yy, b);
        return out;
    }
    public void setSamples(int x, int y, int w, int h, int b, int[] iArray) {
        int k = 0;
        for (int yy = y; yy < y + h; yy++) for (int xx = x; xx < x + w; xx++) setSample(xx, yy, b, iArray[k++]);
    }
    public WritableRaster getWritableParent() { return null; }
}
