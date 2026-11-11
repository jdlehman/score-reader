package javax.imageio;
import java.awt.image.BufferedImage;
import java.awt.image.ColorModel;
import java.awt.image.SampleModel;
/** Minimal javax.imageio.ImageTypeSpecifier. */
public class ImageTypeSpecifier {
    private final ColorModel cm;
    private final SampleModel sm;
    public ImageTypeSpecifier(ColorModel cm, SampleModel sm) { this.cm = cm; this.sm = sm; }
    public static ImageTypeSpecifier createFromBufferedImageType(int type) {
        BufferedImage bi = new BufferedImage(1, 1, type);
        return new ImageTypeSpecifier(bi.getColorModel(), bi.getRaster().getSampleModel());
    }
    public ColorModel getColorModel() { return cm; }
    public SampleModel getSampleModel() { return sm; }
    public BufferedImage createBufferedImage(int w, int h) { return new BufferedImage(cm, new java.awt.image.WritableRaster(sm, sm.createDataBuffer(), new java.awt.Point(0, 0)), false, null); }
}
