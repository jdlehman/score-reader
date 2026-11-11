package java.awt;
/** Minimal java.awt.FontMetrics (correct package -- the JDK class lives in
 *  java.awt, not java.awt.font). Stub metrics: 8px advance.
 *  Deliberately concrete (the JDK class is abstract) so stubs can
 *  instantiate it directly. */
public class FontMetrics implements java.io.Serializable {
    protected Font font;
    public FontMetrics(Font font) { this.font = font; }
    public Font getFont() { return font; }
    public int getHeight() { return 12; }
    public int getAscent() { return 10; }
    public int getDescent() { return 2; }
    public int getLeading() { return 0; }
    public int getMaxAscent() { return 10; }
    public int getMaxDescent() { return 2; }
    public int getMaxAdvance() { return 8; }
    public int charWidth(int ch) { return 8; }
    public int charWidth(char ch) { return 8; }
    public int stringWidth(String str) { return (str == null) ? 0 : str.length() * 8; }
    public int charsWidth(char[] data, int off, int len) { return len * 8; }
    public int bytesWidth(byte[] data, int off, int len) { return len * 8; }
    public int[] getWidths() { int[] w = new int[256]; java.util.Arrays.fill(w, 8); return w; }
    public boolean hasUniformLineMetrics() { return true; }
    public java.awt.geom.Rectangle2D getStringBounds(String str, java.awt.Graphics context) {
        return new java.awt.geom.Rectangle2D.Double(0, 0, stringWidth(str), getHeight());
    }
    public java.awt.geom.Rectangle2D getStringBounds(char[] chars, int beginIndex, int limit, java.awt.Graphics context) {
        return new java.awt.geom.Rectangle2D.Double(0, 0, (limit - beginIndex) * 8, getHeight());
    }
    public java.awt.geom.Rectangle2D getStringBounds(java.text.CharacterIterator ci, int beginIndex, int limit, java.awt.Graphics context) {
        return new java.awt.geom.Rectangle2D.Double(0, 0, (limit - beginIndex) * 8, getHeight());
    }
}
