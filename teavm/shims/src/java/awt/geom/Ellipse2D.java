package java.awt.geom;
/** Minimal java.awt.geom.Ellipse2D. */
public abstract class Ellipse2D extends RectangularShape {
    protected Ellipse2D() {}
    // §31 (DIAG36): JDK-faithful geometry, copied verbatim from OpenJDK 25
    // (java.desktop/java/awt/geom/Ellipse2D.java). The shim previously had
    // NO contains override, so it inherited RectangularShape's
    // bounding-rectangle test: fill(Shape) on an ellipse erased the whole
    // rectangle, including ~192 corner pixels per head ellipse, which is
    // the §30 head-erasure overshoot (Wasm erased ~800 px too much).
    @Override
    public boolean contains(double x, double y) {
        // Normalize the coordinates compared to the ellipse
        // having a center at 0,0 and a radius of 0.5.
        double ellw = getWidth();
        if (ellw <= 0.0) {
            return false;
        }
        double normx = (x - getX()) / ellw - 0.5;
        double ellh = getHeight();
        if (ellh <= 0.0) {
            return false;
        }
        double normy = (y - getY()) / ellh - 0.5;
        return (normx * normx + normy * normy) < 0.25;
    }
    @Override
    public boolean contains(double x, double y, double w, double h) {
        return (contains(x, y) &&
                contains(x + w, y) &&
                contains(x, y + h) &&
                contains(x + w, y + h));
    }
    @Override
    public boolean intersects(double x, double y, double w, double h) {
        if (w <= 0.0 || h <= 0.0) {
            return false;
        }
        // Normalize the rectangular coordinates compared to the ellipse
        // having a center at 0,0 and a radius of 0.5.
        double ellw = getWidth();
        if (ellw <= 0.0) {
            return false;
        }
        double normx0 = (x - getX()) / ellw - 0.5;
        double normx1 = normx0 + w / ellw;
        double ellh = getHeight();
        if (ellh <= 0.0) {
            return false;
        }
        double normy0 = (y - getY()) / ellh - 0.5;
        double normy1 = normy0 + h / ellh;
        // find nearest x (left edge, right edge, 0.0)
        // find nearest y (top edge, bottom edge, 0.0)
        // if nearest x,y is inside circle of radius 0.5, then intersects
        double nearx, neary;
        if (normx0 > 0.0) {
            // center to left of X extents
            nearx = normx0;
        } else if (normx1 < 0.0) {
            // center to right of X extents
            nearx = normx1;
        } else {
            nearx = 0.0;
        }
        if (normy0 > 0.0) {
            // center above Y extents
            neary = normy0;
        } else if (normy1 < 0.0) {
            // center below Y extents
            neary = normy1;
        } else {
            neary = 0.0;
        }
        return (nearx * nearx + neary * neary) < 0.25;
    }
    public static class Double extends Ellipse2D {
        public double x, y, width, height;
        public Double() {}
        public Double(double x, double y, double w, double h) { this.x = x; this.y = y; width = w; height = h; }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public double getWidth() { return width; }
        @Override public double getHeight() { return height; }
        @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
        @Override public void setFrame(double x, double y, double w, double h) { this.x = x; this.y = y; width = w; height = h; }
    }
    public static class Float extends Ellipse2D {
        public float x, y, width, height;
        public Float() {}
        public Float(float x, float y, float w, float h) { this.x = x; this.y = y; width = w; height = h; }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public double getWidth() { return width; }
        @Override public double getHeight() { return height; }
        @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
        @Override public void setFrame(double x, double y, double w, double h) { this.x = (float) x; this.y = (float) y; width = (float) w; height = (float) h; }
    }
}
