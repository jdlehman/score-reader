package java.awt;
/** Minimal java.awt.AlphaComposite. */
public final class AlphaComposite implements Composite {
    public static final int CLEAR = 1;
    public static final int SRC = 2;
    public static final int DST = 9;
    public static final int SRC_OVER = 3;
    public static final int DST_OVER = 4;
    public static final int SRC_IN = 5;
    public static final int DST_IN = 6;
    public static final int SRC_OUT = 7;
    public static final int DST_OUT = 8;
    public static final int SRC_ATOP = 10;
    public static final int DST_ATOP = 11;
    public static final int XOR = 12;
    public static final AlphaComposite Clear = new AlphaComposite(CLEAR, 1.0f);
    public static final AlphaComposite Src = new AlphaComposite(SRC, 1.0f);
    public static final AlphaComposite SrcOver = new AlphaComposite(SRC_OVER, 1.0f);
    public static final AlphaComposite DstOver = new AlphaComposite(DST_OVER, 1.0f);
    protected int rule;
    protected float alpha;
    protected AlphaComposite(int rule, float alpha) { this.rule = rule; this.alpha = alpha; }
    public static AlphaComposite getInstance(int rule) { return new AlphaComposite(rule, 1.0f); }
    public static AlphaComposite getInstance(int rule, float alpha) { return new AlphaComposite(rule, alpha); }
    public int getRule() { return rule; }
    public float getAlpha() { return alpha; }
    public CompositeContext createContext(java.awt.image.ColorModel srcColorModel, java.awt.image.ColorModel dstColorModel, RenderingHints hints) { return null; }
    public int hashCode() { return rule * 31 + Float.floatToIntBits(alpha); }
    public boolean equals(Object obj) { return obj instanceof AlphaComposite && ((AlphaComposite) obj).rule == rule && ((AlphaComposite) obj).alpha == alpha; }
}
