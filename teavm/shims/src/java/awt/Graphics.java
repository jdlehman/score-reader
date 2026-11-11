package java.awt;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.awt.image.ImageObserver;
/** Minimal java.awt.Graphics. */
public abstract class Graphics {
    public abstract Graphics create();
    public abstract void translate(int x, int y);
    public abstract Color getColor();
    public abstract void setColor(Color c);
    public abstract void setPaintMode();
    public abstract void setXORMode(Color c1);
    public abstract Font getFont();
    public abstract void setFont(Font font);
    public abstract java.awt.FontMetrics getFontMetrics();
    public abstract java.awt.FontMetrics getFontMetrics(Font f);
    public abstract Rectangle getClipBounds();
    public abstract void clipRect(int x, int y, int width, int height);
    public abstract void setClip(int x, int y, int width, int height);
    public abstract java.awt.Shape getClip();
    public abstract void setClip(java.awt.Shape clip);
    public abstract void copyArea(int x, int y, int width, int height, int dx, int dy);
    public abstract void drawLine(int x1, int y1, int x2, int y2);
    public abstract void fillRect(int x, int y, int width, int height);
    public abstract void clearRect(int x, int y, int width, int height);
    public abstract void drawRoundRect(int x, int y, int width, int height, int arcWidth, int arcHeight);
    public abstract void fillRoundRect(int x, int y, int width, int height, int arcWidth, int arcHeight);
    public abstract void drawOval(int x, int y, int width, int height);
    public abstract void fillOval(int x, int y, int width, int height);
    public abstract void drawArc(int x, int y, int width, int height, int startAngle, int arcAngle);
    public abstract void fillArc(int x, int y, int width, int height, int startAngle, int arcAngle);
    public abstract void drawPolyline(int[] xPoints, int[] yPoints, int nPoints);
    public abstract void drawPolygon(int[] xPoints, int[] yPoints, int nPoints);
    public abstract void fillPolygon(int[] xPoints, int[] yPoints, int nPoints);
    public abstract void drawString(String str, int x, int y);
    public abstract void drawChars(char[] data, int offset, int length, int x, int y);
    public abstract void drawBytes(byte[] data, int offset, int length, int x, int y);
    public abstract boolean drawImage(Image img, int x, int y, ImageObserver observer);
    public abstract boolean drawImage(Image img, int x, int y, int width, int height, ImageObserver observer);
    public abstract boolean drawImage(Image img, int x, int y, Color bgcolor, ImageObserver observer);
    public abstract boolean drawImage(Image img, int x, int y, int width, int height, Color bgcolor, ImageObserver observer);
    public abstract boolean drawImage(Image img, int dx1, int dy1, int dx2, int dy2, int sx1, int sy1, int sx2, int sy2, ImageObserver observer);
    public abstract boolean drawImage(Image img, int dx1, int dy1, int dx2, int dy2, int sx1, int sy1, int sx2, int sy2, Color bgcolor, ImageObserver observer);
    public abstract void dispose();
    public void drawRect(int x, int y, int w, int h) { drawLine(x, y, x + w, y); drawLine(x + w, y, x + w, y + h); drawLine(x + w, y + h, x, y + h); drawLine(x, y + h, x, y); }
    public void fill3DRect(int x, int y, int w, int h, boolean raised) { fillRect(x, y, w, h); }
    public void draw3DRect(int x, int y, int w, int h, boolean raised) { drawRect(x, y, w, h); }
    public void setClip(Rectangle r) { setClip(r.x, r.y, r.width, r.height); }
    public void drawPolygon(Polygon p) { drawPolygon(p.xpoints, p.ypoints, p.npoints); }
    public void fillPolygon(Polygon p) { fillPolygon(p.xpoints, p.ypoints, p.npoints); }
    public void drawString(java.text.AttributedCharacterIterator iterator, int x, int y) { drawString("", x, y); }
    public boolean hitClip(int x, int y, int w, int h) { return true; }
    public Rectangle getClipBounds(Rectangle r) { return getClipBounds(); }
}
