import java.awt.Rectangle;
import java.awt.font.TextLayout;
import java.awt.geom.Rectangle2D;
import java.awt.image.BufferedImage;
import java.io.FileWriter;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;

import org.audiveris.omr.glyph.Shape;
import org.audiveris.omr.ui.symbol.FontSymbol;
import org.audiveris.omr.ui.symbol.MusicFamily;
import org.audiveris.omr.ui.symbol.MusicFont;
import org.audiveris.omr.ui.symbol.OmrFont;
import org.audiveris.omr.ui.symbol.ShapeSymbol;

/**
 * Phase §19: dump native Bravura symbol metrics on desktop Java with the
 * real Bravura font, for the TeaVM font shim.
 *
 * For every Shape with a Bravura symbol, dumps (at reference size 84 =
 * interline 21, the hymn's):
 *   - the shape's layout bounds / advance / ascent / descent (via
 *     FontSymbol.getLayout(), i.e. the exact path AbstractInter
 *     .getSymbolBounds uses), and its code points;
 *   - the shape's centroidOffset ratios (mass centre of the rendered
 *     symbol image, relative to area centre), via reflection after
 *     triggering getCentroid().
 * For every distinct code point used (shape codes + time digits + space):
 *   - single-glyph TextLayout bounds + advance at sizes 40/84/168, to
 *     prove bounds scale linearly with size (unit metrics) and to let the
 *     shim compose multi-code strings (digit strings, dotted notes) from
 *     per-codepoint metrics.
 * Also verifies (a) multi-code composition: composed bounds/advance from
 * singles vs the real multi-code TextLayout, and (b) centroid
 * size-independence: mass-centre ratios from buildImage at sizes 40/168
 * vs the reflected centroidOffset (computed at STANDARD_INTERLINE 20).
 *
 * Usage: SymbolMetricsDump <out.json>
 */
public class SymbolMetricsDump
{
    private static String num (double v)
    {
        if (Double.isNaN(v) || Double.isInfinite(v)) {
            return "null";
        }
        return Double.toString(v);
    }

    private static String rectJson (Rectangle2D r)
    {
        return "{\"x\":" + num(r.getX()) + ",\"y\":" + num(r.getY())
                + ",\"w\":" + num(r.getWidth()) + ",\"h\":" + num(r.getHeight()) + "}";
    }

    /** Mass-centre ratios (xBar/w - 0.5, yBar/h - 0.5) of a rendered image. */
    private static double[] massRatios (BufferedImage img)
    {
        double xBar = 0, yBar = 0, weight = 0;
        int w = img.getWidth(), h = img.getHeight();
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                int argb = img.getRGB(x, y);
                double alpha = ((argb >> 24) & 0xff) / 255.0;
                if (alpha > 0) {
                    xBar += alpha * x;
                    yBar += alpha * y;
                    weight += alpha;
                }
            }
        }
        if (weight == 0) {
            return null;
        }
        return new double[] { (xBar / weight) / w - 0.5, (yBar / weight) / h - 0.5 };
    }

    public static void main (String[] args) throws Exception
    {
        String out = args[0];
        MusicFont.checkMusicFont();

        Map<String, Object> shapes = new LinkedHashMap<>();
        TreeSet<Integer> codepoints = new TreeSet<>();
        int nShapes = 0, nNoSymbol = 0, nNoLayout = 0, nCentroidErr = 0;

        Field centroidField = ShapeSymbol.class.getDeclaredField("centroidOffset");
        centroidField.setAccessible(true);

        for (Shape shape : Shape.values()) {
            FontSymbol fs;
            try {
                fs = shape.getFontSymbolByInterline(MusicFamily.Bravura, 21);
            } catch (Exception ex) {
                nNoSymbol++;
                continue;
            }
            if (fs == null || fs.symbol == null) {
                nNoSymbol++;
                continue;
            }
            TextLayout layout;
            try {
                layout = fs.getLayout();
            } catch (Throwable ex) {
                // e.g. MetronomeSymbol.getParams pulls in GUI singletons
                // (StubsController / BSAF Application) that cannot run in
                // this headless harness; the shape is skipped, not fatal.
                nNoLayout++;
                continue;
            }
            if (layout == null) {
                nNoLayout++;
                continue;
            }
            nShapes++;
            int[] codes = MusicFamily.Bravura.getSymbols().getCode(shape);
            if (codes != null) {
                for (int cp : codes) {
                    codepoints.add(cp);
                }
            }
            Rectangle2D b = layout.getBounds();
            double[] centroid = null;
            String centroidErr = null;
            try {
                // Trigger the lazy computation, then read the exact ratios.
                fs.symbol.getCentroid(new Rectangle(0, 0, 1000, 1000));
                java.awt.geom.Point2D off =
                        (java.awt.geom.Point2D) centroidField.get(fs.symbol);
                if (off != null) {
                    centroid = new double[] { off.getX(), off.getY() };
                }
            } catch (Throwable ex) {
                centroidErr = ex.toString();
                nCentroidErr++;
            }
            StringBuilder sb = new StringBuilder();
            sb.append("{\"codes\":[");
            if (codes != null) {
                for (int i = 0; i < codes.length; i++) {
                    if (i > 0) {
                        sb.append(',');
                    }
                    sb.append(codes[i]);
                }
            }
            sb.append("],\"bounds\":").append(rectJson(b))
                    .append(",\"advance\":").append(num(layout.getAdvance()))
                    .append(",\"ascent\":").append(num(layout.getAscent()))
                    .append(",\"descent\":").append(num(layout.getDescent()))
                    .append(",\"fontSize\":").append(num(fs.font.getSize2D()));
            if (centroid != null) {
                sb.append(",\"centroid\":[").append(num(centroid[0])).append(',')
                        .append(num(centroid[1])).append(']');
            } else {
                sb.append(",\"centroid\":null");
                if (centroidErr != null) {
                    sb.append(",\"centroidError\":\"")
                            .append(centroidErr.replace("\"", "'")).append('"');
                }
            }
            sb.append('}');
            shapes.put(shape.name(), sb.toString());
        }

        // Time-digit code points + space (multi-code strings are composed
        // from these in the shim).
        int[] zeroCode = MusicFamily.Bravura.getSymbols().getCode(Shape.TIME_ZERO);
        if (zeroCode != null) {
            for (int d = 0; d <= 9; d++) {
                codepoints.add(zeroCode[0] + d);
            }
        }
        codepoints.add(0x20);

        // Per-codepoint single-glyph metrics at sizes 40/84/168.
        Map<Integer, String> cpJson = new TreeMap<>();
        double maxLinErr = 0;
        for (int cp : codepoints) {
            String s = new String(new int[] { cp }, 0, 1);
            StringBuilder sb = new StringBuilder();
            sb.append('{');
            boolean first = true;
            double[][] units = new double[3][];
            int ui = 0;
            for (int size : new int[] { 40, 84, 168 }) {
                MusicFont font = MusicFont.getMusicFont(MusicFamily.Bravura, size);
                TextLayout layout = new TextLayout(s, font, OmrFont.frc);
                Rectangle2D b = layout.getBounds();
                double adv = layout.getAdvance();
                units[ui++] = new double[] { adv / size, b.getX() / size, b.getY() / size,
                        b.getWidth() / size, b.getHeight() / size };
                if (!first) {
                    sb.append(',');
                }
                first = false;
                sb.append('"').append(size).append("\":{\"adv\":").append(num(adv))
                        .append(",\"bounds\":").append(rectJson(b)).append('}');
            }
            // Unit metrics come from the reference size 84; the 40/168
            // sizes only check linearity against it.
            double[] ref = units[1];
            for (int k = 0; k < 3; k++) {
                if (k == 1) {
                    continue;
                }
                for (int i = 0; i < 5; i++) {
                    maxLinErr = Math.max(maxLinErr, Math.abs(units[k][i] - ref[i]));
                }
            }
            sb.append(",\"unit\":{\"adv\":").append(num(ref[0]))
                    .append(",\"x\":").append(num(ref[1]))
                    .append(",\"y\":").append(num(ref[2]))
                    .append(",\"w\":").append(num(ref[3]))
                    .append(",\"h\":").append(num(ref[4])).append("}}");
            cpJson.put(cp, sb.toString());
        }

        // Composition check: for every multi-code shape string and for
        // digit strings, compose bounds/advance from single-codepoint
        // metrics and compare with the real multi-code TextLayout.
        MusicFont font84 = MusicFont.getMusicFont(MusicFamily.Bravura, 84);
        List<String> compLines = new ArrayList<>();
        double maxCompBoundsErr = 0, maxCompAdvErr = 0;
        int nComp = 0, nCompFail = 0;
        List<String> testStrings = new ArrayList<>();
        for (Map.Entry<String, Object> e : shapes.entrySet()) {
            // Rebuild the string from the dumped codes via the JSON text is
            // awkward; use the live codes instead.
        }
        for (Shape shape : Shape.values()) {
            int[] codes = MusicFamily.Bravura.getSymbols().getCode(shape);
            if (codes == null || codes.length < 2) {
                continue;
            }
            testStrings.add(new String(codes, 0, codes.length));
        }
        // Digit strings, built from the TIME_ZERO code the same way
        // MusicFont.layoutNumberByCode does (TextLayout has no getText()).
        int[] zc = MusicFamily.Bravura.getSymbols().getCode(Shape.TIME_ZERO);
        if (zc != null) {
            for (int n : new int[] { 0, 1, 2, 4, 10, 12, 44, 100, 120, 200, 444 }) {
                StringBuilder ds = new StringBuilder();
                for (char c : String.valueOf(n).toCharArray()) {
                    ds.append((char) (zc[0] + (c - '0')));
                }
                testStrings.add(ds.toString());
            }
        }
        // Map codepoint -> unit metrics (size 84 values from the dump above,
        // recomputed live here for the check).
        Map<Integer, double[]> unit = new TreeMap<>();
        for (int cp : codepoints) {
            String s = new String(new int[] { cp }, 0, 1);
            TextLayout l = new TextLayout(s, font84, OmrFont.frc);
            Rectangle2D b = l.getBounds();
            unit.put(cp, new double[] { l.getAdvance(), b.getX(), b.getY(),
                    b.getWidth(), b.getHeight() });
        }
        for (String s : testStrings) {
            TextLayout real = new TextLayout(s, font84, OmrFont.frc);
            Rectangle2D rb = real.getBounds();
            double x0 = Double.MAX_VALUE, y0 = Double.MAX_VALUE;
            double x1 = -Double.MAX_VALUE, y1 = -Double.MAX_VALUE;
            double adv = 0;
            boolean missing = false;
            int[] cps = s.codePoints().toArray();
            for (int cp : cps) {
                double[] u = unit.get(cp);
                if (u == null) {
                    missing = true;
                    break;
                }
                x0 = Math.min(x0, adv + u[1]);
                y0 = Math.min(y0, u[2]);
                x1 = Math.max(x1, adv + u[1] + u[3]);
                y1 = Math.max(y1, u[2] + u[4]);
                adv += u[0];
            }
            nComp++;
            if (missing) {
                nCompFail++;
                compLines.add("MISSING cp in: " + s.codePoints().toArray().length);
                continue;
            }
            double eb = Math.max(
                    Math.max(Math.abs(x0 - rb.getX()), Math.abs(y0 - rb.getY())),
                    Math.max(Math.abs((x1 - x0) - rb.getWidth()),
                            Math.abs((y1 - y0) - rb.getHeight())));
            double ea = Math.abs(adv - real.getAdvance());
            maxCompBoundsErr = Math.max(maxCompBoundsErr, eb);
            maxCompAdvErr = Math.max(maxCompAdvErr, ea);
            if (eb > 0.01 || ea > 0.01) {
                nCompFail++;
                compLines.add("FAIL len=" + cps.length + " boundsErr=" + eb + " advErr=" + ea);
            }
        }

        // Centroid size-independence: mass ratios from buildImage at 40/168
        // vs the reflected centroidOffset (STANDARD_INTERLINE 20).
        double maxCentroidSizeErr = 0;
        int nCentroidChecked = 0, nCentroidImgErr = 0;
        for (Shape shape : Shape.values()) {
            FontSymbol fs = shape.getFontSymbolByInterline(MusicFamily.Bravura, 21);
            if (fs == null || fs.symbol == null) {
                continue;
            }
            double[] ref;
            try {
                fs.symbol.getCentroid(new Rectangle(0, 0, 1000, 1000));
                java.awt.geom.Point2D off =
                        (java.awt.geom.Point2D) centroidField.get(fs.symbol);
                if (off == null) {
                    continue;
                }
                ref = new double[] { off.getX(), off.getY() };
            } catch (Throwable ex) {
                continue;
            }
            for (int size : new int[] { 40, 168 }) {
                try {
                    MusicFont f = MusicFont.getBaseFontBySize(MusicFamily.Bravura, size);
                    BufferedImage img = fs.symbol.buildImage(f);
                    if (img == null) {
                        continue;
                    }
                    if (img == null) {
                        continue;
                    }
                    double[] m = massRatios(img);
                    if (m == null) {
                        continue;
                    }
                    nCentroidChecked++;
                    maxCentroidSizeErr = Math.max(maxCentroidSizeErr,
                            Math.max(Math.abs(m[0] - ref[0]), Math.abs(m[1] - ref[1])));
                } catch (Throwable ex) {
                    nCentroidImgErr++;
                }
            }
        }

        // Ascent/descent sample.
        TextLayout nb = font84.layoutShapeByCode(Shape.NOTEHEAD_BLACK);
        TextLayout gc = font84.layoutShapeByCode(Shape.G_CLEF);

        StringBuilder json = new StringBuilder();
        json.append("{\"family\":\"Bravura\",\"refSize\":84");
        json.append(",\"counts\":{\"shapes\":").append(nShapes)
                .append(",\"noSymbol\":").append(nNoSymbol)
                .append(",\"noLayout\":").append(nNoLayout)
                .append(",\"centroidErr\":").append(nCentroidErr)
                .append(",\"codepoints\":").append(codepoints.size()).append('}');
        json.append(",\"maxLinearityErr\":").append(num(maxLinErr));
        json.append(",\"composition\":{\"n\":").append(nComp)
                .append(",\"fail\":").append(nCompFail)
                .append(",\"maxBoundsErr\":").append(num(maxCompBoundsErr))
                .append(",\"maxAdvErr\":").append(num(maxCompAdvErr))
                .append(",\"failLines\":[");
        for (int i = 0; i < compLines.size(); i++) {
            if (i > 0) {
                json.append(',');
            }
            json.append('"').append(compLines.get(i).replace("\"", "'")).append('"');
        }
        json.append("]}");
        json.append(",\"centroidSizeCheck\":{\"n\":").append(nCentroidChecked)
                .append(",\"imgErr\":").append(nCentroidImgErr)
                .append(",\"maxErr\":").append(num(maxCentroidSizeErr)).append('}');
        json.append(",\"ascentDescent84\":{\"noteheadBlack\":[").append(num(nb.getAscent()))
                .append(',').append(num(nb.getDescent()))
                .append("],\"gClef\":[").append(num(gc.getAscent()))
                .append(',').append(num(gc.getDescent())).append("]}");
        json.append(",\"codepoints\":{");
        boolean first = true;
        for (Map.Entry<Integer, String> e : cpJson.entrySet()) {
            if (!first) {
                json.append(',');
            }
            first = false;
            json.append('"').append(e.getKey()).append("\":").append(e.getValue());
        }
        json.append("},\"shapes\":{");
        first = true;
        for (Map.Entry<String, Object> e : shapes.entrySet()) {
            if (!first) {
                json.append(',');
            }
            first = false;
            json.append('"').append(e.getKey()).append("\":").append(e.getValue());
        }
        json.append("}}");
        try (FileWriter w = new FileWriter(out)) {
            w.write(json.toString());
        }
        System.out.println("shapes=" + nShapes + " noSymbol=" + nNoSymbol + " noLayout=" + nNoLayout
                + " centroidErr=" + nCentroidErr + " codepoints=" + codepoints.size());
        System.out.println("maxLinearityErr=" + maxLinErr);
        System.out.println("composition n=" + nComp + " fail=" + nCompFail
                + " maxBoundsErr=" + maxCompBoundsErr + " maxAdvErr=" + maxCompAdvErr);
        System.out.println("centroidSizeCheck n=" + nCentroidChecked + " imgErr=" + nCentroidImgErr
                + " maxErr=" + maxCentroidSizeErr);
        System.out.println("WROTE " + out);
    }
}
