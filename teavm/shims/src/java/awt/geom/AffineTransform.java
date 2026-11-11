package java.awt.geom;
import java.awt.Shape;
/** Minimal java.awt.geom.AffineTransform (3x3 matrix, double precision). */
public class AffineTransform implements Cloneable {
    public static final int TYPE_IDENTITY = 0;
    public static final int TYPE_TRANSLATION = 1;
    public static final int TYPE_UNIFORM_SCALE = 2;
    public static final int TYPE_GENERAL_SCALE = 4;
    public static final int TYPE_MASK_SCALE = TYPE_UNIFORM_SCALE | TYPE_GENERAL_SCALE;
    public static final int TYPE_FLIP = 64;
    public static final int TYPE_QUADRANT_ROTATION = 8;
    public static final int TYPE_GENERAL_ROTATION = 16;
    public static final int TYPE_MASK_ROTATION = TYPE_QUADRANT_ROTATION | TYPE_GENERAL_ROTATION;
    public static final int TYPE_GENERAL_TRANSFORM = 32;
    double m00, m10, m01, m11, m02, m12;
    public AffineTransform() { m00 = 1; m11 = 1; }
    public AffineTransform(double m00, double m10, double m01, double m11, double m02, double m12) {
        this.m00 = m00; this.m10 = m10; this.m01 = m01; this.m11 = m11; this.m02 = m02; this.m12 = m12;
    }
    public AffineTransform(AffineTransform t) { setTransform(t); }
    public AffineTransform(float m00, float m10, float m01, float m11, float m02, float m12) {
        this((double) m00, (double) m10, (double) m01, (double) m11, (double) m02, (double) m12);
    }
    public static AffineTransform getTranslateInstance(double tx, double ty) {
        return new AffineTransform(1, 0, 0, 1, tx, ty);
    }
    public static AffineTransform getScaleInstance(double sx, double sy) {
        return new AffineTransform(sx, 0, 0, sy, 0, 0);
    }
    public static AffineTransform getRotateInstance(double theta) {
        double c = Math.cos(theta), s = Math.sin(theta);
        return new AffineTransform(c, s, -s, c, 0, 0);
    }
    public static AffineTransform getRotateInstance(double theta, double x, double y) {
        AffineTransform t = getRotateInstance(theta);
        t.translate(x, y);
        return t;
    }
    public static AffineTransform getShearInstance(double shx, double shy) {
        return new AffineTransform(1, shy, shx, 1, 0, 0);
    }
    public int getType() {
        if (m01 == 0 && m10 == 0) {
            if (m00 == 1 && m11 == 1) return m02 == 0 && m12 == 0 ? TYPE_IDENTITY : TYPE_TRANSLATION;
            if (m00 == m11) return TYPE_UNIFORM_SCALE;
            return TYPE_GENERAL_SCALE;
        }
        return TYPE_GENERAL_TRANSFORM;
    }
    public double getDeterminant() { return m00 * m11 - m01 * m10; }
    public void getMatrix(double[] m) { m[0] = m00; m[1] = m10; m[2] = m01; m[3] = m11; m[4] = m02; m[5] = m12; }
    public double getScaleX() { return m00; }
    public double getScaleY() { return m11; }
    public double getShearX() { return m01; }
    public double getShearY() { return m10; }
    public double getTranslateX() { return m02; }
    public double getTranslateY() { return m12; }
    public void setTransform(AffineTransform t) {
        m00 = t.m00; m10 = t.m10; m01 = t.m01; m11 = t.m11; m02 = t.m02; m12 = t.m12;
    }
    public void setTransform(double m00, double m10, double m01, double m11, double m02, double m12) {
        this.m00 = m00; this.m10 = m10; this.m01 = m01; this.m11 = m11; this.m02 = m02; this.m12 = m12;
    }
    public void setToIdentity() { m00 = 1; m10 = 0; m01 = 0; m11 = 1; m02 = 0; m12 = 0; }
    public void setToTranslation(double tx, double ty) { setToIdentity(); m02 = tx; m12 = ty; }
    public void setToScale(double sx, double sy) { setToIdentity(); m00 = sx; m11 = sy; }
    public void setToRotation(double theta) {
        double c = Math.cos(theta), s = Math.sin(theta);
        setTransform(c, s, -s, c, 0, 0);
    }
    public void setToRotation(double theta, double x, double y) {
        setToRotation(theta);
        double tx = x - x * m00 - y * m01, ty = y - x * m10 - y * m11;
        m02 = tx; m12 = ty;
    }
    public void setToShear(double shx, double shy) { setTransform(1, shy, shx, 1, 0, 0); }
    public boolean isIdentity() { return m00 == 1 && m11 == 1 && m01 == 0 && m10 == 0 && m02 == 0 && m12 == 0; }
    public void translate(double tx, double ty) {
        m02 = tx * m00 + ty * m01 + m02;
        m12 = tx * m10 + ty * m11 + m12;
    }
    public void scale(double sx, double sy) { m00 *= sx; m10 *= sx; m01 *= sy; m11 *= sy; }
    public void rotate(double theta) {
        double c = Math.cos(theta), s = Math.sin(theta);
        double n00 = m00 * c + m01 * s, n01 = -m00 * s + m01 * c;
        double n10 = m10 * c + m11 * s, n11 = -m10 * s + m11 * c;
        m00 = n00; m01 = n01; m10 = n10; m11 = n11;
    }
    public void rotate(double theta, double x, double y) { translate(x, y); rotate(theta); translate(-x, -y); }
    public void shear(double shx, double shy) {
        double n00 = m00 + m01 * shy, n01 = m00 * shx + m01;
        double n10 = m10 + m11 * shy, n11 = m10 * shx + m11;
        m00 = n00; m01 = n01; m10 = n10; m11 = n11;
    }
    public void concatenate(AffineTransform t) {
        double n00 = m00 * t.m00 + m01 * t.m10, n01 = m00 * t.m01 + m01 * t.m11;
        double n02 = m00 * t.m02 + m01 * t.m12 + m02;
        double n10 = m10 * t.m00 + m11 * t.m10, n11 = m10 * t.m01 + m11 * t.m11;
        double n12 = m10 * t.m02 + m11 * t.m12 + m12;
        m00 = n00; m01 = n01; m02 = n02; m10 = n10; m11 = n11; m12 = n12;
    }
    public void preConcatenate(AffineTransform t) {
        double n00 = t.m00 * m00 + t.m01 * m10, n01 = t.m00 * m01 + t.m01 * m11;
        double n02 = t.m00 * m02 + t.m01 * m12 + t.m02;
        double n10 = t.m10 * m00 + t.m11 * m10, n11 = t.m10 * m01 + t.m11 * m11;
        double n12 = t.m10 * m02 + t.m11 * m12 + t.m12;
        m00 = n00; m01 = n01; m02 = n02; m10 = n10; m11 = n11; m12 = n12;
    }
    public AffineTransform createInverse() throws NoninvertibleTransformException {
        double det = getDeterminant();
        if (det == 0) throw new NoninvertibleTransformException("zero determinant");
        return new AffineTransform(m11 / det, -m10 / det, -m01 / det, m00 / det,
                (m01 * m12 - m11 * m02) / det, (m10 * m02 - m00 * m12) / det);
    }
    public Point2D transform(Point2D src, Point2D dst) {
        if (dst == null) dst = new Point2D.Double();
        double x = src.getX(), y = src.getY();
        dst.setLocation(x * m00 + y * m01 + m02, x * m10 + y * m11 + m12);
        return dst;
    }
    public double[] transform(double[] src) {
        double[] dst = new double[src.length];
        transform(src, 0, dst, 0, src.length / 2);
        return dst;
    }
    public void transform(double[] src, int so, double[] dst, int doff, int n) {
        for (int i = 0; i < n; i++) {
            double x = src[so + 2 * i], y = src[so + 2 * i + 1];
            dst[doff + 2 * i] = x * m00 + y * m01 + m02;
            dst[doff + 2 * i + 1] = x * m10 + y * m11 + m12;
        }
    }
    public void transform(float[] src, int so, float[] dst, int doff, int n) {
        for (int i = 0; i < n; i++) {
            double x = src[so + 2 * i], y = src[so + 2 * i + 1];
            dst[doff + 2 * i] = (float) (x * m00 + y * m01 + m02);
            dst[doff + 2 * i + 1] = (float) (x * m10 + y * m11 + m12);
        }
    }
    public Point2D deltaTransform(Point2D src, Point2D dst) {
        if (dst == null) dst = new Point2D.Double();
        double x = src.getX(), y = src.getY();
        dst.setLocation(x * m00 + y * m01, x * m10 + y * m11);
        return dst;
    }
    public Point2D inverseTransform(Point2D src, Point2D dst) throws NoninvertibleTransformException {
        return createInverse().transform(src, dst);
    }
    public Shape createTransformedShape(Shape s) {
        if (s instanceof Rectangle2D r) {
            double[] xs = {r.getX(), r.getMaxX(), r.getMaxX(), r.getX()};
            double[] ys = {r.getY(), r.getY(), r.getMaxY(), r.getMaxY()};
            double x0 = Double.MAX_VALUE, y0 = Double.MAX_VALUE, x1 = -Double.MAX_VALUE, y1 = -Double.MAX_VALUE;
            for (int i = 0; i < 4; i++) {
                double[] p = transform(new double[]{xs[i], ys[i]});
                x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]);
            }
            return new Rectangle2D.Double(x0, y0, x1 - x0, y1 - y0);
        }
        return s;
    }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
    @Override public boolean equals(Object o) {
        if (o instanceof AffineTransform t)
            return m00 == t.m00 && m10 == t.m10 && m01 == t.m01 && m11 == t.m11 && m02 == t.m02 && m12 == t.m12;
        return false;
    }
    @Override public int hashCode() {
        long h = Double.doubleToLongBits(m00);
        h = h * 31 + Double.doubleToLongBits(m10);
        h = h * 31 + Double.doubleToLongBits(m01);
        h = h * 31 + Double.doubleToLongBits(m11);
        h = h * 31 + Double.doubleToLongBits(m02);
        h = h * 31 + Double.doubleToLongBits(m12);
        return (int) (h ^ (h >>> 32));
    }
    @Override public String toString() {
        return "AffineTransform[[" + m00 + ", " + m01 + ", " + m02 + "], [" + m10 + ", " + m11 + ", " + m12 + "]]";
    }
    public static AffineTransform getQuadrantRotateInstance(int numquadrants) {
        return new AffineTransform();
    }
}
