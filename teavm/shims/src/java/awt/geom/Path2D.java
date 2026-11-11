package java.awt.geom;
import java.awt.Shape;
import java.util.ArrayList;
import java.util.List;
/**
 * Minimal java.awt.geom.Path2D (double/float storage, segment list).
 *
 * §26 (TeaVM grid gap): contains()/intersects() used to be bounds-based
 * (getBounds2D().contains), which is wrong for any non-rectangular path
 * (e.g. slanted beam parallelograms: the bounds box counts pixels outside
 * the shape). They are now exact point-in-path / rect tests on the
 * flattened segments, honouring the winding rule. getPathIterator(at,
 * flatness) now actually flattens curves (it used to ignore flatness).
 *
 * Flattened-polygon results are cached; the cache is keyed on
 * (coords.size, types.size, windingRule, flatness) and is cleared by
 * transform()/append()/setWindingRule(). Every other mutator only appends
 * to coords/types (or clears them), so the size check catches it.
 */
public abstract class Path2D implements Shape, Cloneable {
    public static final int WIND_EVEN_ODD = PathIterator.WIND_EVEN_ODD;
    public static final int WIND_NON_ZERO = PathIterator.WIND_NON_ZERO;
    int windingRule;
    final ArrayList<java.lang.Double> coords = new ArrayList<>();
    final ArrayList<Integer> types = new ArrayList<>();
    // Flattened-polygon cache (see class note).
    private transient List<double[][]> flatCachePolys;
    private transient double flatCacheFlatness = java.lang.Double.NaN;
    private transient int flatCacheCoords = -1;
    private transient int flatCacheTypes = -1;
    private transient int flatCacheRule = -1;

    protected Path2D(int windingRule) { this.windingRule = windingRule; }
    protected Path2D() { this(WIND_NON_ZERO); }
    public abstract void moveTo(double x, double y);
    public abstract void lineTo(double x, double y);
    public abstract void quadTo(double x1, double y1, double x2, double y2);
    public abstract void curveTo(double x1, double y1, double x2, double y2, double x3, double y3);
    public abstract void closePath();
    public void append(Shape s, boolean connect) {
        invalidateFlatCache();
        PathIterator it = s.getPathIterator(null);
        double[] c = new double[6];
        while (!it.isDone()) {
            int t = it.currentSegment(c);
            switch (t) {
                case PathIterator.SEG_MOVETO -> { if (!connect || types.isEmpty()) moveTo(c[0], c[1]); else lineTo(c[0], c[1]); }
                case PathIterator.SEG_LINETO -> lineTo(c[0], c[1]);
                case PathIterator.SEG_QUADTO -> quadTo(c[0], c[1], c[2], c[3]);
                case PathIterator.SEG_CUBICTO -> curveTo(c[0], c[1], c[2], c[3], c[4], c[5]);
                case PathIterator.SEG_CLOSE -> closePath();
            }
            it.next();
        }
    }
    public void append(PathIterator it, boolean connect) {
        invalidateFlatCache();
        double[] c = new double[6];
        while (!it.isDone()) {
            int t = it.currentSegment(c);
            switch (t) {
                case PathIterator.SEG_MOVETO -> { if (!connect || types.isEmpty()) moveTo(c[0], c[1]); else lineTo(c[0], c[1]); }
                case PathIterator.SEG_LINETO -> lineTo(c[0], c[1]);
                case PathIterator.SEG_QUADTO -> quadTo(c[0], c[1], c[2], c[3]);
                case PathIterator.SEG_CUBICTO -> curveTo(c[0], c[1], c[2], c[3], c[4], c[5]);
                case PathIterator.SEG_CLOSE -> closePath();
            }
            it.next();
        }
    }
    public int getWindingRule() { return windingRule; }
    public void setWindingRule(int r) { windingRule = r; invalidateFlatCache(); }
    public Point2D getCurrentPoint() {
        int n = coords.size();
        if (n < 2) return null;
        return new Point2D.Double(coords.get(n - 2), coords.get(n - 1));
    }
    public void reset() { coords.clear(); types.clear(); invalidateFlatCache(); }
    public void transform(AffineTransform at) {
        invalidateFlatCache();
        double[] all = new double[coords.size()];
        for (int i = 0; i < all.length; i++) all[i] = coords.get(i);
        double[] out = new double[all.length];
        at.transform(all, 0, out, 0, all.length / 2);
        coords.clear();
        for (double v : out) coords.add(v);
    }
    @Override public Rectangle2D getBounds2D() {
        if (coords.isEmpty()) return new Rectangle2D.Double();
        double x0 = java.lang.Double.MAX_VALUE, y0 = java.lang.Double.MAX_VALUE, x1 = -java.lang.Double.MAX_VALUE, y1 = -java.lang.Double.MAX_VALUE;
        for (int i = 0; i + 1 < coords.size(); i += 2) {
            x0 = Math.min(x0, coords.get(i)); y0 = Math.min(y0, coords.get(i + 1));
            x1 = Math.max(x1, coords.get(i)); y1 = Math.max(y1, coords.get(i + 1));
        }
        return new Rectangle2D.Double(x0, y0, x1 - x0, y1 - y0);
    }
    @Override public java.awt.Rectangle getBounds() { return getBounds2D().getBounds(); }

    // ------------------------------------------------------------------
    // Exact geometry (§26). All tests run on the flattened polygons
    // (curves subdivided to the requested flatness); the winding rule is
    // honoured. A point exactly on an edge counts as inside.
    // ------------------------------------------------------------------

    /** Flattened polygons of this path (each implicitly closed, >= 3 vertices). */
    public List<double[][]> flattenedPolygons(double flatness) {
        ensureFlatCache(flatness);
        return flatCachePolys;
    }

    private void invalidateFlatCache() {
        flatCachePolys = null;
        flatCacheFlatness = java.lang.Double.NaN;
        flatCacheCoords = -1;
        flatCacheTypes = -1;
        flatCacheRule = -1;
    }

    private void ensureFlatCache(double flatness) {
        if ((flatCachePolys != null) && (flatCacheFlatness == flatness)
                && (flatCacheCoords == coords.size()) && (flatCacheTypes == types.size())
                && (flatCacheRule == windingRule)) {
            return;
        }
        List<double[][]> polys = new ArrayList<>();
        // Walk the segment list, subdividing curves.
        ArrayList<double[]> run = null;
        boolean runClosed = false;
        double startX = 0, startY = 0, curX = 0, curY = 0;
        int base = 0;
        for (int s = 0; s < types.size(); s++) {
            int t = types.get(s);
            int n = ncoords(t);
            double[] c = new double[n];
            for (int i = 0; i < n; i++) c[i] = coords.get(base + i);
            base += n;
            switch (t) {
                case PathIterator.SEG_MOVETO -> {
                    if (run != null) finishRun(run, runClosed, polys);
                    run = new ArrayList<>();
                    runClosed = false;
                    startX = c[0]; startY = c[1]; curX = c[0]; curY = c[1];
                    run.add(new double[]{c[0], c[1]});
                }
                case PathIterator.SEG_LINETO -> {
                    if (run == null) { run = new ArrayList<>(); run.add(new double[]{c[0], c[1]}); curX = c[0]; curY = c[1]; startX = c[0]; startY = c[1]; break; }
                    run.add(new double[]{c[0], c[1]});
                    curX = c[0]; curY = c[1];
                }
                case PathIterator.SEG_QUADTO -> {
                    if (run == null) { run = new ArrayList<>(); run.add(new double[]{curX, curY}); }
                    ArrayList<double[]> pts = new ArrayList<>();
                    flattenQuad(curX, curY, c[0], c[1], c[2], c[3], flatness, 0, pts);
                    for (double[] p : pts) run.add(p);
                    curX = c[2]; curY = c[3];
                }
                case PathIterator.SEG_CUBICTO -> {
                    if (run == null) { run = new ArrayList<>(); run.add(new double[]{curX, curY}); }
                    ArrayList<double[]> pts = new ArrayList<>();
                    flattenCubic(curX, curY, c[0], c[1], c[2], c[3], c[4], c[5], flatness, 0, pts);
                    for (double[] p : pts) run.add(p);
                    curX = c[4]; curY = c[5];
                }
                case PathIterator.SEG_CLOSE -> {
                    runClosed = true;
                    if (run != null) { curX = startX; curY = startY; }
                }
                default -> { }
            }
        }
        if (run != null) finishRun(run, runClosed, polys);
        flatCachePolys = polys;
        flatCacheFlatness = flatness;
        flatCacheCoords = coords.size();
        flatCacheTypes = types.size();
        flatCacheRule = windingRule;
    }

    private static void finishRun(ArrayList<double[]> run, boolean closed,
                                  List<double[][]> polys) {
        // Drop a duplicated closing vertex; keep runs with >= 2 distinct points.
        ArrayList<double[]> pts = new ArrayList<>();
        for (double[] p : run) {
            if (pts.isEmpty() || (Math.abs(p[0] - pts.get(pts.size() - 1)[0]) > 1e-12
                    || Math.abs(p[1] - pts.get(pts.size() - 1)[1]) > 1e-12)) {
                pts.add(p);
            }
        }
        if ((pts.size() >= 2) && closed && (pts.size() > 2)
                && (Math.abs(pts.get(0)[0] - pts.get(pts.size() - 1)[0]) < 1e-12)
                && (Math.abs(pts.get(0)[1] - pts.get(pts.size() - 1)[1]) < 1e-12)) {
            pts.remove(pts.size() - 1);
        }
        if (pts.size() < 3) return; // a line/point has no interior
        double[][] poly = new double[pts.size()][2];
        for (int i = 0; i < pts.size(); i++) { poly[i][0] = pts.get(i)[0]; poly[i][1] = pts.get(i)[1]; }
        polys.add(poly);
    }

    private static void flattenQuad(double x0, double y0, double x1, double y1,
                                    double x2, double y2, double flatness, int depth,
                                    ArrayList<double[]> out) {
        // Distance of the control point from the chord, halved (standard flatness test).
        double dx = x2 - x0, dy = y2 - y0;
        double len = Math.hypot(dx, dy);
        double dist = (len == 0) ? Math.hypot(x1 - x0, y1 - y0)
                : Math.abs((x1 - x0) * dy - (y1 - y0) * dx) / len;
        if ((dist <= flatness) || (depth >= 16)) {
            out.add(new double[]{x2, y2});
            return;
        }
        double mx01 = (x0 + x1) / 2, my01 = (y0 + y1) / 2;
        double mx12 = (x1 + x2) / 2, my12 = (y1 + y2) / 2;
        double mx = (mx01 + mx12) / 2, my = (my01 + my12) / 2;
        flattenQuad(x0, y0, mx01, my01, mx, my, flatness, depth + 1, out);
        flattenQuad(mx, my, mx12, my12, x2, y2, flatness, depth + 1, out);
    }

    private static void flattenCubic(double x0, double y0, double x1, double y1,
                                     double x2, double y2, double x3, double y3,
                                     double flatness, int depth, ArrayList<double[]> out) {
        double dx = x3 - x0, dy = y3 - y0;
        double len = Math.hypot(dx, dy);
        double d1 = (len == 0) ? Math.hypot(x1 - x0, y1 - y0)
                : Math.abs((x1 - x0) * dy - (y1 - y0) * dx) / len;
        double d2 = (len == 0) ? Math.hypot(x2 - x0, y2 - y0)
                : Math.abs((x2 - x0) * dy - (y2 - y0) * dx) / len;
        if ((Math.max(d1, d2) <= flatness) || (depth >= 16)) {
            out.add(new double[]{x3, y3});
            return;
        }
        double mx01 = (x0 + x1) / 2, my01 = (y0 + y1) / 2;
        double mx12 = (x1 + x2) / 2, my12 = (y1 + y2) / 2;
        double mx23 = (x2 + x3) / 2, my23 = (y2 + y3) / 2;
        double m012 = (mx01 + mx12) / 2, m012y = (my01 + my12) / 2;
        double m123 = (mx12 + mx23) / 2, m123y = (my12 + my23) / 2;
        double mx = (m012 + m123) / 2, my = (m012y + m123y) / 2;
        flattenCubic(x0, y0, mx01, my01, m012, m012y, mx, my, flatness, depth + 1, out);
        flattenCubic(mx, my, m123, m123y, mx23, my23, x3, y3, flatness, depth + 1, out);
    }

    private static int ncoordsStatic(int t) {
        return switch (t) {
            case PathIterator.SEG_MOVETO, PathIterator.SEG_LINETO -> 2;
            case PathIterator.SEG_QUADTO -> 4;
            case PathIterator.SEG_CUBICTO -> 6;
            default -> 0;
        };
    }

    /** Point on segment (within eps)? */
    static boolean onSegment(double px, double py, double x1, double y1, double x2, double y2, double eps) {
        double cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1);
        if (Math.abs(cross) > eps * Math.max(1.0, Math.hypot(x2 - x1, y2 - y1))) return false;
        double dot = (px - x1) * (px - x2) + (py - y1) * (py - y2);
        return dot <= eps;
    }

    /** Winding number of point wrt one implicitly-closed polygon. */
    static int windingNumber(double[][] poly, double x, double y) {
        int wn = 0;
        int n = poly.length;
        for (int i = 0; i < n; i++) {
            double x1 = poly[i][0], y1 = poly[i][1];
            double x2 = poly[(i + 1) % n][0], y2 = poly[(i + 1) % n][1];
            if (y1 <= y) {
                if ((y2 > y) && (isLeft(x1, y1, x2, y2, x, y) > 0)) wn++;
            } else {
                if ((y2 <= y) && (isLeft(x1, y1, x2, y2, x, y) < 0)) wn--;
            }
        }
        return wn;
    }

    /** Crossing count of the +x ray from the point wrt one polygon. */
    static int crossings(double[][] poly, double x, double y) {
        int cn = 0;
        int n = poly.length;
        for (int i = 0; i < n; i++) {
            double x1 = poly[i][0], y1 = poly[i][1];
            double x2 = poly[(i + 1) % n][0], y2 = poly[(i + 1) % n][1];
            if (((y1 <= y) && (y2 > y)) || ((y1 > y) && (y2 <= y))) {
                double xinters = x1 + ((y - y1) * (x2 - x1) / (y2 - y1));
                if (xinters > x) cn++;
            }
        }
        return cn;
    }

    static double isLeft(double x1, double y1, double x2, double y2, double x, double y) {
        return ((x2 - x1) * (y - y1) - (x - x1) * (y2 - y1));
    }

    /** True iff the point is on any flattened edge. */
    boolean onBoundary(double x, double y, double flatness) {
        for (double[][] poly : flattenedPolygons(flatness)) {
            int n = poly.length;
            for (int i = 0; i < n; i++) {
                if (onSegment(x, y, poly[i][0], poly[i][1], poly[(i + 1) % n][0], poly[(i + 1) % n][1], 1e-9)) {
                    return true;
                }
            }
        }
        return false;
    }

    @Override public boolean contains(double x, double y) {
        if (coords.isEmpty()) return false;
        // Bounds are control-point bounds (they contain the true curve), so
        // a point outside them is outside. The far edge stays inclusive.
        Rectangle2D b = getBounds2D();
        if ((x < b.getMinX()) || (x > b.getMaxX()) || (y < b.getMinY()) || (y > b.getMaxY())) return false;
        // NOTE: no on-boundary shortcut. The JDK uses the half-open
        // crossing rule: a point exactly on the left/top edge is inside,
        // on the right/bottom edge outside (verified by ProbeBoundary).
        // Treating on-boundary as inside over-counts by the boundary
        // pixels (the 48-failure residue in the harness).
        double flatness = 0.25;
        if (windingRule == WIND_EVEN_ODD) {
            int cn = 0;
            for (double[][] poly : flattenedPolygons(flatness)) cn += crossings(poly, x, y);
            return (cn % 2) == 1;
        } else {
            int wn = 0;
            for (double[][] poly : flattenedPolygons(flatness)) wn += windingNumber(poly, x, y);
            return wn != 0;
        }
    }
    @Override public boolean contains(Point2D p) { return contains(p.getX(), p.getY()); }
    @Override public boolean contains(double x, double y, double w, double h) {
        if ((w <= 0) || (h <= 0)) return false;
        // Closed rect ⊆ closed shape (verified by ProbeRect): every corner
        // inside-or-on, and no path edge has a point strictly inside the
        // open rect (an edge through the interior means part of the rect
        // lies outside the shape).
        if (!insideOrOn(x, y) || !insideOrOn(x + w, y) || !insideOrOn(x, y + h) || !insideOrOn(x + w, y + h)) {
            return false;
        }
        return !anyEdgeThroughOpenRect(x, y, w, h);
    }
    @Override public boolean contains(Rectangle2D r) { return contains(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }
    @Override public boolean intersects(double x, double y, double w, double h) {
        if ((w <= 0) || (h <= 0) || coords.isEmpty()) return false;
        if (!getBounds2D().intersects(x, y, w, h)) return false;
        // Positive-area overlap (verified by ProbeRect): a rect corner
        // strictly inside the shape, or a path edge passing through the
        // rect interior. Touching at an edge/corner only is NOT an
        // intersection.
        if (strictlyInside(x, y) || strictlyInside(x + w, y)
                || strictlyInside(x, y + h) || strictlyInside(x + w, y + h)) return true;
        if (anyEdgeThroughOpenRect(x, y, w, h)) return true;
        // The shape may lie entirely inside the rect with its edges on the
        // rect boundary (e.g. identical rects): sample a point just inside
        // the shape, on the interior side of each boundary edge.
        return anyInteriorSampleInOpenRect(x, y, w, h);
    }

    /** True iff a point just inside the shape lies strictly inside the open rect. */
    boolean anyInteriorSampleInOpenRect(double x, double y, double w, double h) {
        double eps = 1e-6;
        for (double[][] poly : flattenedPolygons(0.25)) {
            if (poly.length < 3) continue;
            // Inward normal: left of each directed edge for CCW polygons.
            double[][] ccw = (signedArea2D(poly) < 0) ? reversePoly(poly) : poly;
            int n = ccw.length;
            for (int i = 0; i < n; i++) {
                double x1 = ccw[i][0], y1 = ccw[i][1];
                double x2 = ccw[(i + 1) % n][0], y2 = ccw[(i + 1) % n][1];
                double dx = x2 - x1, dy = y2 - y1;
                double len = Math.hypot(dx, dy);
                if (len < 1e-12) continue;
                double nx = -dy / len, ny = dx / len; // left normal
                double mx = (x1 + x2) / 2.0 + eps * nx;
                double my = (y1 + y2) / 2.0 + eps * ny;
                // Guard: the sample must really be inside the shape (a
                // frame-piece edge can face a hole in multi-subpath areas).
                if (contains(mx, my) && (mx > x) && (mx < x + w) && (my > y) && (my < y + h)) return true;
            }
        }
        return false;
    }

    static double signedArea2D(double[][] p) {
        double s = 0;
        for (int i = 0; i < p.length; i++) {
            double[] a = p[i], b = p[(i + 1) % p.length];
            s += (a[0] * b[1] - b[0] * a[1]);
        }
        return s / 2.0;
    }

    static double[][] reversePoly(double[][] p) {
        double[][] r = new double[p.length][2];
        for (int i = 0; i < p.length; i++) { r[i][0] = p[p.length - 1 - i][0]; r[i][1] = p[p.length - 1 - i][1]; }
        return r;
    }

    /** Inside by the half-open point rule, or exactly on the boundary. */
    boolean insideOrOn(double x, double y) {
        return contains(x, y) || onBoundary(x, y, 0.25);
    }

    /** Inside by the half-open point rule and not on the boundary. */
    boolean strictlyInside(double x, double y) {
        return contains(x, y) && !onBoundary(x, y, 0.25);
    }

    /** True iff some flattened edge has a point strictly inside the open rect. */
    boolean anyEdgeThroughOpenRect(double x, double y, double w, double h) {
        for (double[][] poly : flattenedPolygons(0.25)) {
            int n = poly.length;
            for (int i = 0; i < n; i++) {
                if (segmentThroughOpenRect(poly[i][0], poly[i][1], poly[(i + 1) % n][0], poly[(i + 1) % n][1],
                        x, y, w, h)) return true;
            }
        }
        return false;
    }

    /** Liang–Barsky clip to the closed rect; true iff the clipped piece has
     * positive length and its midpoint is strictly inside the open rect. */
    static boolean segmentThroughOpenRect(double x1, double y1, double x2, double y2,
                                          double rx, double ry, double rw, double rh) {
        double dx = x2 - x1, dy = y2 - y1;
        double t0 = 0, t1 = 1;
        double[] p = {-dx, dx, -dy, dy};
        double[] q = {x1 - rx, rx + rw - x1, y1 - ry, ry + rh - y1};
        for (int i = 0; i < 4; i++) {
            if (Math.abs(p[i]) < 1e-15) {
                if (q[i] < 0) return false;
            } else {
                double r = q[i] / p[i];
                if (p[i] < 0) {
                    if (r > t1) return false;
                    if (r > t0) t0 = r;
                } else {
                    if (r < t0) return false;
                    if (r < t1) t1 = r;
                }
            }
        }
        if (t1 - t0 <= 1e-12) return false; // point contact or no overlap
        double tm = (t0 + t1) / 2.0;
        double mx = x1 + tm * dx, my = y1 + tm * dy;
        return (mx > rx) && (mx < rx + rw) && (my > ry) && (my < ry + rh);
    }
    @Override public boolean intersects(Rectangle2D r) { return intersects(r.getX(), r.getY(), r.getWidth(), r.getHeight()); }

    /** Segment vs rectangle (closed): endpoint inside, or crosses an edge. */
    static boolean segmentIntersectsRect(double x1, double y1, double x2, double y2,
                                         double rx, double ry, double rw, double rh) {
        if (pointInRectClosed(x1, y1, rx, ry, rw, rh) || pointInRectClosed(x2, y2, rx, ry, rw, rh)) return true;
        return segmentsIntersect(x1, y1, x2, y2, rx, ry, rx + rw, ry)
                || segmentsIntersect(x1, y1, x2, y2, rx + rw, ry, rx + rw, ry + rh)
                || segmentsIntersect(x1, y1, x2, y2, rx + rw, ry + rh, rx, ry + rh)
                || segmentsIntersect(x1, y1, x2, y2, rx, ry + rh, rx, ry);
    }

    static boolean pointInRectClosed(double x, double y, double rx, double ry, double rw, double rh) {
        return (x >= rx) && (x <= rx + rw) && (y >= ry) && (y <= ry + rh);
    }

    /** Proper segment intersection test (including collinear overlap). */
    static boolean segmentsIntersect(double x1, double y1, double x2, double y2,
                                     double x3, double y3, double x4, double y4) {
        double d1 = orient(x3, y3, x4, y4, x1, y1);
        double d2 = orient(x3, y3, x4, y4, x2, y2);
        double d3 = orient(x1, y1, x2, y2, x3, y3);
        double d4 = orient(x1, y1, x2, y2, x4, y4);
        if ((((d1 > 0) && (d2 < 0)) || ((d1 < 0) && (d2 > 0)))
                && (((d3 > 0) && (d4 < 0)) || ((d3 < 0) && (d4 > 0)))) return true;
        double eps = 1e-12;
        if ((Math.abs(d1) <= eps) && onSegmentCollinear(x1, y1, x3, y3, x4, y4)) return true;
        if ((Math.abs(d2) <= eps) && onSegmentCollinear(x2, y2, x3, y3, x4, y4)) return true;
        if ((Math.abs(d3) <= eps) && onSegmentCollinear(x3, y3, x1, y1, x2, y2)) return true;
        if ((Math.abs(d4) <= eps) && onSegmentCollinear(x4, y4, x1, y1, x2, y2)) return true;
        return false;
    }

    static double orient(double x1, double y1, double x2, double y2, double x3, double y3) {
        return (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1);
    }

    static boolean onSegmentCollinear(double px, double py, double x1, double y1, double x2, double y2) {
        return (px >= Math.min(x1, x2) - 1e-9) && (px <= Math.max(x1, x2) + 1e-9)
                && (py >= Math.min(y1, y2) - 1e-9) && (py <= Math.max(y1, y2) + 1e-9);
    }

    @Override public PathIterator getPathIterator(AffineTransform at) { return new Iter(at, false); }
    @Override public PathIterator getPathIterator(AffineTransform at, double flatness) {
        if (!java.lang.Double.isFinite(flatness)) return new Iter(at, false);
        return new FlatIter(at, flatness);
    }
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }

    private int ncoords(int t) { return ncoordsStatic(t); }

    final class Iter implements PathIterator {
        private final AffineTransform at; private final boolean flat; private int seg;
        Iter(AffineTransform at, boolean flat) { this.at = at; this.flat = flat; }
        @Override public int getWindingRule() { return windingRule; }
        @Override public boolean isDone() { return seg >= types.size(); }
        @Override public void next() { seg++; }
        private double[] xform(double[] c, int n) {
            if (at == null) return c;
            double[] out = new double[n];
            at.transform(c, 0, out, 0, n / 2);
            return out;
        }
        @Override public int currentSegment(float[] cf) {
            double[] cd = new double[6]; int t = currentSegment(cd);
            for (int i = 0; i < 6; i++) cf[i] = (float) cd[i];
            return t;
        }
        @Override public int currentSegment(double[] c) {
            int t = types.get(seg);
            int base = 0;
            for (int i = 0; i < seg; i++) base += ncoords(types.get(i));
            int n = ncoords(t);
            double[] raw = new double[n];
            for (int i = 0; i < n; i++) raw[i] = coords.get(base + i);
            double[] out = xform(raw, n);
            System.arraycopy(out, 0, c, 0, n);
            return t;
        }
    }

    /** Flattening iterator: curves become runs of line segments. */
    final class FlatIter implements PathIterator {
        private final AffineTransform at;
        private final ArrayList<Integer> ftypes = new ArrayList<>();
        private final ArrayList<java.lang.Double> fcoords = new ArrayList<>();
        private int seg;
        FlatIter(AffineTransform at, double flatness) {
            this.at = at;
            // Build the segment stream from the raw segment list, subdividing
            // curves, so open subpaths and degenerate runs survive.
            buildFlatSegments(flatness);
        }
        private void buildFlatSegments(double flatness) {
            double curX = 0, curY = 0;
            int base = 0;
            for (int s = 0; s < types.size(); s++) {
                int t = types.get(s);
                int n = ncoords(t);
                double[] c = new double[n];
                for (int i = 0; i < n; i++) c[i] = coords.get(base + i);
                base += n;
                switch (t) {
                    case PathIterator.SEG_MOVETO -> {
                        emit(PathIterator.SEG_MOVETO, c[0], c[1]);
                        curX = c[0]; curY = c[1];
                    }
                    case PathIterator.SEG_LINETO -> {
                        emit(PathIterator.SEG_LINETO, c[0], c[1]);
                        curX = c[0]; curY = c[1];
                    }
                    case PathIterator.SEG_QUADTO -> {
                        ArrayList<double[]> pts = new ArrayList<>();
                        flattenQuad(curX, curY, c[0], c[1], c[2], c[3], flatness, 0, pts);
                        for (double[] p : pts) emit(PathIterator.SEG_LINETO, p[0], p[1]);
                        curX = c[2]; curY = c[3];
                    }
                    case PathIterator.SEG_CUBICTO -> {
                        ArrayList<double[]> pts = new ArrayList<>();
                        flattenCubic(curX, curY, c[0], c[1], c[2], c[3], c[4], c[5], flatness, 0, pts);
                        for (double[] p : pts) emit(PathIterator.SEG_LINETO, p[0], p[1]);
                        curX = c[4]; curY = c[5];
                    }
                    case PathIterator.SEG_CLOSE -> emit(PathIterator.SEG_CLOSE);
                    default -> { }
                }
            }
        }
        private void emit(int type, double... xy) {
            ftypes.add(type);
            for (double v : xy) fcoords.add(v);
        }
        @Override public int getWindingRule() { return windingRule; }
        @Override public boolean isDone() { return seg >= ftypes.size(); }
        @Override public void next() { seg++; }
        @Override public int currentSegment(float[] cf) {
            double[] cd = new double[6]; int t = currentSegment(cd);
            for (int i = 0; i < 6; i++) cf[i] = (float) cd[i];
            return t;
        }
        @Override public int currentSegment(double[] c) {
            int t = ftypes.get(seg);
            int base = 0;
            for (int i = 0; i < seg; i++) base += ncoords(ftypes.get(i));
            int n = ncoords(t);
            double[] raw = new double[n];
            for (int i = 0; i < n; i++) raw[i] = fcoords.get(base + i);
            if (at != null) {
                double[] out = new double[n];
                at.transform(raw, 0, out, 0, n / 2);
                raw = out;
            }
            System.arraycopy(raw, 0, c, 0, n);
            return t;
        }
    }

    public static class Double extends Path2D {
        public Double() { super(); }
        public Double(int windingRule) { super(windingRule); }
        public Double(Shape s) { super(); append(s, false); }
        public Double(Shape s, AffineTransform at) { super(); append(s.getPathIterator(at), false); }
        @Override public void moveTo(double x, double y) { coords.add(x); coords.add(y); types.add(PathIterator.SEG_MOVETO); }
        @Override public void lineTo(double x, double y) { coords.add(x); coords.add(y); types.add(PathIterator.SEG_LINETO); }
        @Override public void quadTo(double x1, double y1, double x2, double y2) {
            coords.add(x1); coords.add(y1); coords.add(x2); coords.add(y2); types.add(PathIterator.SEG_QUADTO);
        }
        @Override public void curveTo(double x1, double y1, double x2, double y2, double x3, double y3) {
            coords.add(x1); coords.add(y1); coords.add(x2); coords.add(y2); coords.add(x3); coords.add(y3);
            types.add(PathIterator.SEG_CUBICTO);
        }
        @Override public void closePath() { types.add(PathIterator.SEG_CLOSE); }
    }
    public static class Float extends Path2D {
        public Float() { super(); }
        public Float(int windingRule) { super(windingRule); }
        @Override public void moveTo(double x, double y) { coords.add(x); coords.add(y); types.add(PathIterator.SEG_MOVETO); }
        @Override public void lineTo(double x, double y) { coords.add(x); coords.add(y); types.add(PathIterator.SEG_LINETO); }
        public void moveTo(float x, float y) { moveTo((double) x, (double) y); }
        public void lineTo(float x, float y) { lineTo((double) x, (double) y); }
        public void quadTo(float x1, float y1, float x2, float y2) { quadTo((double) x1, (double) y1, (double) x2, (double) y2); }
        public void curveTo(float x1, float y1, float x2, float y2, float x3, float y3) {
            curveTo((double) x1, (double) y1, (double) x2, (double) y2, (double) x3, (double) y3);
        }
        @Override public void quadTo(double x1, double y1, double x2, double y2) {
            coords.add(x1); coords.add(y1); coords.add(x2); coords.add(y2); types.add(PathIterator.SEG_QUADTO);
        }
        @Override public void curveTo(double x1, double y1, double x2, double y2, double x3, double y3) {
            coords.add(x1); coords.add(y1); coords.add(x2); coords.add(y2); coords.add(x3); coords.add(y3);
            types.add(PathIterator.SEG_CUBICTO);
        }
        @Override public void closePath() { types.add(PathIterator.SEG_CLOSE); }
    }
}
