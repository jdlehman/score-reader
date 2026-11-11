package java.awt;
public abstract class GraphicsConfiguration {
    public abstract java.awt.image.BufferedImage createCompatibleImage(int w, int h);
    public abstract java.awt.image.ColorModel getColorModel();
    public abstract java.awt.image.ColorModel getColorModel(int transparency);
    public abstract java.awt.geom.AffineTransform getDefaultTransform();
    public abstract java.awt.geom.AffineTransform getNormalizingTransform();
    public GraphicsDevice getDevice() { return null; }
    public java.awt.Rectangle getBounds() { return new java.awt.Rectangle(0, 0, 0, 0); }
}
