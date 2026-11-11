package javax.imageio;
import java.io.IOException;
/** Minimal javax.imageio.ImageWriter. */
public abstract class ImageWriter {
    public abstract void setOutput(Object output);
    public abstract void write(IIOImage image) throws IOException;
    public void write(java.awt.image.RenderedImage image) throws IOException {}
    public void write(javax.imageio.metadata.IIOMetadata streamMetadata, IIOImage image, ImageWriteParam param) throws IOException {}
    public ImageWriteParam getDefaultWriteParam() { return null; }
    public javax.imageio.metadata.IIOMetadata getDefaultImageMetadata(ImageTypeSpecifier imageType, ImageWriteParam param) { return null; }
    public javax.imageio.metadata.IIOMetadata getDefaultStreamMetadata(ImageWriteParam param) { return null; }
    public void dispose() {}
}
