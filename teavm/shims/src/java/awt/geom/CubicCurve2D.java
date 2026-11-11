package java.awt.geom;
import java.awt.Shape;
/** Minimal java.awt.geom.CubicCurve2D. */
public abstract class CubicCurve2D implements Shape, Cloneable {
    public abstract double getX1();
    public abstract double getY1();
    public abstract double getCtrlX1();
    public abstract double getCtrlY1();
    public abstract double getCtrlX2();
    public abstract double getCtrlY2();
    public abstract double getX2();
    public abstract double getY2();
    public abstract void setCurve(double x1, double y1, double x2, double y2, double x3, double y3, double x4, double y4);
    // §14: SlurSymbol.paint calls setCurve(Point2D[], int); mirror the
    // QuadCurve2D shim's overloads (JDK signatures).
    public void setCurve(double[] coords, int offset) { setCurve(coords[offset], coords[offset + 1], coords[offset + 2], coords[offset + 3], coords[offset + 4], coords[offset + 5], coords[offset + 6], coords[offset + 7]); }
    public void setCurve(Point2D p1, Point2D cp1, Point2D cp2, Point2D p2) { setCurve(p1.getX(), p1.getY(), cp1.getX(), cp1.getY(), cp2.getX(), cp2.getY(), p2.getX(), p2.getY()); }
    public void setCurve(Point2D[] pts, int offset) { setCurve(pts[offset], pts[offset + 1], pts[offset + 2], pts[offset + 3]); }
    public void setCurve(CubicCurve2D c) { setCurve(c.getX1(), c.getY1(), c.getCtrlX1(), c.getCtrlY1(), c.getCtrlX2(), c.getCtrlY2(), c.getX2(), c.getY2()); }
    public Point2D getP1() { return new Point2D.Double(getX1(), getY1()); }
    public Point2D getCtrlP1() { return new Point2D.Double(getCtrlX1(), getCtrlY1()); }
    public Point2D getCtrlP2() { return new Point2D.Double(getCtrlX2(), getCtrlY2()); }
    public Point2D getP2() { return new Point2D.Double(getX2(), getY2()); }
    public static void subdivide(CubicCurve2D src, CubicCurve2D left, CubicCurve2D right) {
        double x1 = src.getX1(), y1 = src.getY1();
        double cx1 = src.getCtrlX1(), cy1 = src.getCtrlY1();
        double cx2 = src.getCtrlX2(), cy2 = src.getCtrlY2();
        double x2 = src.getX2(), y2 = src.getY2();
        double x12 = (x1 + cx1) / 2, y12 = (y1 + cy1) / 2;
        double x23 = (cx1 + cx2) / 2, y23 = (cy1 + cy2) / 2;
        double x34 = (cx2 + x2) / 2, y34 = (cy2 + y2) / 2;
        double x123 = (x12 + x23) / 2, y123 = (y12 + y23) / 2;
        double x234 = (x23 + x34) / 2, y234 = (y23 + y34) / 2;
        double x1234 = (x123 + x234) / 2, y1234 = (y123 + y234) / 2;
        if (left != null) left.setCurve(x1, y1, x12, y12, x123, y123, x1234, y1234);
        if (right != null) right.setCurve(x1234, y1234, x234, y234, x34, y34, x2, y2);
    }
    public static void subdivide(CubicCurve2D src, CubicCurve2D left) { subdivide(src, left, null); }
    @Override public Rectangle2D getBounds2D() {
        double x0 = Math.min(Math.min(getX1(), getCtrlX1()), Math.min(getCtrlX2(), getX2()));
        double y0 = Math.min(Math.min(getY1(), getCtrlY1()), Math.min(getCtrlY2(), getY2()));
        double x1 = Math.max(Math.max(getX1(), getCtrlX1()), Math.max(getCtrlX2(), getX2()));
        double y1 = Math.max(Math.max(getY1(), getCtrlY1()), Math.max(getCtrlY2(), getY2()));
        return new Rectangle2D.Double(x0, y0, x1 - x0, y1 - y0);
    }
    @Override public java.awt.Rectangle getBounds() { return getBounds2D().getBounds(); }
    @Override public boolean contains(double x, double y) { return false; }
    @Override public boolean contains(Point2D p) { return false; }
    @Override public boolean contains(double x, double y, double w, double h) { return false; }
    @Override public boolean contains(Rectangle2D r) { return false; }
    @Override public boolean intersects(double x, double y, double w, double h) { return getBounds2D().intersects(x, y, w, h); }
    @Override public boolean intersects(Rectangle2D r) { return getBounds2D().intersects(r); }
    @Override public PathIterator getPathIterator(AffineTransform at) { return new CubicIterator(this, at); }
    @Override public PathIterator getPathIterator(AffineTransform at, double flatness) { return getPathIterator(at); }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
    static final class CubicIterator implements PathIterator {
        private final CubicCurve2D c; private final AffineTransform at; private int i;
        CubicIterator(CubicCurve2D c, AffineTransform at) { this.c = c; this.at = at; }
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
            double[] raw = {c.getCtrlX1(), c.getCtrlY1(), c.getCtrlX2(), c.getCtrlY2(), c.getX2(), c.getY2()};
            double[] out = at == null ? raw : new double[6];
            if (at != null) at.transform(raw, 0, out, 0, 3);
            System.arraycopy(out, 0, cd, 0, 6);
            return SEG_CUBICTO;
        }
    }
    public static class Double extends CubicCurve2D {
        public double x1, y1, ctrlx1, ctrly1, ctrlx2, ctrly2, x2, y2;
        public Double() {}
        public Double(double x1, double y1, double x2, double y2, double x3, double y3, double x4, double y4) {
            setCurve(x1, y1, x2, y2, x3, y3, x4, y4);
        }
        @Override public double getX1() { return x1; }
        @Override public double getY1() { return y1; }
        @Override public double getCtrlX1() { return ctrlx1; }
        @Override public double getCtrlY1() { return ctrly1; }
        @Override public double getCtrlX2() { return ctrlx2; }
        @Override public double getCtrlY2() { return ctrly2; }
        @Override public double getX2() { return x2; }
        @Override public double getY2() { return y2; }
        @Override public void setCurve(double x1, double y1, double x2, double y2, double x3, double y3, double x4, double y4) {
            this.x1 = x1; this.y1 = y1; ctrlx1 = x2; ctrly1 = y2; ctrlx2 = x3; ctrly2 = y3; this.x2 = x4; this.y2 = y4;
        }
    }
}
