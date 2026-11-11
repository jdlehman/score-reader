package java.awt.image;
public interface ImageConsumer {
    int RANDOMPIXELORDER = 1, TOPDOWNLEFTRIGHT = 2, COMPLETESCANLINES = 4, SINGLEPASS = 8, SINGLEFRAME = 16, IMAGEERROR = 32, SINGLEFRAMEDONE = 64, STATICIMAGEDONE = 128, IMAGEABORTED = 256;
    void setDimensions(int w, int h);
    void setProperties(java.util.Hashtable<?, ?> props);
    void setColorModel(ColorModel model);
    void setHints(int hints);
    void setPixels(int x, int y, int w, int h, ColorModel model, byte[] pixels, int off, int scansize);
    void setPixels(int x, int y, int w, int h, ColorModel model, int[] pixels, int off, int scansize);
    void imageComplete(int status);
}
