package javax.imageio;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.InputStream;
import java.io.OutputStream;
import javax.imageio.stream.ImageOutputStream;
import java.util.Collections;
import java.util.Iterator;
/** Minimal javax.imageio.ImageIO: reading is unsupported in TeaVM (images come from JS). */
public final class ImageIO {
    private ImageIO() {}
    public static BufferedImage read(File input) { throw new UnsupportedOperationException("ImageIO.read not available in TeaVM"); }
    public static BufferedImage read(InputStream input) { throw new UnsupportedOperationException("ImageIO.read not available in TeaVM"); }
    public static BufferedImage read(java.net.URL input) { throw new UnsupportedOperationException("ImageIO.read not available in TeaVM"); }
    public static BufferedImage read(javax.imageio.stream.ImageInputStream stream) { throw new UnsupportedOperationException("ImageIO.read not available in TeaVM"); }
    public static boolean write(BufferedImage im, String formatName, File output) { throw new UnsupportedOperationException("ImageIO.write not available in TeaVM"); }
    public static boolean write(BufferedImage im, String formatName, OutputStream output) { throw new UnsupportedOperationException("ImageIO.write not available in TeaVM"); }
    public static boolean write(BufferedImage im, String formatName, ImageOutputStream output) { throw new UnsupportedOperationException("ImageIO.write not available in TeaVM"); }
    public static Iterator<ImageReader> getImageReadersByFormatName(String formatName) { return Collections.emptyIterator(); }
    public static Iterator<ImageReader> getImageReadersBySuffix(String suffix) { return Collections.emptyIterator(); }
    public static Iterator<ImageReader> getImageReadersByMIMEType(String mime) { return Collections.emptyIterator(); }
    public static Iterator<ImageWriter> getImageWritersByFormatName(String formatName) { return Collections.emptyIterator(); }
    public static String[] getReaderFormatNames() { return new String[0]; }
    public static String[] getWriterFormatNames() { return new String[0]; }
    public static ImageReader getImageReader(javax.imageio.stream.ImageInputStream stream) { return null; }
    public static javax.imageio.stream.ImageInputStream createImageInputStream(Object input) { return null; }
    public static javax.imageio.stream.ImageOutputStream createImageOutputStream(Object input) { return null; }
    public static Iterator<ImageReader> getImageReaders(Object input) { return Collections.emptyIterator(); }
    public static boolean write(java.awt.image.RenderedImage im, String formatName, File output) { return false; }
    public static boolean write(java.awt.image.RenderedImage im, String formatName, OutputStream output) { return false; }
}
