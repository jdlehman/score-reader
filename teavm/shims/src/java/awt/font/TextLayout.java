package java.awt.font;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.Shape;
import java.awt.geom.AffineTransform;
import java.awt.geom.Rectangle2D;
/** Minimal java.awt.font.TextLayout (stub: no real glyph layout; bounds from string length).
 * §19: for the Bravura music font the bounds/advance come from pre-rendered
 * per-codepoint metrics (BravuraMetrics, dumped on desktop Java with the
 * real Bravura font), composed over the string's code points — exact on
 * desktop (22 multi-code strings compose with 0.0 error). Any other font,
 * or a code point not in the table, falls back to the stub values below.
 * getAscent/getDescent stay stub values: no pipeline caller uses them
 * (verified by grep over the Audiveris sources); getBounds() no longer
 * derives from them for Bravura strings. TextLayout.draw stays a no-op:
 * painting is not needed in the pipeline (symbol images stay blank;
 * the centroid is fixed separately by the patched ShapeSymbol). */
public class TextLayout implements Cloneable {
    private final String text;
    private final Font font;
    private final FontRenderContext frc;
    public TextLayout(String text, Font font, FontRenderContext frc) {
        this.text = text == null ? "" : text;
        this.font = font == null ? new Font("Dialog", Font.PLAIN, 12) : font;
        this.frc = frc;
    }
    public TextLayout(String text, java.util.Map<? extends java.text.AttributedCharacterIterator.Attribute, ?> attrs, FontRenderContext frc) {
        this(text, (Font) attrs.get(java.awt.font.TextAttribute.FONT), frc);
    }
    public String getText() { return text; }
    public Font getFont() { return font; }
    /** Real Bravura advance when the whole string is covered by the table, else stub. */
    public float getAdvance() {
        double adv = composedAdvance();
        if (adv >= 0) return (float) adv;
        return text.length() * font.getSize() * 0.5f;
    }
    public float getVisibleAdvance() { return getAdvance(); }
    public float getAscent() { return font.getSize() * 0.8f; }
    public float getDescent() { return font.getSize() * 0.2f; }
    public float getLeading() { return 0; }
    public Rectangle2D getBounds() {
        double[] b = composedBounds();
        if (b != null) return new Rectangle2D.Double(b[0], b[1], b[2], b[3]);
        return new Rectangle2D.Double(0, -getAscent(), getAdvance(), getAscent() + getDescent());
    }
    public Rectangle2D getPixelBounds(FontRenderContext frc, float x, float y) {
        Rectangle2D b = getBounds();
        return new Rectangle2D.Double(b.getX() + x, b.getY() + y, b.getWidth(), b.getHeight());
    }
    public Shape getOutline(AffineTransform tx) {
        Rectangle2D b = getBounds();
        java.awt.geom.Path2D.Double p = new java.awt.geom.Path2D.Double();
        p.moveTo(b.getX(), b.getY());
        p.lineTo(b.getMaxX(), b.getY());
        p.lineTo(b.getMaxX(), b.getMaxY());
        p.lineTo(b.getX(), b.getMaxY());
        p.closePath();
        if (tx != null) p.transform(tx);
        return p;
    }
    public void draw(Graphics2D g, float x, float y) {}
    public boolean isLeftToRight() { return true; }
    public boolean isVertical() { return false; }
    public int getCharacterCount() { return text.length(); }
    /**
     * §19: composed Bravura advance in pixels, or -1 when the table does
     * not cover this font/text. Composition: glyphs are placed left to
     * right, each at the cumulative advance of the previous ones; the
     * advance is the sum of per-codepoint advances scaled by the font's
     * point size (getSize2D, the size the real TextLayout scales with).
     */
    private double composedAdvance() {
        if (!"Bravura".equals(font.getName()) || text.isEmpty()) return -1;
        double size = font.getSize2D();
        double adv = 0;
        int i = 0;
        while (i < text.length()) {
            int cp = text.codePointAt(i);
            double[] m = BravuraMetrics.get(cp);
            if (m == null) return -1;
            adv += m[0] * size;
            i += Character.charCount(cp);
        }
        return adv;
    }
    /**
     * §19: composed Bravura bounds {x, y, width, height} in pixels, or
     * null when the table does not cover this font/text. Each glyph's
     * unit bounds are scaled by point size and translated by the
     * cumulative advance; the result is the union over glyphs with
     * non-empty bounds (a space contributes advance only). An all-space
     * string has the empty bounds the real layout reports.
     */
    private double[] composedBounds() {
        if (!"Bravura".equals(font.getName()) || text.isEmpty()) return null;
        double size = font.getSize2D();
        double adv = 0;
        double x0 = Double.MAX_VALUE, y0 = Double.MAX_VALUE;
        double x1 = -Double.MAX_VALUE, y1 = -Double.MAX_VALUE;
        boolean any = false;
        int i = 0;
        while (i < text.length()) {
            int cp = text.codePointAt(i);
            double[] m = BravuraMetrics.get(cp);
            if (m == null) return null;
            double gx = adv + m[1] * size;
            double gy = m[2] * size;
            double gw = m[3] * size;
            double gh = m[4] * size;
            if (gw > 0 && gh > 0) {
                any = true;
                x0 = Math.min(x0, gx);
                y0 = Math.min(y0, gy);
                x1 = Math.max(x1, gx + gw);
                y1 = Math.max(y1, gy + gh);
            }
            adv += m[0] * size;
            i += Character.charCount(cp);
        }
        if (!any) return new double[] { 0, 0, 0, 0 };
        return new double[] { x0, y0, x1 - x0, y1 - y0 };
    }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
}
