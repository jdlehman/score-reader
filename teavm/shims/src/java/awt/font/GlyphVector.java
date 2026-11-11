package java.awt.font;
import java.awt.Font;
import java.awt.Shape;
import java.awt.geom.Rectangle2D;
/** Minimal java.awt.font.GlyphVector (stub). */
public abstract class GlyphVector implements Cloneable {
    public abstract Font getFont();
    public abstract FontRenderContext getFontRenderContext();
    public abstract int getNumGlyphs();
    public abstract int getGlyphCode(int i);
    public abstract int[] getGlyphCodes(int begin, int count, int[] codes);
    public abstract Shape getOutline();
    public abstract Shape getOutline(float x, float y);
    public abstract Shape getGlyphOutline(int i);
    public abstract Shape getGlyphOutline(int i, float x, float y);
    public abstract Rectangle2D getOutlineBounds();
    public abstract Rectangle2D getVisualBounds();
    public abstract Rectangle2D getGlyphVisualBounds(int i);
    public java.awt.Rectangle getPixelBounds(FontRenderContext renderContext, float x, float y) {
        Rectangle2D b = getVisualBounds();
        return new java.awt.Rectangle((int) (x + b.getX()), (int) (y + b.getY()), (int) b.getWidth(), (int) b.getHeight());
    }
    public abstract java.awt.geom.Point2D getGlyphPosition(int i);
    public abstract void setGlyphPosition(int i, java.awt.geom.Point2D pos);
    public abstract java.awt.geom.AffineTransform getGlyphTransform(int i);
    public abstract void setGlyphTransform(int i, java.awt.geom.AffineTransform t);
    public abstract GlyphMetrics getGlyphMetrics(int i);
    public abstract int getLayoutFlags();
    public abstract float[] getGlyphPositions(int begin, int count, float[] out);
    public abstract void performDefaultLayout();
}
