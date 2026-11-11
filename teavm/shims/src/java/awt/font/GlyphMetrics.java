package java.awt.font;
import java.awt.geom.Rectangle2D;
/** Minimal java.awt.font.GlyphMetrics. */
public class GlyphMetrics {
    private final float advanceX, advanceY;
    private final Rectangle2D bounds;
    private final byte type;
    public GlyphMetrics(boolean horizontal, float advanceX, float advanceY, Rectangle2D bounds, byte type) {
        this.advanceX = advanceX; this.advanceY = advanceY; this.bounds = bounds; this.type = type;
    }
    public float getAdvanceX() { return advanceX; }
    public float getAdvanceY() { return advanceY; }
    public Rectangle2D getBounds2D() { return bounds; }
    public int getType() { return type; }
    public float getLSB() { return 0; }
    public float getRSB() { return 0; }
    public boolean isWhitespace() { return false; }
    public boolean isStandard() { return true; }
    public boolean isCombining() { return false; }
    public boolean isComponent() { return false; }
    public boolean isLigature() { return false; }
    public boolean isMultiCell() { return false; }
}
