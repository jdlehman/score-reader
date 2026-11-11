package java.awt.image;
import java.awt.Rectangle;
import java.awt.geom.Point2D;
import java.awt.geom.Rectangle2D;
public interface BufferedImageOp {
    BufferedImage filter(BufferedImage src, BufferedImage dest);
    Rectangle2D getBounds2D(BufferedImage src);
    BufferedImage createCompatibleDestImage(BufferedImage src, ColorModel destCM);
    Point2D getPoint2D(Point2D srcPt, Point2D dstPt);
    RenderingHints getRenderingHints();
}
