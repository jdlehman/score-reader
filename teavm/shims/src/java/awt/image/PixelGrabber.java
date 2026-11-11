package java.awt.image;
import java.awt.Image;
/** Minimal java.awt.image.PixelGrabber. */
public class PixelGrabber implements ImageConsumer {
    protected Image image;
    protected int dstX, dstY, width, height;
    protected int[] pixels;
    protected boolean grabbing;
    public PixelGrabber(Image img, int x, int y, int w, int h, int[] pix, int off, int scansize) {
        image = img; dstX = x; dstY = y; width = w; height = h; pixels = pix;
    }
    public PixelGrabber(java.awt.image.ImageProducer ip, int x, int y, int w, int h, int[] pix, int off, int scansize) {
        dstX = x; dstY = y; width = w; height = h; pixels = pix;
    }
    public PixelGrabber(Image img, int x, int y, int w, int h, boolean grabPixels) {
        image = img; dstX = x; dstY = y; width = w; height = h;
    }
    public synchronized ColorModel getColorModel() { return null; }
    public synchronized boolean grabPixels() throws InterruptedException { return false; }
    public synchronized boolean grabPixels(long ms) throws InterruptedException { return false; }
    public synchronized int getStatus() { return 0; }
    public synchronized int getWidth() { return width; }
    public synchronized int getHeight() { return height; }
    public synchronized Object getPixels() { return pixels; }
    public synchronized int getPixel(int x, int y) { return 0; }
    public synchronized void abortGrabbing() {}
    public synchronized void startGrabbing() {}
    public void setDimensions(int width, int height) {}
    public void setProperties(java.util.Hashtable<?, ?> props) {}
    public void setColorModel(ColorModel model) {}
    public void setHints(int hintflags) {}
    public void setPixels(int x, int y, int w, int h, ColorModel model, byte[] pixels, int off, int scansize) {}
    public void setPixels(int x, int y, int w, int h, ColorModel model, int[] pixels, int off, int scansize) {}
    public void imageComplete(int status) {}
}
