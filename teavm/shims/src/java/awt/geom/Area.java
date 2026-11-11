package java.awt.geom;
import java.awt.Shape;
import java.util.ArrayList;
import java.util.List;
/**
 * Minimal java.awt.geom.Area, backed by a Path2D.
 *
 * §26 (TeaVM grid gap): add/subtract/intersect/exclusiveOr used to be
 * no-ops (subtract/intersect/xor) or a bare path append (add), and
 * contains() was bounds-based via Path2D. That made BeamItem.getBeltArea
 * return the belt WITH the core still in it, so computeImpacts rejected
 * every good beam (beltRatio 0.71 vs maxBelt 0.4) and BeamsBuilder created
 * zero beams — hence zero MultipleRestInter and the Hallelujah grid gap.
 *
 * Boolean ops are now real polygon operations on the flattened path
 * (flatness 0.5): Sutherland–Hodgman clipping when the clip polygon is
 * convex, Greiner–Hormann clipping when it is not. Results are stored as
 * ordinary subpaths; contains() is the exact Path2D point-in-path test
 * (winding rule honoured), so a multi-subpath union/difference reads
 * correctly. Degenerate (zero-area) polygons are dropped.
 *
 * NOTE on the earlier triangulation approach (removed): subtracting a
 * non-convex clip by triangulating it and subtracting triangles
 * sequentially makes the piece count grow ~3x per triangle — for a staff
 * core path (~100 triangles) that is an exponential blowup (OOM in
 * BenchTri on page-minus-staff). Greiner–Hormann handles concave clips
 * directly in O(n*m + k) with no triangulation.
 */
public class Area implements Shape, Cloneable {
    private Path2D path;
    public Area() { path = new Path2D.Double(); }
    public Area(Shape s) { path = new Path2D.Double(s); }
    public Area(Area a) { path = new Path2D.Double(a.path); }

    /** Flattened polygons of this area (implicitly closed, >= 3 vertices). */
    List<double[][]> polys() {
        List<double[][]> out = new ArrayList<>();
        for (double[][] p : path.flattenedPolygons(0.5)) {
            if (Math.abs(signedArea(p)) > 1e-12) out.add(p);
        }
        return out;
    }

    private void rebuild(List<double[][]> polys) {
        path.reset();
        for (double[][] p : polys) {
            if (p.length < 3) continue;
            path.moveTo(p[0][0], p[0][1]);
            for (int i = 1; i < p.length; i++) path.lineTo(p[i][0], p[i][1]);
            path.closePath();
        }
    }

    public void add(Area a) { path.append(a.path, false); }

    public void subtract(Area a) {
        List<double[][]> subjects = polys();
        List<double[][]> clips = a.polys();
        if (subjects.isEmpty() || clips.isEmpty()) return;
        for (double[][] clip : clips) {
            subjects = subtractOne(subjects, clip);
            if (subjects.isEmpty()) break;
        }
        rebuild(subjects);
    }

    public void intersect(Area a) {
        List<double[][]> left = polys();
        List<double[][]> right = a.polys();
        if (left.isEmpty() || right.isEmpty()) { path.reset(); return; }
        List<double[][]> result = new ArrayList<>();
        for (double[][] p : left) {
            for (double[][] q : right) {
                result.addAll(intersectOne(p, q));
            }
        }
        rebuild(result);
    }

    public void exclusiveOr(Area a) {
        Area d1 = new Area(this);
        d1.subtract(a);
        Area d2 = new Area(a);
        d2.subtract(this);
        path = d1.path;
        path.append(d2.path, false);
    }

    public void reset() { path.reset(); }
    public boolean isEmpty() { return path.getBounds2D().isEmpty(); }
    public boolean isPolygonal() { return true; }
    public boolean isRectangular() { return false; }
    public boolean isSingular() { return true; }
    public Rectangle2D getBounds2D() { return path.getBounds2D(); }
    @Override public java.awt.Rectangle getBounds() { return path.getBounds(); }
    @Override public boolean contains(double x, double y) { return path.contains(x, y); }
    @Override public boolean contains(Point2D p) { return path.contains(p); }
    @Override public boolean contains(double x, double y, double w, double h) { return path.contains(x, y, w, h); }
    @Override public boolean contains(Rectangle2D r) { return path.contains(r); }
    @Override public boolean intersects(double x, double y, double w, double h) { return path.intersects(x, y, w, h); }
    @Override public boolean intersects(Rectangle2D r) { return path.intersects(r); }
    @Override public PathIterator getPathIterator(AffineTransform at) { return path.getPathIterator(at); }
    @Override public PathIterator getPathIterator(AffineTransform at, double flatness) { return path.getPathIterator(at, flatness); }
    @Override public Object clone() { return new Area(this); }
    @Override public boolean equals(Object o) { return o instanceof Area a && path.getBounds2D().equals(a.path.getBounds2D()); }

    // ------------------------------------------------------------------
    // Polygon helpers
    // ------------------------------------------------------------------

    static double signedArea(double[][] p) {
        double s = 0;
        for (int i = 0; i < p.length; i++) {
            double[] a = p[i], b = p[(i + 1) % p.length];
            s += (a[0] * b[1] - b[0] * a[1]);
        }
        return s / 2.0;
    }

    static boolean isConvex(double[][] p) {
        int n = p.length;
        int sign = 0;
        for (int i = 0; i < n; i++) {
            double[] a = p[i], b = p[(i + 1) % n], c = p[(i + 2) % n];
            double cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]);
            if (Math.abs(cross) < 1e-12) continue;
            int s = (cross > 0) ? 1 : -1;
            if ((sign != 0) && (s != sign)) return false;
            sign = s;
        }
        return true;
    }

    static double[][] ensureCCW(double[][] p) {
        if (signedArea(p) < 0) {
            double[][] r = new double[p.length][2];
            for (int i = 0; i < p.length; i++) { r[i][0] = p[p.length - 1 - i][0]; r[i][1] = p[p.length - 1 - i][1]; }
            return r;
        }
        return p;
    }

    /** Clip polygon by a half-plane: keep points on the LEFT of edge a->b (keepLeft) or RIGHT. */
    static double[][] clipHalfPlane(double[][] poly, double ax, double ay, double bx, double by, boolean keepLeft) {
        ArrayList<double[]> out = new ArrayList<>();
        int n = poly.length;
        double eps = 1e-12;
        for (int i = 0; i < n; i++) {
            double[] cur = poly[i];
            double[] prev = poly[(i + n - 1) % n];
            double dc = (bx - ax) * (cur[1] - ay) - (by - ay) * (cur[0] - ax);
            double dp = (bx - ax) * (prev[1] - ay) - (by - ay) * (prev[0] - ax);
            boolean curIn = keepLeft ? (dc >= -eps) : (dc <= eps);
            boolean prevIn = keepLeft ? (dp >= -eps) : (dp <= eps);
            if (curIn != prevIn) {
                double t = dp / (dp - dc); // dp and dc have opposite signs (or one is ~0)
                double ix = prev[0] + t * (cur[0] - prev[0]);
                double iy = prev[1] + t * (cur[1] - prev[1]);
                out.add(new double[]{ix, iy});
            }
            if (curIn) out.add(new double[]{cur[0], cur[1]});
        }
        return toArray(out);
    }

    /** Subject clipped to the inside of a convex (CCW) clip polygon. Empty if disjoint. */
    static double[][] clipByConvex(double[][] subject, double[][] clipCCW) {
        double[][] out = subject;
        int n = clipCCW.length;
        for (int i = 0; i < n; i++) {
            double[] a = clipCCW[i], b = clipCCW[(i + 1) % n];
            out = clipHalfPlane(out, a[0], a[1], b[0], b[1], true);
            if (out.length < 3) return new double[0][2];
        }
        return out;
    }

    /** subjectList minus a convex clip polygon: P - Q = union over Q's edges of (P outside that edge).
     * The pieces MUST be disjoint: the naive union (P outside H_i) for each
     * edge overlaps at the corners, so the Area stores the overlap twice
     * and the next subtract splits each copy again — the piece count
     * grows ~x2.2 per subtract (DIAG31: 20, 65, 180, ..., 286,655
     * segments after 12 staff strips, vs 65 on desktop) and any later
     * fill/contains over the area stalls. Piece i is therefore clipped
     * to the INSIDE of every earlier half-plane H_j (j < i): the pieces
     * are pairwise disjoint (piece i is outside H_i, piece j>i is inside
     * H_i) and their union is still P - Q (a point of P - Q is outside
     * some H_i; take the smallest such i). */
    static List<double[][]> subtractConvex(List<double[][]> subjects, double[][] clip) {
        double[][] ccw = ensureCCW(clip);
        List<double[][]> result = new ArrayList<>();
        int n = ccw.length;
        for (double[][] p : subjects) {
            for (int i = 0; i < n; i++) {
                double[] a = ccw[i], b = ccw[(i + 1) % n];
                double[][] piece = clipHalfPlane(p, a[0], a[1], b[0], b[1], false);
                for (int j = 0; (j < i) && (piece.length >= 3); j++) {
                    double[] aj = ccw[j], bj = ccw[(j + 1) % n];
                    piece = clipHalfPlane(piece, aj[0], aj[1], bj[0], bj[1], true);
                }
                if ((piece.length >= 3) && (Math.abs(signedArea(piece)) > 1e-12)) result.add(piece);
            }
        }
        return result;
    }

    /** subjectList minus one (possibly non-convex) clip polygon. */
    static List<double[][]> subtractOne(List<double[][]> subjects, double[][] clip) {
        if (isConvex(clip)) return subtractConvex(subjects, clip);
        List<double[][]> out = new ArrayList<>();
        for (double[][] s : subjects) {
            out.addAll(greinerHormann(s, clip, GH_DIFF));
        }
        return out;
    }

    /** Intersection of two polygons. */
    static List<double[][]> intersectOne(double[][] p, double[][] q) {
        List<double[][]> out = new ArrayList<>();
        if (isConvex(q)) {
            double[][] r = clipByConvex(p, ensureCCW(q));
            if ((r.length >= 3) && (Math.abs(signedArea(r)) > 1e-12)) out.add(r);
            return out;
        }
        if (isConvex(p)) {
            double[][] r = clipByConvex(q, ensureCCW(p));
            if ((r.length >= 3) && (Math.abs(signedArea(r)) > 1e-12)) out.add(r);
            return out;
        }
        return greinerHormann(p, q, GH_INTERSECT);
    }

    static double[][] toArray(ArrayList<double[]> list) {
        double[][] out = new double[list.size()][2];
        for (int i = 0; i < list.size(); i++) { out[i][0] = list.get(i)[0]; out[i][1] = list.get(i)[1]; }
        return out;
    }

    // ------------------------------------------------------------------
    // Greiner–Hormann polygon clipping (for non-convex operands).
    // Entry/exit flags: entry(v) == the edge AFTER v lies inside the
    // OTHER polygon. Traces (verified on the two-square example):
    //   INTERSECT: S forward entry->exit, C forward exit->entry.
    //   UNION:     S forward exit->entry, C forward entry->exit.
    //   DIFF:      S forward exit->entry, C BACKWARD until an entry node.
    // Degenerate intersections (vertex-on-edge, shared vertices, collinear
    // overlaps) are resolved by nudging the clip polygon by ~1e-7 and
    // retrying; identical polygons are handled exactly up front (a nudge
    // would turn an empty difference into a 1e-7 frame).
    // ------------------------------------------------------------------

    static final int GH_INTERSECT = 0;
    static final int GH_UNION = 1;
    static final int GH_DIFF = 2;

    /** One vertex in a GH circular list. */
    static final class GHNode {
        double x, y;
        GHNode next, prev;
        boolean isX;      // intersection node
        GHNode twin;      // counterpart in the other polygon
        boolean entry;    // the edge AFTER this node lies inside the other polygon
        boolean visited;
        GHNode(double x, double y) { this.x = x; this.y = y; }
    }

    /** Drop duplicate consecutive vertices (incl. a duplicated closing vertex). */
    static double[][] cleanPoly(double[][] p) {
        ArrayList<double[]> pts = new ArrayList<>();
        for (double[] v : p) {
            if (pts.isEmpty() || (Math.abs(v[0] - pts.get(pts.size() - 1)[0]) > 1e-12
                    || Math.abs(v[1] - pts.get(pts.size() - 1)[1]) > 1e-12)) {
                pts.add(new double[]{v[0], v[1]});
            }
        }
        if ((pts.size() > 1) && (Math.abs(pts.get(0)[0] - pts.get(pts.size() - 1)[0]) < 1e-12)
                && (Math.abs(pts.get(0)[1] - pts.get(pts.size() - 1)[1]) < 1e-12)) {
            pts.remove(pts.size() - 1);
        }
        return toArray(pts);
    }

    /** True iff the two polygons have the same vertices in order (up to rotation / reversal). */
    static boolean identicalPolys(double[][] a, double[][] b) {
        if (a.length != b.length) return false;
        int n = a.length;
        for (int start = 0; start < n; start++) {
            if ((Math.abs(a[0][0] - b[start][0]) < 1e-12) && (Math.abs(a[0][1] - b[start][1]) < 1e-12)) {
                boolean fwd = true, rev = true;
                for (int i = 0; i < n; i++) {
                    double[] av = a[i];
                    double[] bvF = b[(start + i) % n];
                    double[] bvR = b[(start - i + 2 * n) % n];
                    if ((Math.abs(av[0] - bvF[0]) > 1e-12) || (Math.abs(av[1] - bvF[1]) > 1e-12)) fwd = false;
                    if ((Math.abs(av[0] - bvR[0]) > 1e-12) || (Math.abs(av[1] - bvR[1]) > 1e-12)) rev = false;
                }
                if (fwd || rev) return true;
            }
        }
        return false;
    }

    static double[][] reversedPoly(double[][] p) {
        double[][] r = new double[p.length][2];
        for (int i = 0; i < p.length; i++) { r[i][0] = p[p.length - 1 - i][0]; r[i][1] = p[p.length - 1 - i][1]; }
        return r;
    }

    /** Greiner–Hormann clip of subject by clip polygon. Returns result polygons (possibly empty). */
    static List<double[][]> greinerHormann(double[][] sPoly, double[][] cPoly, int op) {
        double[][] s = cleanPoly(ensureCCW(sPoly));
        double[][] c = cleanPoly(ensureCCW(cPoly));
        List<double[][]> out = new ArrayList<>();
        if ((s.length < 3) || (Math.abs(signedArea(s)) <= 1e-12)) return out;
        if ((c.length < 3) || (Math.abs(signedArea(c)) <= 1e-12)) {
            // Empty clip: diff keeps the subject, intersect is empty, union keeps the subject.
            if (op != GH_INTERSECT) out.add(s);
            return out;
        }
        if (identicalPolys(s, c)) {
            if (op == GH_INTERSECT) out.add(s);
            else if (op == GH_UNION) out.add(s);
            // DIFF of identical polygons is empty.
            return out;
        }
        for (int attempt = 0; attempt < 4; attempt++) {
            double[][] cc = c;
            if (attempt > 0) {
                double d = 1e-7 * attempt;
                cc = new double[c.length][2];
                for (int i = 0; i < c.length; i++) { cc[i][0] = c[i][0] + d; cc[i][1] = c[i][1] + d * 0.6180339887; }
            }
            List<double[][]> r = greinerHormannAttempt(s, cc, op);
            if (r != null) return r; // null means a degeneracy was hit; retry nudged
        }
        // All attempts degenerate: fall back to leaving the subject unchanged
        // for DIFF/UNION, empty for INTERSECT (previous no-op behaviour).
        if (op != GH_INTERSECT) out.add(s);
        return out;
    }

    /** One GH attempt. Returns null on a degenerate intersection (retry nudged). */
    static List<double[][]> greinerHormannAttempt(double[][] s, double[][] c, int op) {
        GHNode sHead = buildList(s);
        GHNode cHead = buildList(c);
        // --- Find intersections (proper crossings only; anything else is degenerate). ---
        ArrayList<GHNode> sNodes = listNodes(sHead);
        ArrayList<GHNode> cNodes = listNodes(cHead);
        int ns = sNodes.size(), nc = cNodes.size();
        // Per-edge intersection lists, sorted by parameter t along the edge.
        ArrayList<ArrayList<double[]>> sHits = new ArrayList<>();
        ArrayList<ArrayList<double[]>> cHits = new ArrayList<>();
        for (int i = 0; i < ns; i++) sHits.add(new ArrayList<>());
        for (int i = 0; i < nc; i++) cHits.add(new ArrayList<>());
        double eps = 1e-12;
        for (int i = 0; i < ns; i++) {
            double[] a = s[i], b = s[(i + 1) % ns];
            for (int j = 0; j < nc; j++) {
                double[] p = c[j], q = c[(j + 1) % nc];
                double d1 = Path2D.orient(p[0], p[1], q[0], q[1], a[0], a[1]);
                double d2 = Path2D.orient(p[0], p[1], q[0], q[1], b[0], b[1]);
                double d3 = Path2D.orient(a[0], a[1], b[0], b[1], p[0], p[1]);
                double d4 = Path2D.orient(a[0], a[1], b[0], b[1], q[0], q[1]);
                boolean z1 = Math.abs(d1) <= eps, z2 = Math.abs(d2) <= eps;
                boolean z3 = Math.abs(d3) <= eps, z4 = Math.abs(d4) <= eps;
                if (z1 && z2 && z3 && z4) {
                    // Collinear edges: overlapping with positive length is degenerate;
                    // a single-point touch is also degenerate for GH.
                    return null;
                }
                if (z1 || z2 || z3 || z4) return null; // endpoint touch: degenerate
                if (((d1 > 0) == (d2 > 0)) || ((d3 > 0) == (d4 > 0))) continue; // no crossing
                // Proper crossing: solve a + t*(b-a) = p + u*(q-p).
                double denom = ((b[0] - a[0]) * (q[1] - p[1]) - (b[1] - a[1]) * (q[0] - p[0]));
                if (Math.abs(denom) < 1e-300) return null;
                double t = ((p[0] - a[0]) * (q[1] - p[1]) - (p[1] - a[1]) * (q[0] - p[0])) / denom;
                double u = ((p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])) / denom;
                if ((t <= 0) || (t >= 1) || (u <= 0) || (u >= 1)) return null; // should not happen; be safe
                double x = a[0] + t * (b[0] - a[0]);
                double y = a[1] + t * (b[1] - a[1]);
                double[] hit = {t, x, y};
                double[] hitC = {u, x, y};
                sHits.get(i).add(hit);
                cHits.get(j).add(hitC);
            }
        }
        int totalX = 0;
        for (ArrayList<double[]> h : sHits) totalX += h.size();
        if (totalX == 0) return noIntersectionResult(s, c, op);
        // --- Insert intersection nodes (sorted by t along each edge). ---
        insertHits(sHead, sHits);
        insertHits(cHead, cHits);
        // Link twins: intersections are the same geometric points in both lists.
        sNodes = listNodes(sHead);
        cNodes = listNodes(cHead);
        for (GHNode sn : sNodes) {
            if (!sn.isX) continue;
            for (GHNode cn : cNodes) {
                if (cn.isX && (Math.abs(cn.x - sn.x) < 1e-9) && (Math.abs(cn.y - sn.y) < 1e-9)) {
                    sn.twin = cn;
                    cn.twin = sn;
                    break;
                }
            }
            if (sn.twin == null) return null; // unmatched intersection: degenerate
        }
        // --- Classify entry/exit: entry(v) == the edge AFTER v lies inside the other polygon. ---
        for (GHNode sn : sNodes) {
            if (!sn.isX) continue;
            sn.entry = edgeMidInside(sn, c);
        }
        for (GHNode cn : cNodes) {
            if (!cn.isX) continue;
            cn.entry = edgeMidInside(cn, s);
        }
        // --- Trace. ---
        List<double[][]> out = new ArrayList<>();
        ArrayList<GHNode> sList = listNodes(sHead);
        if (op == GH_INTERSECT) {
            for (GHNode start : sList) {
                if (start.isX && start.entry && !start.visited) {
                    double[][] poly = trace(sHead, start, true, true);
                    if (poly != null) out.add(poly);
                }
            }
        } else if (op == GH_UNION) {
            for (GHNode start : sList) {
                if (start.isX && !start.entry && !start.visited) {
                    double[][] poly = trace(sHead, start, false, true);
                    if (poly != null) out.add(poly);
                }
            }
        } else { // GH_DIFF
            for (GHNode start : sList) {
                if (start.isX && !start.entry && !start.visited) {
                    double[][] poly = trace(sHead, start, false, false);
                    if (poly != null) out.add(poly);
                }
            }
        }
        return out;
    }

    /** No-intersection outcome. */
    static List<double[][]> noIntersectionResult(double[][] s, double[][] c, int op) {
        List<double[][]> out = new ArrayList<>();
        boolean sInC = Path2D.windingNumber(c, s[0][0], s[0][1]) != 0;
        boolean cInS = Path2D.windingNumber(s, c[0][0], c[0][1]) != 0;
        if (op == GH_INTERSECT) {
            if (sInC) out.add(s);
            else if (cInS) out.add(c);
        } else if (op == GH_UNION) {
            if (sInC) out.add(c);
            else if (cInS) out.add(s);
            else { out.add(s); out.add(c); }
        } else { // GH_DIFF
            if (sInC) { /* empty */ }
            else if (cInS) { out.add(s); out.add(reversedPoly(c)); } // hole: reversed contour
            else out.add(s);
        }
        return out;
    }

    /** True iff the midpoint of (node -> next) lies inside the given polygon. */
    static boolean edgeMidInside(GHNode node, double[][] poly) {
        double mx = (node.x + node.next.x) / 2.0;
        double my = (node.y + node.next.y) / 2.0;
        if (Path2D.windingNumber(poly, mx, my) != 0) return true;
        // Midpoint on the boundary (degenerate): try quarter points.
        for (double f : new double[]{0.25, 0.75}) {
            double qx = node.x + f * (node.next.x - node.x);
            double qy = node.y + f * (node.next.y - node.y);
            if (Path2D.windingNumber(poly, qx, qy) != 0) return true;
            if (!onPolyBoundary(poly, qx, qy)) return false;
        }
        return false;
    }

    static boolean onPolyBoundary(double[][] poly, double x, double y) {
        int n = poly.length;
        for (int i = 0; i < n; i++) {
            if (Path2D.onSegment(x, y, poly[i][0], poly[i][1], poly[(i + 1) % n][0], poly[(i + 1) % n][1], 1e-9)) {
                return true;
            }
        }
        return false;
    }

    /** Trace one result polygon.
     * @param start  start node (on S)
     * @param sEntry true to start an S-entry walk (INTERSECT), false for S-exit (UNION/DIFF)
     * @param cForward true to walk C forward (INTERSECT/UNION), false to walk C backward (DIFF)
     */
    static double[][] trace(GHNode sHead, GHNode start, boolean sEntry, boolean cForward) {
        ArrayList<double[]> pts = new ArrayList<>();
        GHNode cur = start;
        boolean onS = true;
        boolean wantEntry = sEntry; // on S, stop when reaching a node with entry == !wantEntry... see below
        int guard = 0;
        int maxSteps = 10000;
        while (guard++ < maxSteps) {
            if (cur.visited && (cur == start) && !pts.isEmpty()) break;
            pts.add(new double[]{cur.x, cur.y});
            cur.visited = true;
            GHNode next = onS ? cur.next : (cForward ? cur.next : cur.prev);
            // The node we step TO decides the switch: on S we stop at a node
            // whose entry flag is the opposite of the walk's start polarity.
            boolean stopEntry = !wantEntry;
            if (next.isX && (next.entry == stopEntry)) {
                // Collect the stop node, then jump to its twin.
                pts.add(new double[]{next.x, next.y});
                next.visited = true;
                if (next == start) break;
                cur = next.twin;
                onS = !onS;
                // After the jump, the walk polarity on the new polygon is the
                // twin's entry flag (the walk continues from an entry node on
                // the other polygon for INTERSECT/UNION; for DIFF the C walk
                // stops at an entry node, so the polarity flips the same way).
                wantEntry = cur.entry;
                if (cur == start) break;
                continue;
            }
            cur = next;
            if (cur == start) break;
        }
        if (pts.size() < 3) return null;
        double[][] poly = toArray(pts);
        if (Math.abs(signedArea(poly)) <= 1e-12) return null;
        return poly;
    }

    static GHNode buildList(double[][] poly) {
        GHNode head = null, prev = null;
        for (double[] v : poly) {
            GHNode n = new GHNode(v[0], v[1]);
            if (head == null) head = n;
            if (prev != null) { prev.next = n; n.prev = prev; }
            prev = n;
        }
        prev.next = head;
        head.prev = prev;
        return head;
    }

    static ArrayList<GHNode> listNodes(GHNode head) {
        ArrayList<GHNode> out = new ArrayList<>();
        GHNode cur = head;
        do {
            out.add(cur);
            cur = cur.next;
        } while (cur != head);
        return out;
    }

    /** Insert recorded hits into the circular list, sorted by t along each edge. */
    static void insertHits(GHNode head, ArrayList<ArrayList<double[]>> hits) {
        ArrayList<GHNode> nodes = listNodes(head);
        for (int i = 0; i < nodes.size(); i++) {
            ArrayList<double[]> h = hits.get(i);
            if (h.isEmpty()) continue;
            h.sort((a, b) -> Double.compare(a[0], b[0]));
            GHNode edgeStart = nodes.get(i);
            GHNode edgeEnd = edgeStart.next;
            GHNode prev = edgeStart;
            for (double[] hit : h) {
                GHNode n = new GHNode(hit[1], hit[2]);
                n.isX = true;
                n.prev = prev;
                n.next = edgeEnd;
                prev.next = n;
                edgeEnd.prev = n;
                prev = n;
            }
        }
    }
}
