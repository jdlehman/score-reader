package java.awt;
/** Minimal java.awt.Color. TeaVM's classlib only has BLACK/WHITE + ctors/getters;
 *  this shim adds the full constant set and decode(). If TeaVM prefers its own
 *  TColor, the missing fields are patched at the call sites instead. */
public class Color implements Paint {
    public static final Color WHITE = new Color(255, 255, 255);
    public static final Color BLACK = new Color(0, 0, 0);
    // §14: populateAllSymbols() pulls in the symbol painters, which use the
    // standard constants (NonDraggableSymbol.paint uses RED). JDK values.
    public static final Color RED = new Color(255, 0, 0);
    public static final Color GREEN = new Color(0, 255, 0);
    public static final Color BLUE = new Color(0, 0, 255);
    public static final Color YELLOW = new Color(255, 255, 0);
    public static final Color CYAN = new Color(0, 255, 255);
    public static final Color MAGENTA = new Color(255, 0, 255);
    public static final Color ORANGE = new Color(255, 200, 0);
    public static final Color PINK = new Color(255, 175, 175);
    public static final Color GRAY = new Color(128, 128, 128);
    public static final Color LIGHT_GRAY = new Color(192, 192, 192);
    public static final Color DARK_GRAY = new Color(64, 64, 64);
    private final int value;
    public Color(int r, int g, int b) { this(r, g, b, 255); }
    public Color(int r, int g, int b, int a) {
        value = ((a & 0xff) << 24) | ((r & 0xff) << 16) | ((g & 0xff) << 8) | (b & 0xff);
    }
    public Color(int rgb) { value = 0xff000000 | rgb; }
    public Color(int rgba, boolean hasAlpha) { value = hasAlpha ? rgba : (0xff000000 | rgba); }
    public Color(float r, float g, float b) { this((int) (r * 255), (int) (g * 255), (int) (b * 255)); }
    public Color(float r, float g, float b, float a) { this((int) (r * 255), (int) (g * 255), (int) (b * 255), (int) (a * 255)); }
    public int getRed() { return (value >> 16) & 0xff; }
    public int getGreen() { return (value >> 8) & 0xff; }
    public int getBlue() { return value & 0xff; }
    public int getAlpha() { return (value >> 24) & 0xff; }
    @Override public PaintContext createContext(java.awt.image.ColorModel cm, Rectangle deviceBounds,
            java.awt.geom.Rectangle2D userBounds, java.awt.geom.AffineTransform xform, RenderingHints hints) {
        return null;
    }
    @Override public int getTransparency() { return getAlpha() == 255 ? 1 : 3; }
    @Override public boolean equals(Object o) { return o instanceof Color c && value == c.value; }
    @Override public int hashCode() { return value; }
    @Override public String toString() { return "Color[r=" + getRed() + ",g=" + getGreen() + ",b=" + getBlue() + "]"; }
}
