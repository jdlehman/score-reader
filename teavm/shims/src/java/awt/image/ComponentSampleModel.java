package java.awt.image;
/** Minimal ComponentSampleModel for interleaved/banded byte data. */
public class ComponentSampleModel extends SampleModel {
    protected int[] bandOffsets;
    protected int[] bankIndices;
    protected int pixelStride;
    protected int scanlineStride;
    public ComponentSampleModel(int dataType, int w, int h, int pixelStride, int scanlineStride,
                                int[] bandOffsets) {
        super(dataType, w, h, bandOffsets.length);
        this.pixelStride = pixelStride; this.scanlineStride = scanlineStride;
        this.bandOffsets = bandOffsets.clone();
        bankIndices = new int[bandOffsets.length];
    }
    public ComponentSampleModel(int dataType, int w, int h, int pixelStride, int scanlineStride,
                                int[] bankIndices, int[] bandOffsets) {
        super(dataType, w, h, bandOffsets.length);
        this.pixelStride = pixelStride; this.scanlineStride = scanlineStride;
        this.bandOffsets = bandOffsets.clone();
        this.bankIndices = bankIndices.clone();
    }
    public int getPixelStride() { return pixelStride; }
    public int getScanlineStride() { return scanlineStride; }
    public int[] getBandOffsets() { return bandOffsets.clone(); }
    public int[] getBankIndices() { return bankIndices.clone(); }
    @Override public int getNumDataElements() { return numBands; }
    @Override public DataBuffer createDataBuffer() {
        if (dataType == DataBuffer.TYPE_INT) return new DataBufferInt(scanlineStride * height);
        return new DataBufferByte(scanlineStride * height);
    }
    @Override public SampleModel createCompatibleSampleModel(int w, int h) {
        return new ComponentSampleModel(dataType, w, h, pixelStride, pixelStride * w, bandOffsets);
    }
    @Override public SampleModel createSubsetSampleModel(int[] bands) {
        int[] offs = new int[bands.length];
        for (int i = 0; i < bands.length; i++) offs[i] = bandOffsets[bands[i]];
        return new ComponentSampleModel(dataType, width, height, pixelStride, scanlineStride, offs);
    }
    private int idx(int x, int y, int b, DataBuffer db) {
        return y * scanlineStride + x * pixelStride + bandOffsets[b];
    }
    private int getElem(DataBuffer db, int i) {
        if (db instanceof DataBufferInt di) return di.getElem(i);
        return ((DataBufferByte) db).getElem(i);
    }
    private void setElem(DataBuffer db, int i, int v) {
        if (db instanceof DataBufferInt di) di.setElem(i, v);
        else ((DataBufferByte) db).setElem(i, v);
    }
    @Override public Object getDataElements(int x, int y, Object obj, DataBuffer db) {
        if (dataType == DataBuffer.TYPE_INT) {
            int[] out = (obj instanceof int[] a) ? a : new int[numBands];
            for (int b = 0; b < numBands; b++) out[b] = getElem(db, idx(x, y, b, db));
            return out;
        }
        byte[] out = (obj instanceof byte[] b) ? b : new byte[numBands];
        for (int b = 0; b < numBands; b++) out[b] = (byte) getElem(db, idx(x, y, b, db));
        return out;
    }
    @Override public int[] getPixel(int x, int y, int[] iArray, DataBuffer db) {
        int[] out = iArray == null ? new int[numBands] : iArray;
        for (int b = 0; b < numBands; b++) out[b] = getElem(db, idx(x, y, b, db));
        return out;
    }
    @Override public int getSample(int x, int y, int b, DataBuffer db) {
        return getElem(db, idx(x, y, b, db));
    }
    @Override public void setDataElements(int x, int y, Object obj, DataBuffer db) {
        if (dataType == DataBuffer.TYPE_INT) {
            int[] in = (int[]) obj;
            for (int b = 0; b < numBands; b++) setElem(db, idx(x, y, b, db), in[b]);
            return;
        }
        byte[] in = (byte[]) obj;
        for (int b = 0; b < numBands; b++) setElem(db, idx(x, y, b, db), in[b]);
    }
    @Override public void setPixel(int x, int y, int[] iArray, DataBuffer db) {
        for (int b = 0; b < numBands; b++) setElem(db, idx(x, y, b, db), iArray[b]);
    }
    @Override public void setSample(int x, int y, int b, int s, DataBuffer db) {
        setElem(db, idx(x, y, b, db), s);
    }
}
