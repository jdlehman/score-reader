package java.awt;
import java.awt.geom.Point2D;
import java.awt.geom.Rectangle2D;
/** Minimal java.awt.Rectangle (integer bounds; Audiveris uses fields + contains/intersects/union). */
public class Rectangle extends Rectangle2D {
    public int x, y, width, height;
    public Rectangle() {}
    public Rectangle(int x, int y, int w, int h) { this.x = x; this.y = y; width = w; height = h; }
    public Rectangle(int w, int h) { this(0, 0, w, h); }
    public void setFrame(double x, double y, double w, double h) {
        this.x = (int) x; this.y = (int) y; width = (int) w; height = (int) h;
    }
    public Rectangle(Point p) { this(p.x, p.y, 0, 0); }
    public Rectangle(Point p, Dimension d) { this(p.x, p.y, d.width, d.height); }
    public Rectangle(Dimension d) { this(0, 0, d.width, d.height); }
    public Rectangle(Rectangle r) { this(r.x, r.y, r.width, r.height); }
    public Rectangle(Rectangle2D r) { this((int) r.getX(), (int) r.getY(), (int) r.getWidth(), (int) r.getHeight()); }
    @Override public double getX() { return x; }
    @Override public double getY() { return y; }
    @Override public double getWidth() { return width; }
    @Override public double getHeight() { return height; }
    @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
    @Override public void setRect(double x, double y, double w, double h) {
        this.x = (int) x; this.y = (int) y; width = (int) w; height = (int) h;
    }
    public void setBounds(int x, int y, int w, int h) { this.x = x; this.y = y; width = w; height = h; }
    public void setBounds(Rectangle r) { setBounds(r.x, r.y, r.width, r.height); }
    public Rectangle getBounds() { return new Rectangle(x, y, width, height); }
    public Point getLocation() { return new Point(x, y); }
    public void setLocation(int x, int y) { this.x = x; this.y = y; }
    public void setLocation(Point p) { setLocation(p.x, p.y); }
    public void setSize(int w, int h) { width = w; height = h; }
    public void setSize(Dimension d) { setSize(d.width, d.height); }
    public Dimension getSize() { return new Dimension(width, height); }
    public void translate(int dx, int dy) { x += dx; y += dy; }
    public void grow(int h, int v) { x -= h; y -= v; width += 2 * h; height += 2 * v; }
    public boolean contains(int px, int py) { return px >= x && px < x + width && py >= y && py < y + height; }
    public boolean contains(Point p) { return contains(p.x, p.y); }
    // TEAVM §24 trap 4: JDK Rectangle.contains(int,int,int,int) is INCLUSIVE
    // on the far edge (x+w <= maxX, y+h <= maxY) and false for w<=0/h<=0.
    // The shim previously had no int overload, so contains(Rectangle)
    // resolved to Rectangle2D.contains(double,double,double,double), whose
    // half-open point test (contains(x+w,y+h)) rejected every section
    // touching the char box's right or bottom edge — 741/741 missed
    // sections in TextBuilder.retrieveSections. Verified against JDK 25.
    public boolean contains(int x, int y, int w, int h) {
        return w > 0 && h > 0 && x >= this.x && y >= this.y
                && (x + w) <= this.x + width && (y + h) <= this.y + height;
    }
    public boolean contains(Rectangle r) { return contains(r.x, r.y, r.width, r.height); }
    public boolean intersects(Rectangle r) { return intersects(r.x, r.y, r.width, r.height); }
    public Rectangle union(Rectangle r) {
        int x0 = Math.min(x, r.x), y0 = Math.min(y, r.y);
        int x1 = Math.max(x + width, r.x + r.width), y1 = Math.max(y + height, r.y + r.height);
        return new Rectangle(x0, y0, x1 - x0, y1 - y0);
    }
    public Rectangle intersection(Rectangle r) {
        int x0 = Math.max(x, r.x), y0 = Math.max(y, r.y);
        int x1 = Math.min(x + width, r.x + r.width), y1 = Math.min(y + height, r.y + r.height);
        return new Rectangle(x0, y0, Math.max(0, x1 - x0), Math.max(0, y1 - y0));
    }
    public void add(int px, int py) { add((double) px, (double) py); }
    public void add(Point p) { add(p.x, p.y); }
    public void add(Rectangle r) { add((Rectangle2D) r); }
    @Override public boolean equals(Object o) {
        if (o instanceof Rectangle r) return x == r.x && y == r.y && width == r.width && height == r.height;
        return false;
    }
    @Override public int hashCode() { return x * 31 * 31 * 31 + y * 31 * 31 + width * 31 + height; }
    @Override public String toString() { return "Rectangle[" + x + ", " + y + ", " + width + "x" + height + "]"; }
    public boolean intersectsLine(double x1, double y1, double x2, double y2) { return false; }
}
