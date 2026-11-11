package javax.imageio;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.util.Iterator;
/** Minimal javax.imageio.ImageReader. */
public abstract class ImageReader {
    protected ImageReader() {}
    public abstract int getNumImages(boolean allowSearch) throws IOException;
    public abstract int getWidth(int imageIndex) throws IOException;
    public abstract int getHeight(int imageIndex) throws IOException;
    public abstract BufferedImage read(int imageIndex) throws IOException;
    public abstract BufferedImage read(int imageIndex, ImageReadParam param) throws IOException;
    public abstract Iterator<ImageTypeSpecifier> getImageTypes(int imageIndex) throws IOException;
    public void setInput(Object input) {}
    public void setInput(Object input, boolean seekForwardOnly) {}
    public void setInput(Object input, boolean seekForwardOnly, boolean ignoreMetadata) {}
    public Object getInput() { return null; }
    public void dispose() {}
    public void reset() {}
    public ImageReadParam getDefaultReadParam() { return new ImageReadParam(); }
    public javax.imageio.metadata.IIOMetadata getImageMetadata(int imageIndex) throws java.io.IOException { return null; }
    public boolean canReadRaster() { return false; }
}
