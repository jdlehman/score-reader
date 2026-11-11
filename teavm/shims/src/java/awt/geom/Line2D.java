package java.awt.geom;
import java.awt.Shape;
/** Minimal java.awt.geom.Line2D. */
public abstract class Line2D implements Shape, Cloneable {
    public abstract double getX1();
    public abstract double getY1();
    public abstract double getX2();
    public abstract double getY2();
    public abstract void setLine(double x1, double y1, double x2, double y2);
    public void setLine(Point2D p1, Point2D p2) { setLine(p1.getX(), p1.getY(), p2.getX(), p2.getY()); }
    public void setLine(Line2D l) { setLine(l.getX1(), l.getY1(), l.getX2(), l.getY2()); }
    public Point2D getP1() { return new Point2D.Double(getX1(), getY1()); }
    public Point2D getP2() { return new Point2D.Double(getX2(), getY2()); }
    public int relativeCCW(Point2D p) {
        return relativeCCW(getX1(), getY1(), getX2(), getY2(), p.getX(), p.getY());
    }
    public static int relativeCCW(double x1, double y1, double x2, double y2, double px, double py) {
        double dx = x2 - x1;
        double dy = y2 - y1;
        double dx1 = px - x1;
        double dy1 = py - y1;
        double ccw = dx1 * dy - dy1 * dx;
        if (ccw == 0.0) {
            ccw = dx1 * dx + dy1 * dy;
            if (ccw > 0.0) {
                dx1 -= dx;
                dy1 -= dy;
                ccw = dx1 * dx + dy1 * dy;
                if (ccw < 0.0) ccw = 0.0;
            }
        }
        return (ccw < 0.0) ? -1 : ((ccw > 0.0) ? 1 : 0);
    }
    public static double ptSegDistSq(double x1, double y1, double x2, double y2, double px, double py) {
        double dx = x2 - x1, dy = y2 - y1;
        double len2 = dx * dx + dy * dy;
        double t = len2 == 0 ? 0 : ((px - x1) * dx + (py - y1) * dy) / len2;
        t = Math.max(0, Math.min(1, t));
        double cx = x1 + t * dx, cy = y1 + t * dy;
        return Point2D.distanceSq(px, py, cx, cy);
    }
    public static double ptSegDist(double x1, double y1, double x2, double y2, double px, double py) {
        return Math.sqrt(ptSegDistSq(x1, y1, x2, y2, px, py));
    }
    public static double ptLineDistSq(double x1, double y1, double x2, double y2, double px, double py) {
        double dx = x2 - x1, dy = y2 - y1;
        double len2 = dx * dx + dy * dy;
        if (len2 == 0) return Point2D.distanceSq(px, py, x1, y1);
        double c = ((px - x1) * dx + (py - y1) * dy) / len2;
        double cx = x1 + c * dx, cy = y1 + c * dy;
        return Point2D.distanceSq(px, py, cx, cy);
    }
    public static double ptLineDist(double x1, double y1, double x2, double y2, double px, double py) {
        return Math.sqrt(ptLineDistSq(x1, y1, x2, y2, px, py));
    }
    public double ptSegDistSq(double px, double py) { return ptSegDistSq(getX1(), getY1(), getX2(), getY2(), px, py); }
    public double ptSegDistSq(Point2D p) { return ptSegDistSq(p.getX(), p.getY()); }
    public double ptSegDist(double px, double py) { return Math.sqrt(ptSegDistSq(px, py)); }
    public double ptSegDist(Point2D p) { return ptSegDist(p.getX(), p.getY()); }
    public double ptLineDistSq(double px, double py) { return ptLineDistSq(getX1(), getY1(), getX2(), getY2(), px, py); }
    public double ptLineDistSq(Point2D p) { return ptLineDistSq(p.getX(), p.getY()); }
    public double ptLineDist(double px, double py) { return Math.sqrt(ptLineDistSq(px, py)); }
    public double ptLineDist(Point2D p) { return ptLineDist(p.getX(), p.getY()); }
    public static boolean linesIntersect(double x1, double y1, double x2, double y2, double x3, double y3, double x4, double y4) {
        double d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3);
        if (d == 0) return false;
        double t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d;
        double u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / d;
        return t >= 0 && t <= 1 && u >= 0 && u <= 1;
    }
    public boolean intersectsLine(Line2D l) { return linesIntersect(getX1(), getY1(), getX2(), getY2(), l.getX1(), l.getY1(), l.getX2(), l.getY2()); }
    public boolean intersectsLine(double x1, double y1, double x2, double y2) { return linesIntersect(getX1(), getY1(), getX2(), getY2(), x1, y1, x2, y2); }
    @Override public Rectangle2D getBounds2D() {
        double x0 = Math.min(getX1(), getX2()), y0 = Math.min(getY1(), getY2());
        return new Rectangle2D.Double(x0, y0, Math.abs(getX2() - getX1()), Math.abs(getY2() - getY1()));
    }
    @Override public java.awt.Rectangle getBounds() { return getBounds2D().getBounds(); }
    @Override public boolean contains(double x, double y) { return false; }
    @Override public boolean contains(Point2D p) { return false; }
    @Override public boolean intersects(double x, double y, double w, double h) {
        return linesIntersect(getX1(), getY1(), getX2(), getY2(), x, y, x + w, y)
            || linesIntersect(getX1(), getY1(), getX2(), getY2(), x + w, y, x + w, y + h)
            || linesIntersect(getX1(), getY1(), getX2(), getY2(), x + w, y + h, x, y + h)
            || linesIntersect(getX1(), getY1(), getX2(), getY2(), x, y + h, x, y);
    }
    @Override public boolean intersects(Rectangle2D r) { return intersects(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
    @Override public boolean contains(double x, double y, double w, double h) { return false; }
    @Override public boolean contains(Rectangle2D r) { return false; }
    @Override public PathIterator getPathIterator(AffineTransform at) {
        return new LineIterator(this, at);
    }
    @Override public PathIterator getPathIterator(AffineTransform at, double flatness) { return getPathIterator(at); }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
    static final class LineIterator implements PathIterator {
        private final Line2D l; private final AffineTransform at; private int i;
        LineIterator(Line2D l, AffineTransform at) { this.l = l; this.at = at; }
        @Override public int getWindingRule() { return WIND_NON_ZERO; }
        @Override public boolean isDone() { return i > 1; }
        @Override public void next() { i++; }
        @Override public int currentSegment(float[] c) { double[] d = new double[6]; int t = currentSegment(d); for (int k = 0; k < 2; k++) c[k] = (float) d[k]; return t; }
        @Override public int currentSegment(double[] c) {
            double px = i == 0 ? l.getX1() : l.getX2(), py = i == 0 ? l.getY1() : l.getY2();
            if (at != null) { double[] p = at.transform(new double[]{px, py}); px = p[0]; py = p[1]; }
            c[0] = px; c[1] = py;
            return i == 0 ? SEG_MOVETO : SEG_LINETO;
        }
    }
    public static class Double extends Line2D {
        public double x1, y1, x2, y2;
        public Double() {}
        public Double(double x1, double y1, double x2, double y2) { this.x1 = x1; this.y1 = y1; this.x2 = x2; this.y2 = y2; }
        public Double(Point2D p1, Point2D p2) { this(p1.getX(), p1.getY(), p2.getX(), p2.getY()); }
        @Override public double getX1() { return x1; }
        @Override public double getY1() { return y1; }
        @Override public double getX2() { return x2; }
        @Override public double getY2() { return y2; }
        @Override public void setLine(double x1, double y1, double x2, double y2) { this.x1 = x1; this.y1 = y1; this.x2 = x2; this.y2 = y2; }
    }
    public static class Float extends Line2D {
        public float x1, y1, x2, y2;
        public Float() {}
        public Float(float x1, float y1, float x2, float y2) { this.x1 = x1; this.y1 = y1; this.x2 = x2; this.y2 = y2; }
        @Override public double getX1() { return x1; }
        @Override public double getY1() { return y1; }
        @Override public double getX2() { return x2; }
        @Override public double getY2() { return y2; }
        @Override public void setLine(double x1, double y1, double x2, double y2) { this.x1 = (float) x1; this.y1 = (float) y1; this.x2 = (float) x2; this.y2 = (float) y2; }
    }
}
