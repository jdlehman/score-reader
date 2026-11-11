package java.awt.geom;
/** Minimal java.awt.geom.RoundRectangle2D. */
public abstract class RoundRectangle2D extends RectangularShape {
    public abstract double getArcWidth();
    public abstract double getArcHeight();
    public abstract void setRoundRect(double x, double y, double w, double h, double arcWidth, double arcHeight);
    public void setRoundRect(RoundRectangle2D rr) { setRoundRect(rr.getX(), rr.getY(), rr.getWidth(), rr.getHeight(), rr.getArcWidth(), rr.getArcHeight()); }
    public static class Double extends RoundRectangle2D {
        public double x, y, width, height, arcwidth, archeight;
        public Double() {}
        public Double(double x, double y, double w, double h, double arcWidth, double arcHeight) {
            this.x = x; this.y = y; width = w; height = h; arcwidth = arcWidth; archeight = arcHeight;
        }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public double getWidth() { return width; }
        @Override public double getHeight() { return height; }
        @Override public double getArcWidth() { return arcwidth; }
        @Override public double getArcHeight() { return archeight; }
        @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
        @Override public void setFrame(double x, double y, double w, double h) { this.x = x; this.y = y; width = w; height = h; }
        @Override public void setRoundRect(double x, double y, double w, double h, double arcWidth, double arcHeight) {
            this.x = x; this.y = y; width = w; height = h; arcwidth = arcWidth; archeight = arcHeight;
        }
        @Override public Rectangle2D getBounds2D() { return new Rectangle2D.Double(x, y, width, height); }
    }
    public static class Float extends RoundRectangle2D {
        public float x, y, width, height, arcwidth, archeight;
        public Float() {}
        public Float(float x, float y, float w, float h, float arcWidth, float arcHeight) {
            this.x = x; this.y = y; width = w; height = h; arcwidth = arcWidth; archeight = arcHeight;
        }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public double getWidth() { return width; }
        @Override public double getHeight() { return height; }
        @Override public double getArcWidth() { return arcwidth; }
        @Override public double getArcHeight() { return archeight; }
        @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
        @Override public void setFrame(double x, double y, double w, double h) { this.x = (float) x; this.y = (float) y; width = (float) w; height = (float) h; }
        @Override public void setRoundRect(double x, double y, double w, double h, double arcWidth, double arcHeight) {
            this.x = (float) x; this.y = (float) y; width = (float) w; height = (float) h;
            arcwidth = (float) arcWidth; archeight = (float) arcHeight;
        }
        @Override public Rectangle2D getBounds2D() { return new Rectangle2D.Float(x, y, width, height); }
    }
}
