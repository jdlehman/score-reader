package java.awt.font;
import java.awt.Font;
import java.awt.Shape;
import java.awt.geom.AffineTransform;
import java.awt.geom.Point2D;
import java.awt.geom.Rectangle2D;
/**
 * Minimal concrete GlyphVector for the TeaVM shim.
 * §23: Font.createGlyphVector used to return null, and OmrFont.computeSize
 * dereferences the result (glyphVector.getVisualBounds()) — the first 'W'
 * row of any OCR text trapped with a null-pointer dereference in
 * BrowserOCR.parse. Visual bounds reuse the TextLayout model exactly
 * (Bravura composed advance when applicable, else 0.5 * size per char;
 * ascent 0.8 * size, descent 0.2 * size), so computeSize's fitted point
 * size is consistent with TextLayout-based measurement elsewhere.
 * Per-glyph positions are evenly spaced over the advance.
 */
public class SimpleGlyphVector extends GlyphVector {
    private final Font font;
    private final FontRenderContext frc;
    private final String text;
    private final float[] positions;

    public SimpleGlyphVector(Font font, FontRenderContext frc, String str) {
        this.font = font;
        this.frc = frc;
        this.text = (str == null) ? "" : str;
        float advance = new TextLayout(this.text, font, frc).getAdvance();
        float each = (text.isEmpty()) ? 0 : advance / text.length();
        this.positions = new float[text.length() * 2 + 2];
        for (int i = 0; i <= text.length(); i++) {
            positions[2 * i] = i * each;
            positions[2 * i + 1] = 0;
        }
    }

    @Override public Font getFont() { return font; }
    @Override public FontRenderContext getFontRenderContext() { return frc; }
    @Override public int getNumGlyphs() { return text.length(); }
    @Override public int getGlyphCode(int i) { return text.charAt(i); }
    @Override public int[] getGlyphCodes(int begin, int count, int[] codes) {
        if (codes == null) codes = new int[count];
        for (int i = 0; i < count; i++) codes[i] = text.charAt(begin + i);
        return codes;
    }
    @Override public Shape getOutline() { return new TextLayout(text, font, frc).getOutline(null); }
    @Override public Shape getOutline(float x, float y) {
        return new TextLayout(text, font, frc).getOutline(AffineTransform.getTranslateInstance(x, y));
    }
    @Override public Shape getGlyphOutline(int i) { return getGlyphOutline(i, 0, 0); }
    @Override public Shape getGlyphOutline(int i, float x, float y) {
        float each = (text.isEmpty()) ? 0 : new TextLayout(text, font, frc).getAdvance() / text.length();
        Rectangle2D b = getGlyphVisualBounds(i);
        java.awt.geom.Path2D.Double p = new java.awt.geom.Path2D.Double();
        p.moveTo(b.getX() + x, b.getY() + y);
        p.lineTo(b.getMaxX() + x, b.getY() + y);
        p.lineTo(b.getMaxX() + x, b.getMaxY() + y);
        p.lineTo(b.getX() + x, b.getMaxY() + y);
        p.closePath();
        return p;
    }
    @Override public Rectangle2D getOutlineBounds() { return getVisualBounds(); }
    @Override public Rectangle2D getVisualBounds() {
        return new TextLayout(text, font, frc).getBounds();
    }
    @Override public Rectangle2D getGlyphVisualBounds(int i) {
        float size = font.getSize2D();
        float each = (text.isEmpty()) ? 0 : new TextLayout(text, font, frc).getAdvance() / text.length();
        return new Rectangle2D.Double(i * each, -size * 0.8f, each, size);
    }
    @Override public Point2D getGlyphPosition(int i) {
        return new Point2D.Float(positions[2 * i], positions[2 * i + 1]);
    }
    @Override public void setGlyphPosition(int i, Point2D pos) {
        positions[2 * i] = (float) pos.getX();
        positions[2 * i + 1] = (float) pos.getY();
    }
    @Override public AffineTransform getGlyphTransform(int i) { return new AffineTransform(); }
    @Override public void setGlyphTransform(int i, AffineTransform t) {}
    @Override public GlyphMetrics getGlyphMetrics(int i) {
        float size = font.getSize2D();
        float each = (text.isEmpty()) ? 0 : new TextLayout(text, font, frc).getAdvance() / text.length();
        return new GlyphMetrics(true, each, 0,
                new Rectangle2D.Double(0, -size * 0.8f, each, size), (byte) 0);
    }
    @Override public int getLayoutFlags() { return 0; }
    @Override public float[] getGlyphPositions(int begin, int count, float[] out) {
        if (out == null) out = new float[count * 2 + 2];
        System.arraycopy(positions, begin * 2, out, 0, count * 2 + 2);
        return out;
    }
    @Override public void performDefaultLayout() {}
}
