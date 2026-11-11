package java.awt.geom;
/** Minimal java.awt.geom.Point2D (OpenJDK geometry is plain Java; this is a fresh minimal port). */
public abstract class Point2D implements Cloneable {
    public abstract double getX();
    public abstract double getY();
    public abstract void setLocation(double x, double y);
    public void setLocation(Point2D p) { setLocation(p.getX(), p.getY()); }
    public static double distanceSq(double x1, double y1, double x2, double y2) {
        double dx = x2 - x1, dy = y2 - y1; return dx * dx + dy * dy;
    }
    public static double distance(double x1, double y1, double x2, double y2) {
        return Math.sqrt(distanceSq(x1, y1, x2, y2));
    }
    public double distanceSq(double px, double py) { return distanceSq(getX(), getY(), px, py); }
    public double distanceSq(Point2D p) { return distanceSq(getX(), getY(), p.getX(), p.getY()); }
    public double distance(double px, double py) { return distance(getX(), getY(), px, py); }
    public double distance(Point2D p) { return distance(getX(), getY(), p.getX(), p.getY()); }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
    @Override public boolean equals(Object o) {
        if (o instanceof Point2D p) return getX() == p.getX() && getY() == p.getY();
        return false;
    }
    @Override public int hashCode() {
        long x = java.lang.Double.doubleToLongBits(getX()), y = java.lang.Double.doubleToLongBits(getY());
        return (int) (x ^ (x >>> 32)) * 31 + (int) (y ^ (y >>> 32));
    }
    public static class Double extends Point2D {
        public double x, y;
        public Double() {}
        public Double(double x, double y) { this.x = x; this.y = y; }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public void setLocation(double x, double y) { this.x = x; this.y = y; }
        @Override public String toString() { return "Point2D.Double[" + x + ", " + y + "]"; }
    }
    public static class Float extends Point2D {
        public float x, y;
        public Float() {}
        public Float(float x, float y) { this.x = x; this.y = y; }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public void setLocation(double x, double y) { this.x = (float) x; this.y = (float) y; }
        @Override public String toString() { return "Point2D.Float[" + x + ", " + y + "]"; }
    }
}
