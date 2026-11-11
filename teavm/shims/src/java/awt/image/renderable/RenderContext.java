package java.awt.image.renderable;
public class RenderContext implements Cloneable {
    public RenderContext(java.awt.geom.AffineTransform usr2dev) {}
    public RenderContext(java.awt.geom.AffineTransform usr2dev, java.awt.Shape aoi) {}
    public RenderContext(java.awt.geom.AffineTransform usr2dev, java.awt.Shape aoi, java.awt.image.RenderingHints hints) {}
    public java.awt.geom.AffineTransform getTransform() { return new java.awt.geom.AffineTransform(); }
    public void setTransform(java.awt.geom.AffineTransform t) {}
    public java.awt.Shape getAreaOfInterest() { return null; }
    public void setAreaOfInterest(java.awt.Shape s) {}
    public java.awt.image.RenderingHints getRenderingHints() { return null; }
    public void setRenderingHints(java.awt.image.RenderingHints h) {}
    @Override public Object clone() { return new RenderContext(new java.awt.geom.AffineTransform()); }
}
