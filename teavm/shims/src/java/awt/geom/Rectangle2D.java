package java.awt.geom;
import java.awt.Shape;
/** Minimal java.awt.geom.Rectangle2D. */
public abstract class Rectangle2D implements Shape, Cloneable {
    public static final int OUT_LEFT = 1, OUT_TOP = 2, OUT_RIGHT = 4, OUT_BOTTOM = 8;
    public abstract double getX();
    public abstract double getY();
    public abstract double getWidth();
    public abstract double getHeight();
    public abstract boolean isEmpty();
    public abstract void setRect(double x, double y, double w, double h);
    public void setRect(Rectangle2D r) { setRect(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
    public double getMinX() { return getX(); }
    public double getMinY() { return getY(); }
    public double getMaxX() { return getX() + getWidth(); }
    public double getMaxY() { return getY() + getHeight(); }
    public double getCenterX() { return getX() + getWidth() / 2; }
    public double getCenterY() { return getY() + getHeight() / 2; }
    public Rectangle2D getBounds2D() { return new Double(getX(), getY(), getWidth(), getHeight()); }
    // §31 (DIAG36): JDK RectangularShape.getBounds, verbatim from OpenJDK 25
    // (Rectangle2D inherits it in the JDK; the shim's Rectangle2D is
    // standalone, so it needs its own copy). The old truncation shrank the
    // fill window by up to 1 px on the right/bottom, same defect as
    // RectangularShape.getBounds.
    public java.awt.Rectangle getBounds() {
        double width = getWidth();
        double height = getHeight();
        if (width < 0 || height < 0) {
            return new java.awt.Rectangle();
        }
        double x = getX();
        double y = getY();
        double x1 = Math.floor(x);
        double y1 = Math.floor(y);
        double x2 = Math.ceil(x + width);
        double y2 = Math.ceil(y + height);
        return new java.awt.Rectangle((int) x1, (int) y1,
                                      (int) (x2 - x1), (int) (y2 - y1));
    }
    public boolean contains(double x, double y) {
        return x >= getX() && x < getMaxX() && y >= getY() && y < getMaxY();
    }
    public boolean contains(Point2D p) { return contains(p.getX(), p.getY()); }
    // TEAVM §24 trap 4: JDK Rectangle2D.Double/Float.contains(x,y,w,h) is
    // INCLUSIVE on the far edge and false for w<=0/h<=0 (verified on JDK 25).
    // The old half-open two-corner test rejected every rectangle touching
    // the far edge. (Correction, §31: the §24 note's claim that
    // RectangularShape's two-corner form is "JDK-faithful for
    // non-rectangular shapes such as Ellipse2D" was wrong — JDK Ellipse2D
    // overrides contains(x,y,w,h) with the four-corner test, verified on
    // JDK 25: rect [6,1,3,3] on ellipse (0,0,10,10) is false, while the
    // two-corner test says true. Ellipse2D now carries the verbatim JDK
    // four-corner override, and RectangularShape's form is four-corner.
    // A zero-size rect at an interior point IS contained by an ellipse —
    // the four-corner test has no w<=0/h<=0 guard, unlike this rectangle
    // version — which the differential test confirms.)
    public boolean contains(double x, double y, double w, double h) {
        if (w <= 0 || h <= 0) {
            return false;
        }
        return x >= getX() && y >= getY() && (x + w) <= getMaxX() && (y + h) <= getMaxY();
    }
    public boolean contains(Rectangle2D r) { return contains(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
    public boolean intersects(double x, double y, double w, double h) {
        return x + w > getX() && x < getMaxX() && y + h > getY() && y < getMaxY();
    }
    public boolean intersects(Rectangle2D r) { return intersects(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
    public int outcode(double x, double y) {
        int c = 0;
        if (x < getX()) c |= OUT_LEFT; else if (x > getMaxX()) c |= OUT_RIGHT;
        if (y < getY()) c |= OUT_TOP; else if (y > getMaxY()) c |= OUT_BOTTOM;
        return c;
    }
    public void add(double x, double y) {
        double x0 = Math.min(getX(), x), y0 = Math.min(getY(), y);
        double x1 = Math.max(getMaxX(), x), y1 = Math.max(getMaxY(), y);
        setRect(x0, y0, x1 - x0, y1 - y0);
    }
    public void add(Point2D p) { add(p.getX(), p.getY()); }
    public void add(Rectangle2D r) {
        double x0 = Math.min(getX(), r.getX()), y0 = Math.min(getY(), r.getY());
        double x1 = Math.max(getMaxX(), r.getMaxX()), y1 = Math.max(getMaxY(), r.getMaxY());
        setRect(x0, y0, x1 - x0, y1 - y0);
    }
    public static void union(Rectangle2D a, Rectangle2D b, Rectangle2D dest) {
        double x0 = Math.min(a.getX(), b.getX()), y0 = Math.min(a.getY(), b.getY());
        double x1 = Math.max(a.getMaxX(), b.getMaxX()), y1 = Math.max(a.getMaxY(), b.getMaxY());
        dest.setRect(x0, y0, x1 - x0, y1 - y0);
    }
    public static void intersect(Rectangle2D a, Rectangle2D b, Rectangle2D dest) {
        double x0 = Math.max(a.getX(), b.getX()), y0 = Math.max(a.getY(), b.getY());
        double x1 = Math.min(a.getMaxX(), b.getMaxX()), y1 = Math.min(a.getMaxY(), b.getMaxY());
        dest.setRect(x0, y0, Math.max(0, x1 - x0), Math.max(0, y1 - y0));
    }
    public Rectangle2D createIntersection(Rectangle2D r) {
        Rectangle2D d = new Double();
        intersect(this, r, d);
        return d;
    }
    public Rectangle2D createUnion(Rectangle2D r) {
        Rectangle2D d = new Double();
        union(this, r, d);
        return d;
    }
    @Override public PathIterator getPathIterator(AffineTransform at) {
        return new RectIterator(this, at);
    }
    @Override public PathIterator getPathIterator(AffineTransform at, double flatness) { return getPathIterator(at); }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
    @Override public boolean equals(Object o) {
        if (o instanceof Rectangle2D r)
            return getX() == r.getX() && getY() == r.getY() && getWidth() == r.getWidth() && getHeight() == r.getHeight();
        return false;
    }
    @Override public int hashCode() {
        long h = java.lang.Double.doubleToLongBits(getX());
        h = h * 31 + java.lang.Double.doubleToLongBits(getY());
        h = h * 31 + java.lang.Double.doubleToLongBits(getWidth());
        h = h * 31 + java.lang.Double.doubleToLongBits(getHeight());
        return (int) (h ^ (h >>> 32));
    }
    static final class RectIterator implements PathIterator {
        private final double x, y, w, h; private final AffineTransform at; private int i;
        RectIterator(Rectangle2D r, AffineTransform at) { x = r.getX(); y = r.getY(); w = r.getWidth(); h = r.getHeight(); this.at = at; }
        @Override public int getWindingRule() { return WIND_NON_ZERO; }
        @Override public boolean isDone() { return i > 4; }
        @Override public void next() { i++; }
        @Override public int currentSegment(float[] c) { double[] d = new double[6]; int t = currentSegment(d); for (int k = 0; k < 6; k++) c[k] = (float) d[k]; return t; }
        @Override public int currentSegment(double[] c) {
            double px, py; int type;
            switch (i) {
                case 0 -> { px = x; py = y; type = SEG_MOVETO; }
                case 1 -> { px = x + w; py = y; type = SEG_LINETO; }
                case 2 -> { px = x + w; py = y + h; type = SEG_LINETO; }
                case 3 -> { px = x; py = y + h; type = SEG_LINETO; }
                default -> { type = SEG_CLOSE; px = 0; py = 0; }
            }
            if (type != SEG_CLOSE) {
                if (at != null) { double[] p = at.transform(new double[]{px, py}); px = p[0]; py = p[1]; }
                c[0] = px; c[1] = py;
            }
            return type;
        }
    }
    public static class Double extends Rectangle2D {
        public double x, y, width, height;
        public Double() {}
        public Double(double x, double y, double w, double h) { this.x = x; this.y = y; width = w; height = h; }
        public Double(Rectangle2D r) { this(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public double getWidth() { return width; }
        @Override public double getHeight() { return height; }
        @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
        @Override public void setRect(double x, double y, double w, double h) { this.x = x; this.y = y; width = w; height = h; }
        @Override public String toString() { return "Rectangle2D.Double[" + x + ", " + y + ", " + width + "x" + height + "]"; }
    }
    public static class Float extends Rectangle2D {
        public float x, y, width, height;
        public Float() {}
        public Float(float x, float y, float w, float h) { this.x = x; this.y = y; width = w; height = h; }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public double getWidth() { return width; }
        @Override public double getHeight() { return height; }
        @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
        @Override public void setRect(double x, double y, double w, double h) { this.x = (float) x; this.y = (float) y; width = (float) w; height = (float) h; }
    }
}
