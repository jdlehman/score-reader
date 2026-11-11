package javax.imageio;
import java.awt.Rectangle;
import java.awt.image.BufferedImage;
/** Minimal javax.imageio.ImageReadParam. */
public class ImageReadParam {
    public void setSourceRegion(Rectangle region) {}
    public Rectangle getSourceRegion() { return null; }
    public void setSourceSubsampling(int x, int y, int xOff, int yOff) {}
    public void setDestination(BufferedImage dest) {}
    public BufferedImage getDestination() { return null; }
}
