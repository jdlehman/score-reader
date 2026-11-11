package java.awt.image;
import java.awt.Color;
import java.awt.Composite;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GraphicsConfiguration;
import java.awt.Paint;
import java.awt.Rectangle;
import java.awt.RenderingHints;
import java.awt.Shape;
import java.awt.Stroke;
import java.awt.font.FontRenderContext;
import java.awt.font.GlyphVector;
import java.awt.geom.AffineTransform;
import java.awt.geom.PathIterator;
import java.awt.image.renderable.RenderableImage;
import java.text.AttributedCharacterIterator;
import java.util.Map;
/** A Graphics2D that draws into a BufferedImage's pixels (grey or int).
 *  Only the ops Audiveris's reading path uses are real (fillRect/drawLine/fill/draw
 *  of rectangles and paths); text/font ops are no-ops. */
public class BufferedImageGraphics extends Graphics2D {
    private final BufferedImage img;
    private Color color = Color.BLACK;
    private Font font = new Font("Dialog", Font.PLAIN, 12);
    private Stroke stroke;
    private AffineTransform transform = new AffineTransform();
    private int tx, ty;
    public BufferedImageGraphics(BufferedImage img) { this.img = img; }
    private void setPixel(int x, int y) {
        x += tx; y += ty;
        if (x < 0 || y < 0 || x >= img.getWidth() || y >= img.getHeight()) return;
        img.setRGB(x, y, (color.getAlpha() << 24) | (color.getRed() << 16) | (color.getGreen() << 8) | color.getBlue());
    }
    @Override public Graphics create() { return new BufferedImageGraphics(img); }
    @Override public void translate(int x, int y) { tx += x; ty += y; }
    @Override public Color getColor() { return color; }
    @Override public void setColor(Color c) { if (c != null) color = c; }
    @Override public void setPaintMode() {}
    @Override public void setXORMode(Color c1) {}
    @Override public Font getFont() { return font; }
    @Override public void setFont(Font f) { if (f != null) font = f; }
    @Override public java.awt.FontMetrics getFontMetrics() { return new java.awt.FontMetrics(font); }
    @Override public java.awt.FontMetrics getFontMetrics(Font f) { return new java.awt.FontMetrics(f); }
    @Override public Rectangle getClipBounds() { return new Rectangle(0, 0, img.getWidth(), img.getHeight()); }
    @Override public void clipRect(int x, int y, int w, int h) {}
    @Override public void setClip(int x, int y, int w, int h) {}
    @Override public Shape getClip() { return null; }
    @Override public void setClip(Shape clip) {}
    @Override public void copyArea(int x, int y, int w, int h, int dx, int dy) {}
    @Override public void drawLine(int x1, int y1, int x2, int y2) {
        int dx = Math.abs(x2 - x1), dy = Math.abs(y2 - y1);
        int sx = x1 < x2 ? 1 : -1, sy = y1 < y2 ? 1 : -1, err = dx - dy;
        while (true) {
            setPixel(x1, y1);
            if (x1 == x2 && y1 == y2) break;
            int e2 = 2 * err;
            if (e2 > -dy) { err -= dy; x1 += sx; }
            if (e2 < dx) { err += dx; y1 += sy; }
        }
    }
    @Override public void fillRect(int x, int y, int w, int h) {
        for (int yy = y; yy < y + h; yy++)
            for (int xx = x; xx < x + w; xx++) setPixel(xx, yy);
    }
    @Override public void clearRect(int x, int y, int w, int h) {
        Color old = color; color = Color.WHITE; fillRect(x, y, w, h); color = old;
    }
    @Override public void drawRoundRect(int x, int y, int w, int h, int aw, int ah) { drawRect(x, y, w, h); }
    @Override public void fillRoundRect(int x, int y, int w, int h, int aw, int ah) { fillRect(x, y, w, h); }
    @Override public void drawOval(int x, int y, int w, int h) {
        for (int a = 0; a < 360; a++) {
            double t = Math.toRadians(a);
            setPixel(x + w / 2 + (int) (Math.cos(t) * w / 2), y + h / 2 + (int) (Math.sin(t) * h / 2));
        }
    }
    @Override public void fillOval(int x, int y, int w, int h) {
        for (int yy = 0; yy < h; yy++)
            for (int xx = 0; xx < w; xx++) {
                double dx = (xx - w / 2.0) / (w / 2.0), dy = (yy - h / 2.0) / (h / 2.0);
                if (dx * dx + dy * dy <= 1) setPixel(x + xx, y + yy);
            }
    }
    @Override public void drawArc(int x, int y, int w, int h, int start, int arc) {}
    @Override public void fillArc(int x, int y, int w, int h, int start, int arc) {}
    @Override public void drawPolyline(int[] xs, int[] ys, int n) {
        for (int i = 1; i < n; i++) drawLine(xs[i - 1], ys[i - 1], xs[i], ys[i]);
    }
    @Override public void drawPolygon(int[] xs, int[] ys, int n) {
        drawPolyline(xs, ys, n);
        if (n > 1) drawLine(xs[n - 1], ys[n - 1], xs[0], ys[0]);
    }
    @Override public void fillPolygon(int[] xs, int[] ys, int n) {
        Rectangle b = new Rectangle(xs[0], ys[0], 0, 0);
        for (int i = 1; i < n; i++) b.add(xs[i], ys[i]);
        java.awt.Polygon p = new java.awt.Polygon(xs, ys, n);
        for (int yy = b.y; yy < b.y + b.height; yy++)
            for (int xx = b.x; xx < b.x + b.width; xx++)
                if (p.contains(xx, yy)) setPixel(xx, yy);
    }
    @Override public void drawString(String str, int x, int y) {}
    @Override public void drawChars(char[] d, int o, int l, int x, int y) {}
    @Override public void drawBytes(byte[] d, int o, int l, int x, int y) {}
    @Override public boolean drawImage(java.awt.Image im, int x, int y, ImageObserver o) {
        if (im instanceof BufferedImage bi) {
            for (int yy = 0; yy < bi.getHeight(); yy++)
                for (int xx = 0; xx < bi.getWidth(); xx++) {
                    int argb = bi.getRGB(xx, yy);
                    Color old = color;
                    // TEAVM: no Color(int, boolean) ctor; compose from components instead.
                    color = new Color((argb >> 16) & 0xFF, (argb >> 8) & 0xFF, argb & 0xFF, (argb >> 24) & 0xFF);
                    setPixel(x + xx, y + yy);
                    color = old;
                }
            return true;
        }
        return false;
    }
    @Override public boolean drawImage(java.awt.Image im, int x, int y, int w, int h, ImageObserver o) { return drawImage(im, x, y, o); }
    @Override public boolean drawImage(java.awt.Image im, int x, int y, Color bg, ImageObserver o) { return drawImage(im, x, y, o); }
    @Override public boolean drawImage(java.awt.Image im, int x, int y, int w, int h, Color bg, ImageObserver o) { return drawImage(im, x, y, o); }
    @Override public boolean drawImage(java.awt.Image im, int dx1, int dy1, int dx2, int dy2, int sx1, int sy1, int sx2, int sy2, ImageObserver o) { return drawImage(im, dx1, dy1, o); }
    @Override public boolean drawImage(java.awt.Image im, int dx1, int dy1, int dx2, int dy2, int sx1, int sy1, int sx2, int sy2, Color bg, ImageObserver o) { return drawImage(im, dx1, dy1, o); }
    @Override public void dispose() {}
    @Override public void draw(Shape s) {
        PathIterator it = s.getPathIterator(transform);
        double[] c = new double[6];
        double sx = 0, sy = 0, lx = 0, ly = 0;
        while (!it.isDone()) {
            int t = it.currentSegment(c);
            switch (t) {
                case PathIterator.SEG_MOVETO -> { sx = lx = c[0]; sy = ly = c[1]; }
                case PathIterator.SEG_LINETO -> { drawLine((int) lx, (int) ly, (int) c[0], (int) c[1]); lx = c[0]; ly = c[1]; }
                case PathIterator.SEG_CLOSE -> drawLine((int) lx, (int) ly, (int) sx, (int) sy);
                default -> {}
            }
            it.next();
        }
    }
    @Override public void fill(Shape s) {
        Rectangle b = s.getBounds();
        if ((b.width <= 0) || (b.height <= 0)) return;
        // Scanline fill (§26, TeaVM grid gap): the old per-pixel loop called
        // s.contains() once per pixel — O(pixels * edges). After the §26
        // Area fix, a real page-minus-staff area has thousands of edges, so
        // StemScaler.getBuffer()'s g.fill(area) (2480x3509 page) stalled
        // for 5+ minutes at 100% CPU. The scanline sweep below reproduces
        // s.contains(xx+0.5, yy+0.5) exactly (same half-open crossing rule
        // as Path2D.contains: an edge contributes iff it crosses the
        // scanline in the half-open y-range and its x-intercept is strictly
        // right of the pixel centre) in O(rows * edges + filled pixels).
        // Falls back to the per-pixel loop when the shape has no usable
        // flattened iterator (e.g. shim Ellipse2D: RectangularShape
        // getPathIterator returns null) or yields a curve segment.
        PathIterator it;
        try {
            it = s.getPathIterator(transform, 0.25);
        } catch (Exception ex) {
            fillPixels(s, b);
            return;
        }
        if (it == null) {
            fillPixels(s, b);
            return;
        }
        java.util.ArrayList<double[]> edges = new java.util.ArrayList<>();
        double[] c = new double[6];
        double sx = 0, sy = 0, lx = 0, ly = 0;
        boolean haveStart = false;
        while (!it.isDone()) {
            int t = it.currentSegment(c);
            switch (t) {
                case PathIterator.SEG_MOVETO -> {
                    sx = lx = c[0];
                    sy = ly = c[1];
                    haveStart = true;
                }
                case PathIterator.SEG_LINETO -> {
                    if (haveStart) edges.add(new double[]{lx, ly, c[0], c[1]});
                    lx = c[0];
                    ly = c[1];
                }
                case PathIterator.SEG_CLOSE -> {
                    if (haveStart && ((lx != sx) || (ly != sy))) edges.add(new double[]{lx, ly, sx, sy});
                    lx = sx;
                    ly = sy;
                }
                default -> {
                    fillPixels(s, b);
                    return;
                }
            }
            it.next();
        }
        if (edges.isEmpty()) return;
        int rule = it.getWindingRule();
        boolean evenOdd = (rule == PathIterator.WIND_EVEN_ODD);
        // Per-scanline sweep. crossings: [x-intercept, dir] (+1 upward edge,
        // -1 downward edge, per the half-open y-range of Path2D.contains).
        for (int yy = b.y; yy < b.y + b.height; yy++) {
            double y = yy + 0.5;
            double[][] cross = new double[edges.size()][2];
            int n = 0;
            for (double[] e : edges) {
                double y1 = e[1], y2 = e[3];
                int dir;
                if ((y1 <= y) && (y2 > y)) dir = 1;
                else if ((y2 <= y) && (y1 > y)) dir = -1;
                else continue;
                cross[n][0] = e[0] + ((y - y1) * (e[2] - e[0]) / (y2 - y1));
                cross[n][1] = dir;
                n++;
            }
            if (n == 0) continue;
            java.util.Arrays.sort(cross, 0, n,
                    (a, b2) -> Double.compare(a[0], b2[0]));
            // wn(px) = sum of dirs over crossings with x-intercept > px
            // (even-odd: count of such crossings, parity). Sweep left to
            // right, dropping each crossing once its x-intercept <= px.
            int wn = 0;
            for (int i = 0; i < n; i++) wn += (int) cross[i][1];
            int remaining = n;
            int ci = 0;
            for (int xx = b.x; xx < b.x + b.width; xx++) {
                double px = xx + 0.5;
                while ((ci < n) && (cross[ci][0] <= px)) {
                    wn -= (int) cross[ci][1];
                    remaining--;
                    ci++;
                }
                boolean inside = evenOdd ? ((remaining % 2) == 1) : (wn != 0);
                if (inside) setPixel(xx, yy);
            }
        }
    }

    /** The old per-pixel fill (kept as the fallback for shapes without a
     * flattened iterator). */
    private void fillPixels(Shape s, Rectangle b) {
        for (int yy = b.y; yy < b.y + b.height; yy++)
            for (int xx = b.x; xx < b.x + b.width; xx++)
                if (s.contains(xx + 0.5, yy + 0.5)) setPixel(xx, yy);
    }
    @Override public boolean drawImage(java.awt.Image im, AffineTransform xform, ImageObserver obs) { return drawImage(im, 0, 0, obs); }
    @Override public void drawImage(BufferedImage im, BufferedImageOp op, int x, int y) { drawImage(im, x, y, null); }
    @Override public void drawRenderedImage(RenderedImage im, AffineTransform xform) {}
    @Override public void drawRenderableImage(RenderableImage im, AffineTransform xform) {}
    @Override public void drawString(String str, float x, float y) {}
    @Override public void drawString(AttributedCharacterIterator it, float x, float y) {}
    @Override public void drawGlyphVector(GlyphVector g, float x, float y) {}
    @Override public boolean hit(Rectangle r, Shape s, boolean onStroke) { return false; }
    @Override public GraphicsConfiguration getDeviceConfiguration() { return null; }
    @Override public void setComposite(Composite comp) {}
    @Override public void setPaint(Paint paint) { if (paint instanceof Color c) color = c; }
    @Override public void setStroke(Stroke s) { stroke = s; }
    @Override public void setRenderingHint(RenderingHints.Key k, Object v) {}
    @Override public Object getRenderingHint(RenderingHints.Key k) { return null; }
    @Override public void setRenderingHints(Map<?, ?> hints) {}
    @Override public void addRenderingHints(Map<?, ?> hints) {}
    @Override public RenderingHints getRenderingHints() { return new RenderingHints(null); }
    @Override public void translate(double tx, double ty) { this.tx += (int) tx; this.ty += (int) ty; }
    @Override public void rotate(double theta) {}
    @Override public void rotate(double theta, double x, double y) {}
    @Override public void scale(double sx, double sy) {}
    @Override public void shear(double shx, double shy) {}
    @Override public void transform(AffineTransform Tx) { transform.concatenate(Tx); }
    @Override public void setTransform(AffineTransform Tx) { transform = new AffineTransform(Tx); }
    @Override public AffineTransform getTransform() { return new AffineTransform(transform); }
    @Override public Paint getPaint() { return color; }
    @Override public Composite getComposite() { return null; }
    @Override public void setBackground(Color c) {}
    @Override public Color getBackground() { return Color.WHITE; }
    @Override public Stroke getStroke() { return stroke; }
    @Override public void clip(Shape s) {}
    @Override public FontRenderContext getFontRenderContext() { return new FontRenderContext(transform, false, false); }
}
