package java.awt;
import java.awt.geom.Point2D;
import java.awt.geom.Rectangle2D;
/** Minimal java.awt.Polygon. */
public class Polygon implements Shape {
    public int npoints;
    public int[] xpoints, ypoints;
    protected Rectangle bounds;
    public Polygon() { xpoints = new int[4]; ypoints = new int[4]; }
    public Polygon(int[] xs, int[] ys, int n) {
        xpoints = xs.clone(); ypoints = ys.clone(); npoints = n;
    }
    public void addPoint(int x, int y) {
        if (npoints == xpoints.length) {
            int[] nx = new int[npoints * 2], ny = new int[npoints * 2];
            System.arraycopy(xpoints, 0, nx, 0, npoints);
            System.arraycopy(ypoints, 0, ny, 0, npoints);
            xpoints = nx; ypoints = ny;
        }
        xpoints[npoints] = x; ypoints[npoints] = y; npoints++;
        bounds = null;
    }
    public void reset() { npoints = 0; bounds = null; }
    public void translate(int dx, int dy) {
        for (int i = 0; i < npoints; i++) { xpoints[i] += dx; ypoints[i] += dy; }
        bounds = null;
    }
    public boolean contains(int x, int y) {
        boolean inside = false;
        for (int i = 0, j = npoints - 1; i < npoints; j = i++) {
            if ((ypoints[i] > y) != (ypoints[j] > y)
                    && x < (xpoints[j] - xpoints[i]) * (y - ypoints[i]) / (double) (ypoints[j] - ypoints[i]) + xpoints[i])
                inside = !inside;
        }
        return inside;
    }
    public boolean contains(Point2D p) { return contains((int) p.getX(), (int) p.getY()); }
    public Rectangle getBounds() {
        if (bounds != null) return new Rectangle(bounds);
        if (npoints == 0) return new Rectangle();
        int x0 = xpoints[0], y0 = ypoints[0], x1 = x0, y1 = y0;
        for (int i = 1; i < npoints; i++) {
            x0 = Math.min(x0, xpoints[i]); y0 = Math.min(y0, ypoints[i]);
            x1 = Math.max(x1, xpoints[i]); y1 = Math.max(y1, ypoints[i]);
        }
        bounds = new Rectangle(x0, y0, x1 - x0, y1 - y0);
        return new Rectangle(bounds);
    }
    @Override public Rectangle2D getBounds2D() { Rectangle r = getBounds(); return new Rectangle2D.Double(r.x, r.y, r.width, r.height); }
    @Override public boolean contains(double x, double y) { return contains((int) x, (int) y); }
    @Override public boolean intersects(double x, double y, double w, double h) { return getBounds2D().intersects(x, y, w, h); }
    @Override public boolean intersects(Rectangle2D r) { return getBounds2D().intersects(r); }
    @Override public boolean contains(double x, double y, double w, double h) { return getBounds2D().contains(x, y, w, h); }
    @Override public boolean contains(Rectangle2D r) { return getBounds2D().contains(r); }
    @Override public java.awt.geom.PathIterator getPathIterator(java.awt.geom.AffineTransform at) {
        return new java.awt.geom.Path2D.Double(this).getPathIterator(at);
    }
    @Override public java.awt.geom.PathIterator getPathIterator(java.awt.geom.AffineTransform at, double f) { return getPathIterator(at); }
}
