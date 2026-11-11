package java.awt.font;
import java.awt.geom.AffineTransform;
/** Minimal java.awt.font.FontRenderContext (no real metrics). */
public class FontRenderContext {
    private final AffineTransform transform;
    private final boolean antiAliased, usesFractionalMetrics;
    public FontRenderContext(AffineTransform tx, boolean aa, boolean fm) {
        transform = tx == null ? new AffineTransform() : new AffineTransform(tx);
        antiAliased = aa; usesFractionalMetrics = fm;
    }
    public AffineTransform getTransform() { return new AffineTransform(transform); }
    public boolean isAntiAliased() { return antiAliased; }
    public boolean usesFractionalMetrics() { return usesFractionalMetrics; }
    @Override public boolean equals(Object o) {
        if (o instanceof FontRenderContext f)
            return transform.equals(f.transform) && antiAliased == f.antiAliased && usesFractionalMetrics == f.usesFractionalMetrics;
        return false;
    }
    @Override public int hashCode() { return transform.hashCode(); }
}
