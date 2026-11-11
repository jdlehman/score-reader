package java.awt;
import java.awt.geom.Path2D;
import java.awt.Shape;
/** Minimal java.awt.BasicStroke (stroking is a no-op: returns the shape itself). */
public class BasicStroke implements Stroke {
    public static final int CAP_BUTT = 0, CAP_ROUND = 1, CAP_SQUARE = 2;
    public static final int JOIN_MITER = 0, JOIN_ROUND = 1, JOIN_BEVEL = 2;
    private final float width;
    private final int cap, join;
    private final float miterlimit;
    private final float[] dash;
    private final float dashPhase;
    public BasicStroke(float width) { this(width, CAP_SQUARE, JOIN_MITER, 10.0f, null, 0.0f); }
    public BasicStroke(float width, int cap, int join) { this(width, cap, join, 10.0f, null, 0.0f); }
    public BasicStroke(float width, int cap, int join, float miterlimit) { this(width, cap, join, miterlimit, null, 0.0f); }
    public BasicStroke(float width, int cap, int join, float miterlimit, float[] dash, float dashPhase) {
        this.width = width; this.cap = cap; this.join = join; this.miterlimit = miterlimit;
        this.dash = dash; this.dashPhase = dashPhase;
    }
    public BasicStroke() { this(1.0f); }
    public float getLineWidth() { return width; }
    public int getEndCap() { return cap; }
    public int getLineJoin() { return join; }
    public float getMiterLimit() { return miterlimit; }
    public float[] getDashArray() { return dash == null ? null : dash.clone(); }
    public float getDashPhase() { return dashPhase; }
    @Override public Shape createStrokedShape(Shape s) { return s; }
    @Override public boolean equals(Object o) {
        if (o instanceof BasicStroke b)
            return width == b.width && cap == b.cap && join == b.join && miterlimit == b.miterlimit;
        return false;
    }
    @Override public int hashCode() { return (int) width * 31 + cap * 7 + join; }
}
