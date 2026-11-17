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
    // §31: JDK RectangularShape.getBounds, from OpenJDK 25: floor and ceil, so the bounds cover
    // the whole shape (§30's ellipse fill needs its right and bottom pixels).
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
    // §31: the four-corner test, as JDK 25's Ellipse2D and RoundRectangle2D use (two diagonal
    // corners inside isn't enough: rect [6,1,3,3] on ellipse (0,0,10,10) is outside). For a
    // rectangle it equals the two-corner test; Ellipse2D carries its own copy of the JDK's.
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
