package java.awt.geom;
import java.awt.Shape;
/** Minimal java.awt.geom.QuadCurve2D. */
public abstract class QuadCurve2D implements Shape, Cloneable {
    protected QuadCurve2D() {}
    public abstract double getX1();
    public abstract double getY1();
    public abstract Point2D getP1();
    public abstract double getCtrlX();
    public abstract double getCtrlY();
    public abstract Point2D getCtrlPt();
    public abstract double getX2();
    public abstract double getY2();
    public abstract Point2D getP2();
    public abstract void setCurve(double x1, double y1, double ctrlx, double ctrly, double x2, double y2);
    public void setCurve(Point2D p1, Point2D cp, Point2D p2) { setCurve(p1.getX(), p1.getY(), cp.getX(), cp.getY(), p2.getX(), p2.getY()); }
    public void setCurve(double[] coords, int offset) { setCurve(coords[offset], coords[offset + 1], coords[offset + 2], coords[offset + 3], coords[offset + 4], coords[offset + 5]); }
    public void setCurve(Point2D[] pts, int offset) { setCurve(pts[offset], pts[offset + 1], pts[offset + 2]); }
    public void setCurve(QuadCurve2D c) { setCurve(c.getX1(), c.getY1(), c.getCtrlX(), c.getCtrlY(), c.getX2(), c.getY2()); }
    public static double getFlatnessSq(double x1, double y1, double ctrlx, double ctrly, double x2, double y2) { return 0; }
    public static double getFlatness(double x1, double y1, double ctrlx, double ctrly, double x2, double y2) { return 0; }
    public static double getFlatnessSq(double[] coords, int offset) { return 0; }
    public static double getFlatness(double[] coords, int offset) { return 0; }
    public double getFlatnessSq() { return 0; }
    public double getFlatness() { return 0; }
    public void subdivide(QuadCurve2D left, QuadCurve2D right) {}
    public static void subdivide(QuadCurve2D src, QuadCurve2D left, QuadCurve2D right) {}
    public static void subdivide(double[] src, int srcoff, double[] left, int leftoff, double[] right, int rightoff) {}
    public int solveQuadratic(double[] eqn) { return 0; }
    public int solveQuadratic(double[] eqn, double[] res) { return 0; }
    @Override public java.awt.Rectangle getBounds() { return new java.awt.Rectangle(); }
    @Override public boolean contains(double x, double y) { return false; }
    @Override public boolean contains(Point2D p) { return false; }
    @Override public boolean intersects(double x, double y, double w, double h) { return false; }
    @Override public boolean intersects(Rectangle2D r) { return false; }
    @Override public boolean contains(double x, double y, double w, double h) { return false; }
    @Override public boolean contains(Rectangle2D r) { return false; }
    // TEAVM §12: these used to return null. NaturalSpline.interpolate()
    // builds a QuadCurve2D for a 3-point interpolation, and its ctor appends
    // the curve via Path2D.append -> getPathIterator(null) -> it.isDone()
    // on the null iterator traps under TeaVM WasmGC (GRID step, first seen
    // in full-out16). Mirror the CubicIterator in CubicCurve2D.java.
    @Override public PathIterator getPathIterator(AffineTransform at) { return new QuadIterator(this, at); }
    @Override public PathIterator getPathIterator(AffineTransform at, double flatness) { return getPathIterator(at); }
    static final class QuadIterator implements PathIterator {
        private final QuadCurve2D c; private final AffineTransform at; private int i;
        QuadIterator(QuadCurve2D c, AffineTransform at) { this.c = c; this.at = at; }
        @Override public int getWindingRule() { return WIND_NON_ZERO; }
        @Override public boolean isDone() { return i > 1; }
        @Override public void next() { i++; }
        @Override public int currentSegment(float[] cf) { double[] cd = new double[6]; int t = currentSegment(cd); for (int k = 0; k < 6; k++) cf[k] = (float) cd[k]; return t; }
        @Override public int currentSegment(double[] cd) {
            if (i == 0) {
                double[] p = at == null ? new double[]{c.getX1(), c.getY1()} : at.transform(new double[]{c.getX1(), c.getY1()});
                cd[0] = p[0]; cd[1] = p[1];
                return SEG_MOVETO;
            }
            double[] raw = {c.getCtrlX(), c.getCtrlY(), c.getX2(), c.getY2()};
            double[] out = at == null ? raw : new double[4];
            if (at != null) at.transform(raw, 0, out, 0, 2);
            System.arraycopy(out, 0, cd, 0, 4);
            return SEG_QUADTO;
        }
    }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
    public static class Double extends QuadCurve2D {
        public double x1, y1, ctrlx, ctrly, x2, y2;
        public Double() {}
        public Double(double x1, double y1, double ctrlx, double ctrly, double x2, double y2) { setCurve(x1, y1, ctrlx, ctrly, x2, y2); }
        @Override public double getX1() { return x1; }
        @Override public double getY1() { return y1; }
        @Override public Point2D getP1() { return new Point2D.Double(x1, y1); }
        @Override public double getCtrlX() { return ctrlx; }
        @Override public double getCtrlY() { return ctrly; }
        @Override public Point2D getCtrlPt() { return new Point2D.Double(ctrlx, ctrly); }
        @Override public double getX2() { return x2; }
        @Override public double getY2() { return y2; }
        @Override public Point2D getP2() { return new Point2D.Double(x2, y2); }
        @Override public void setCurve(double x1, double y1, double ctrlx, double ctrly, double x2, double y2) {
            this.x1 = x1; this.y1 = y1; this.ctrlx = ctrlx; this.ctrly = ctrly; this.x2 = x2; this.y2 = y2;
        }
        @Override public Rectangle2D getBounds2D() {
            return new Rectangle2D.Double(Math.min(x1, x2), Math.min(y1, y2), Math.abs(x2 - x1), Math.abs(y2 - y1));
        }
    }
    public static class Float extends QuadCurve2D {
        public float x1, y1, ctrlx, ctrly, x2, y2;
        public Float() {}
        public Float(float x1, float y1, float ctrlx, float ctrly, float x2, float y2) { setCurve(x1, y1, ctrlx, ctrly, x2, y2); }
        @Override public double getX1() { return x1; }
        @Override public double getY1() { return y1; }
        @Override public Point2D getP1() { return new Point2D.Double(x1, y1); }
        @Override public double getCtrlX() { return ctrlx; }
        @Override public double getCtrlY() { return ctrly; }
        @Override public Point2D getCtrlPt() { return new Point2D.Double(ctrlx, ctrly); }
        @Override public double getX2() { return x2; }
        @Override public double getY2() { return y2; }
        @Override public Point2D getP2() { return new Point2D.Double(x2, y2); }
        @Override public void setCurve(double x1, double y1, double ctrlx, double ctrly, double x2, double y2) {
            this.x1 = (float) x1; this.y1 = (float) y1; this.ctrlx = (float) ctrlx; this.ctrly = (float) ctrly; this.x2 = (float) x2; this.y2 = (float) y2;
        }
        @Override public Rectangle2D getBounds2D() {
            return new Rectangle2D.Double(Math.min(x1, x2), Math.min(y1, y2), Math.abs(x2 - x1), Math.abs(y2 - y1));
        }
    }
}
