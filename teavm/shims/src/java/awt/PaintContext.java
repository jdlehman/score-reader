package java.awt;
public interface PaintContext {
    void dispose();
    java.awt.image.ColorModel getColorModel();
    java.awt.image.Raster getRaster(int x, int y, int w, int h);
}
