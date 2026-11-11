package java.awt;
/** Minimal java.awt.Font: metrics are stubs (no real font rasterization in TeaVM).
 * Fields mirror real JDK: {@code size} is int, {@code pointSize} is float
 * (see FN272 follow-up #3027: the old single {@code float size} field made
 * TeaVM emit an f32 where Audiveris passes the inherited field to an
 * int-parameter method, and Node rejected the module). */
public class Font {
    public static final int PLAIN = 0;
    public static final int BOLD = 1;
    public static final int ITALIC = 2;
    public static final int TRUETYPE_FONT = 0;
    public static final int TYPE1_FONT = 1;
    protected String name;
    protected int style;
    protected int size;
    protected float pointSize;
    public Font(String name, int style, int size) {
        this.name = name == null ? "Dialog" : name;
        this.style = style; this.size = size; this.pointSize = size;
    }
    public Font(String name, int style, float size) {
        this.name = name == null ? "Dialog" : name;
        this.style = style; this.size = (int) size; this.pointSize = size;
    }
    public String getName() { return name; }
    public String getFamily() { return name; }
    public String getFontName() { return name; }
    public int getStyle() { return style; }
    public int getSize() { return size; }
    public float getSize2D() { return pointSize; }
    public boolean isPlain() { return style == PLAIN; }
    public boolean isBold() { return (style & BOLD) != 0; }
    public boolean isItalic() { return (style & ITALIC) != 0; }
    public Font deriveFont(int style) { return new Font(name, style, pointSize); }
    public Font deriveFont(float size) { return new Font(name, style, size); }
    public Font deriveFont(int style, float size) { return new Font(name, style, size); }
    public static Font decode(String str) { return new Font("Dialog", PLAIN, 12); }
    public static Font createFont(int fontFormat, java.io.InputStream in) {
        return new Font("Dialog", PLAIN, 12);
    }
    public static Font createFont(int fontFormat, java.io.File f) {
        return new Font("Dialog", PLAIN, 12);
    }
    public java.awt.font.FontRenderContext getFontRenderContext() {
        return new java.awt.font.FontRenderContext(null, false, false);
    }
    @Override public boolean equals(Object o) {
        if (o instanceof Font f) return name.equals(f.name) && style == f.style && size == f.size && pointSize == f.pointSize;
        return false;
    }
    @Override public int hashCode() { return name.hashCode() * 31 + style * 7 + size; }
    @Override public String toString() { return name + " style=" + style + " size=" + size; }
    public Font(Font font) { this(font.name, font.style, font.pointSize); }
    public Font deriveFont(java.awt.geom.AffineTransform trans) { return this; }
    // §23: used to return null; OmrFont.computeSize dereferences the result
    // (glyphVector.getVisualBounds()), which trapped on the first OCR word.
    public java.awt.font.GlyphVector createGlyphVector(java.awt.font.FontRenderContext frc, String str) { return new java.awt.font.SimpleGlyphVector(this, frc, str); }
    public java.awt.font.GlyphVector createGlyphVector(java.awt.font.FontRenderContext frc, char[] chars) { return new java.awt.font.SimpleGlyphVector(this, frc, new String(chars)); }
    public java.awt.font.GlyphVector createGlyphVector(java.awt.font.FontRenderContext frc, java.text.CharacterIterator ci) {
        StringBuilder sb = new StringBuilder();
        for (char c = ci.first(); c != java.text.CharacterIterator.DONE; c = ci.next()) sb.append(c);
        return new java.awt.font.SimpleGlyphVector(this, frc, sb.toString());
    }
}
