import java.awt.Rectangle;
import java.awt.image.BufferedImage;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

import org.audiveris.omr.glyph.Shape;
import org.audiveris.omr.ui.symbol.FontSymbol;
import org.audiveris.omr.ui.symbol.MusicFamily;
import org.audiveris.omr.ui.symbol.MusicFont;
import org.audiveris.omr.ui.symbol.ShapeSymbol;

/**
 * §19 diagnostic: for each shape, compare the reflected centroidOffset
 * (computed by Audiveris from the STANDARD_INTERLINE image) with manual
 * mass-centre ratios from buildImage at sizes 40/80/168. Lists every
 * shape whose max error exceeds 0.02, so we can tell genuine
 * size-dependence apart from a bug in the manual computation (size 80
 * must match the reflected value exactly if the computation is right).
 */
public class CentroidDiag
{
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
        MusicFont.checkMusicFont();
        Field f = ShapeSymbol.class.getDeclaredField("centroidOffset");
        f.setAccessible(true);
        List<String> bad = new ArrayList<>();
        double max80 = 0;
        int n = 0;
        for (Shape shape : Shape.values()) {
            FontSymbol fs;
            try {
                fs = shape.getFontSymbolByInterline(MusicFamily.Bravura, 21);
            } catch (Throwable ex) {
                continue;
            }
            if (fs == null || fs.symbol == null) {
                continue;
            }
            double[] ref;
            try {
                fs.symbol.getCentroid(new Rectangle(0, 0, 1000, 1000));
                java.awt.geom.Point2D off = (java.awt.geom.Point2D) f.get(fs.symbol);
                if (off == null) {
                    continue;
                }
                ref = new double[] { off.getX(), off.getY() };
            } catch (Throwable ex) {
                continue;
            }
            n++;
            StringBuilder sb = new StringBuilder();
            sb.append(shape).append(" ref=[").append(String.format("%.4f,%.4f", ref[0], ref[1])).append(']');
            double worst = 0;
            for (int size : new int[] { 40, 80, 168 }) {
                try {
                    MusicFont mf = MusicFont.getBaseFontBySize(MusicFamily.Bravura, size);
                    BufferedImage img = fs.symbol.buildImage(mf);
                    if (img == null) {
                        continue;
                    }
                    double[] m = massRatios(img);
                    if (m == null) {
                        sb.append(" size").append(size).append("=BLANK");
                        continue;
                    }
                    double e = Math.max(Math.abs(m[0] - ref[0]), Math.abs(m[1] - ref[1]));
                    worst = Math.max(worst, e);
                    if (size == 80) {
                        max80 = Math.max(max80, e);
                    }
                    sb.append(" size").append(size).append(" err=").append(String.format("%.4f", e));
                } catch (Throwable ex) {
                    sb.append(" size").append(size).append(" ERR ").append(ex);
                }
            }
            if (worst > 0.02) {
                bad.add(sb.toString());
            }
        }
        System.out.println("checked=" + n + " maxErrAt80=" + max80 + " badCount=" + bad.size());
        for (String s : bad) {
            System.out.println(s);
        }
    }
}
