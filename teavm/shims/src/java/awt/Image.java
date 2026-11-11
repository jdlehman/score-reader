package java.awt;
import java.awt.image.ImageObserver;
/** Minimal java.awt.Image. */
public abstract class Image {
    public static final int SCALE_DEFAULT = 1;
    public static final int SCALE_FAST = 2;
    public static final int SCALE_SMOOTH = 4;
    public static final int SCALE_REPLICATE = 8;
    public static final int SCALE_AREA_AVERAGING = 16;
    public abstract int getWidth(ImageObserver observer);
    public abstract int getHeight(ImageObserver observer);
    public abstract java.awt.image.ImageProducer getSource();
    public abstract Graphics getGraphics();
    public abstract Object getProperty(String name, ImageObserver observer);
    public int getWidth() { return getWidth(null); }
    public int getHeight() { return getHeight(null); }
    public Image getScaledInstance(int w, int h, int hints) { throw new UnsupportedOperationException(); }
    public void flush() {}
}
