package java.awt;
public interface CompositeContext {
    void dispose();
    void compose(java.awt.image.Raster src, java.awt.image.Raster dstIn, java.awt.image.WritableRaster dstOut);
}
