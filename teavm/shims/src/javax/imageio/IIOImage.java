package javax.imageio;
import java.awt.image.BufferedImage;
import java.awt.image.Raster;
/** Minimal javax.imageio.IIOImage. */
public class IIOImage {
    private BufferedImage image;
    private Raster raster;
    public IIOImage(BufferedImage image, java.util.List<? extends BufferedImage> thumbnails, IIOMetadata metadata) { this.image = image; }
    public IIOImage(Raster raster, java.util.List<? extends BufferedImage> thumbnails, IIOMetadata metadata) { this.raster = raster; }
    public IIOImage(java.awt.image.RenderedImage image, java.util.List<? extends BufferedImage> thumbnails, javax.imageio.metadata.IIOMetadata metadata) {
        if (image instanceof BufferedImage) this.image = (BufferedImage) image;
        else if (image instanceof Raster) this.raster = (Raster) image;
    }
    public BufferedImage getRenderedImage() { return image; }
    public Raster getRaster() { return raster; }
    public void setRenderedImage(BufferedImage image) { this.image = image; }
    public void setRaster(Raster raster) { this.raster = raster; }
}
