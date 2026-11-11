package java.awt;
public interface Paint {
    PaintContext createContext(java.awt.image.ColorModel cm, Rectangle deviceBounds,
                               java.awt.geom.Rectangle2D userBounds, java.awt.geom.AffineTransform xform,
                               RenderingHints hints);
    int getTransparency();
}
