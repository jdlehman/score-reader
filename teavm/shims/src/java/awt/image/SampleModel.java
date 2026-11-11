package java.awt.image;
/** Minimal java.awt.image.SampleModel. */
public abstract class SampleModel {
    protected int width, height, numBands, dataType;
    public SampleModel(int dataType, int w, int h, int numBands) {
        this.dataType = dataType; width = w; height = h; this.numBands = numBands;
    }
    public int getWidth() { return width; }
    public int getHeight() { return height; }
    public int getNumBands() { return numBands; }
    public int getDataType() { return dataType; }
    public abstract int getNumDataElements();
    public abstract DataBuffer createDataBuffer();
    public abstract SampleModel createCompatibleSampleModel(int w, int h);
    public abstract SampleModel createSubsetSampleModel(int[] bands);
    public abstract Object getDataElements(int x, int y, Object obj, DataBuffer db);
    public abstract int[] getPixel(int x, int y, int[] iArray, DataBuffer db);
    public abstract int getSample(int x, int y, int b, DataBuffer db);
    public abstract void setDataElements(int x, int y, Object obj, DataBuffer db);
    public abstract void setPixel(int x, int y, int[] iArray, DataBuffer db);
    public abstract void setSample(int x, int y, int b, int s, DataBuffer db);
}
