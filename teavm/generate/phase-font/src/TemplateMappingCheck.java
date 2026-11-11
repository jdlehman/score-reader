import java.awt.Rectangle;
import java.awt.geom.Point2D;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;

import org.audiveris.omr.glyph.Shape;
import org.audiveris.omr.glyph.ShapeSet;
import org.audiveris.omr.image.PixelDistance;
import org.audiveris.omr.image.Template;
import org.audiveris.omr.image.TemplateFactory;
import org.audiveris.omr.image.Anchored.Anchor;
import org.audiveris.omr.ui.symbol.MusicFamily;
import org.audiveris.omr.ui.symbol.MusicFont;

import teavm.PreRenderedTemplates;

/**
 * §19 round-trip (successor to the Phase B RoundTrip, whose simulated
 * requests 47/54/64 and DESKTOP_PER_TEAVM_POINT no longer exist): the
 * shim TextLayout now returns real Bravura bounds, so BlackHeadSizer
 * calibrates to the desktop point size directly — requested == desktop.
 * For each catalog point size, request that size and check the
 * pre-rendered Template equals the live-built native template at that
 * size, field by field (width, height, slim bounds, point size, every
 * anchor offset, every key point x/y/d, plus a SHA-256 of the key list).
 * Exit non-zero on any mismatch.
 */
public class TemplateMappingCheck
{
    public static void main (String[] args) throws Exception
    {
        MusicFont.checkMusicFont();
        TemplateFactory factory = TemplateFactory.getInstance();
        int failures = 0;
        int checked = 0;

        for (int ps : PreRenderedTemplates.CATALOG_POINT_SIZES) {
            int requested = ps; // §19: requested IS the desktop point size
            System.out.println("desktop " + ps + " <- TeaVM requested " + requested);
            TemplateFactory.Catalog cat = factory.getCatalog(MusicFamily.Bravura, ps);

            for (Shape shape : ShapeSet.Heads) {
                checked++;
                Template live = cat.getTemplate(shape);
                live.getKeyPoints(); // force lazy build
                Template pre = PreRenderedTemplates.getTemplate(shape, MusicFamily.Bravura, requested);
                String tag = "ps=" + ps + " " + shape;
                if (pre == null) {
                    System.out.println("FAIL " + tag + ": pre-rendered is null");
                    failures++;
                    continue;
                }
                if (pre.getWidth() != live.getWidth() || pre.getHeight() != live.getHeight()) {
                    System.out.println("FAIL " + tag + ": size pre=" + pre.getWidth() + "x" + pre.getHeight()
                            + " live=" + live.getWidth() + "x" + live.getHeight());
                    failures++;
                }
                if (!pre.getSlimBounds().equals(live.getSlimBounds())) {
                    System.out.println("FAIL " + tag + ": slim pre=" + pre.getSlimBounds()
                            + " live=" + live.getSlimBounds());
                    failures++;
                }
                if (pre.getPointSize() != ps) {
                    System.out.println("FAIL " + tag + ": pointSize pre=" + pre.getPointSize() + " want " + ps);
                    failures++;
                }
                Map<Anchor, Point2D> po = pre.getOffsets();
                Map<Anchor, Point2D> lo = live.getOffsets();
                if (!po.keySet().equals(lo.keySet())) {
                    System.out.println("FAIL " + tag + ": anchor keys pre=" + po.keySet() + " live=" + lo.keySet());
                    failures++;
                } else {
                    for (Anchor a : po.keySet()) {
                        if (!po.get(a).equals(lo.get(a))) {
                            System.out.println("FAIL " + tag + ": anchor " + a + " pre=" + po.get(a)
                                    + " live=" + lo.get(a));
                            failures++;
                        }
                    }
                }
                List<PixelDistance> pk = pre.getKeyPoints();
                List<PixelDistance> lk = live.getKeyPoints();
                if (pk.size() != lk.size()) {
                    System.out.println("FAIL " + tag + ": keyPoints size pre=" + pk.size() + " live=" + lk.size());
                    failures++;
                } else {
                    MessageDigest mdp = MessageDigest.getInstance("SHA-256");
                    MessageDigest mdl = MessageDigest.getInstance("SHA-256");
                    boolean mismatch = false;
                    for (int i = 0; i < pk.size(); i++) {
                        PixelDistance p = pk.get(i);
                        PixelDistance l = lk.get(i);
                        mdp.update((byte) (p.x >> 8)); mdp.update((byte) p.x);
                        mdp.update((byte) (p.y >> 8)); mdp.update((byte) p.y);
                        mdp.update(Double.toString(p.d).getBytes(java.nio.charset.StandardCharsets.UTF_8));
                        mdp.update((byte) ',');
                        mdl.update((byte) (l.x >> 8)); mdl.update((byte) l.x);
                        mdl.update((byte) (l.y >> 8)); mdl.update((byte) l.y);
                        mdl.update(Double.toString(l.d).getBytes(java.nio.charset.StandardCharsets.UTF_8));
                        mdl.update((byte) ',');
                        if (!mismatch && (p.x != l.x || p.y != l.y || p.d != l.d)) {
                            System.out.println("FAIL " + tag + ": keyPoint[" + i + "] pre=(" + p.x + "," + p.y
                                    + "," + p.d + ") live=(" + l.x + "," + l.y + "," + l.d + ")");
                            failures++;
                            mismatch = true;
                        }
                    }
                    String hp = HexFormat.of().formatHex(mdp.digest());
                    String hl = HexFormat.of().formatHex(mdl.digest());
                    if (!hp.equals(hl)) {
                        System.out.println("FAIL " + tag + ": keyPoints SHA pre=" + hp + " live=" + hl);
                        failures++;
                    } else {
                        System.out.println("PASS " + tag + " kp=" + pk.size() + " sha=" + hp.substring(0, 12));
                    }
                }
            }
        }
        // Negative checks: unknown family and far-out size must fall back (null).
        Template t1 = PreRenderedTemplates.getTemplate(Shape.NOTEHEAD_BLACK, MusicFamily.Leland, 54);
        Template t2 = PreRenderedTemplates.getTemplate(Shape.NOTEHEAD_BLACK, MusicFamily.Bravura, 10);
        Template t3 = PreRenderedTemplates.getTemplate(Shape.NOTEHEAD_BLACK, MusicFamily.Bravura, 200);
        System.out.println("fallback Leland/54 -> " + t1 + " (want null)");
        System.out.println("fallback Bravura/10 -> " + t2 + " (want null)");
        System.out.println("fallback Bravura/200 -> " + t3 + " (want null)");
        if (t1 != null || t2 != null || t3 != null) failures++;

        System.out.println("RoundTrip: " + checked + " templates checked, " + failures + " failures");
        if (failures > 0) System.exit(1);
    }
}
