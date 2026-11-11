import java.awt.font.TextLayout;
import java.awt.geom.Rectangle2D;

import org.audiveris.omr.ui.symbol.MusicFamily;
import org.audiveris.omr.ui.symbol.MusicFont;
import org.audiveris.omr.ui.symbol.OmrFont;

/**
 * §45: dump the Bravura LINE_CODE (0xe010) metrics on desktop Java with the
 * real Bravura font, in the exact JSON shape phase-font/symbol-metrics.json
 * uses per codepoint (sizes 40/84/168 + unit from 84). 0xe010 was missing
 * from the §19 table (157 codepoints), so the shim TextLayout fell back
 * to the stub bounds (height = font size) and populatePitchOffsets
 * computed lineHeight = 200 instead of 6.40625, collapsing pitchHeight
 * 25.0 -> 0.80 and inflating every pitch offset ~31x — which is what
 * killed every flat key signature under Wasm (DIAG51c).
 *
 * Usage (desktop JDK 25 + stock jars, headless):
 *   javac -cp <program jars> -d phase55/classes LineCodeDump.java
 *   java -Djava.awt.headless=true -cp phase55/classes:<program jars> LineCodeDump
 */
public class LineCodeDump
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

    public static void main (String[] args) throws Exception
    {
        MusicFont.checkMusicFont();

        int cp = 0xe010;
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
        double maxLinErr = 0;
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
                .append(",\"h\":").append(num(ref[4])).append('}');
        sb.append('}');
        System.out.println("LINECODE maxLinErr=" + maxLinErr);
        System.out.println(sb.toString());
    }
}
