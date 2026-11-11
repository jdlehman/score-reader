package java.awt.geom;
import java.awt.Rectangle;
import java.awt.Shape;
/** Minimal java.awt.geom.RectangularShape. */
public abstract class RectangularShape implements Shape, Cloneable {
    protected RectangularShape() {}
    public abstract double getX();
    public abstract double getY();
    public abstract double getWidth();
    public abstract double getHeight();
    public abstract boolean isEmpty();
    public abstract void setFrame(double x, double y, double w, double h);
    public void setFrame(Point2D loc, java.awt.geom.Dimension2D size) { setFrame(loc.getX(), loc.getY(), size.getWidth(), size.getHeight()); }
    public void setFrame(Rectangle2D r) { setFrame(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
    public Rectangle2D getFrame() { return new Rectangle2D.Double(getX(), getY(), getWidth(), getHeight()); }
    public double getMinX() { return getX(); }
    public double getMinY() { return getY(); }
    public double getMaxX() { return getX() + getWidth(); }
    public double getMaxY() { return getY() + getHeight(); }
    public double getCenterX() { return getX() + getWidth() / 2.0; }
    public double getCenterY() { return getY() + getHeight() / 2.0; }
    // §31 (DIAG36): JDK RectangularShape.getBounds, verbatim from OpenJDK 25.
    // The old truncation ((int) getX(), (int) getWidth(), ...) shrank the
    // fill window by up to 1 px on the right/bottom: the §30 ROUND 33
    // ellipse fill missed the right/bottom strips entirely (the 791 px
    // left on Wasm after the fill in DIAG36 live counts).
    @Override public Rectangle getBounds() {
        double width = getWidth();
        double height = getHeight();
        if (width < 0 || height < 0) {
            return new Rectangle();
        }
        double x = getX();
        double y = getY();
        double x1 = Math.floor(x);
        double y1 = Math.floor(y);
        double x2 = Math.ceil(x + width);
        double y2 = Math.ceil(y + height);
        return new Rectangle((int) x1, (int) y1,
                                      (int) (x2 - x1), (int) (y2 - y1));
    }
    @Override public Rectangle2D getBounds2D() { return new Rectangle2D.Double(getX(), getY(), getWidth(), getHeight()); }
    @Override public boolean contains(double x, double y) { return x >= getX() && y >= getY() && x < getMaxX() && y < getMaxY(); }
    @Override public boolean contains(Point2D p) { return contains(p.getX(), p.getY()); }
    @Override public boolean intersects(double x, double y, double w, double h) {
        return x + w > getX() && y + h > getY() && x < getMaxX() && y < getMaxY();
    }
    @Override public boolean intersects(Rectangle2D r) { return intersects(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
    // §31 (DIAG36): four-corner test. The old two-corner form
    // (contains(x,y) && contains(x+w,y+h)) is NOT JDK-faithful: JDK
    // Ellipse2D and RoundRectangle2D both override contains(x,y,w,h)
    // with the four-corner test (verified on JDK 25: rect [6,1,3,3] on
    // ellipse (0,0,10,10) is false — both diagonal corners inside, one
    // off-diagonal corner outside — while two-corner says true). For a
    // rectangle the two forms coincide, so this changes nothing for
    // rectangular shapes; Ellipse2D carries its own verbatim override.
    @Override public boolean contains(double x, double y, double w, double h) {
        return contains(x, y) && contains(x + w, y)
                && contains(x, y + h) && contains(x + w, y + h);
    }
    @Override public boolean contains(Rectangle2D r) { return contains(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
    @Override public PathIterator getPathIterator(java.awt.geom.AffineTransform at) { return null; }
    @Override public PathIterator getPathIterator(java.awt.geom.AffineTransform at, double flatness) { return null; }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
}
