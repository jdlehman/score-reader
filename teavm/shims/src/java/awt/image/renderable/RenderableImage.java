package java.awt.image.renderable;
import java.awt.image.RenderedImage;
import java.util.Vector;
public interface RenderableImage {
    Vector<RenderableImage> getSources();
    Object getProperty(String name);
    String[] getPropertyNames();
    boolean isDynamic();
    float getWidth();
    float getHeight();
    float getMinX();
    float getMinY();
    RenderedImage createScaledRendering(int w, int h, java.awt.image.RenderingHints hints);
    RenderedImage createDefaultRendering();
    RenderedImage createRendering(RenderContext renderContext);
}
