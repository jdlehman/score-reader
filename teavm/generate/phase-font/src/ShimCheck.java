import java.awt.Font;
import java.awt.font.FontRenderContext;
import java.awt.font.TextLayout;
import java.awt.geom.Rectangle2D;
import java.io.FileInputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * §19 desktop verification for the shim TextLayout: prints bounds +
 * advance for every test string (phase-font/test-strings.txt, one
 * comma-separated code-point list per line) at sizes 84/92/108.
 *
 * Two modes, same harness, same output format (so a plain diff compares):
 *   stock <bravura.otf> <strings>  — real JDK TextLayout with the real
 *       Bravura font loaded via Font.createFont.
 *   shim <strings>                 — shim TextLayout via --patch-module
 *       java.desktop=<shims/classes>; font is new Font("Bravura", ...),
 *       the same name the TeaVM platform-font fallback produces.
 * Run with --patch-module ONLY in shim mode; in stock mode the JDK
 * TextLayout runs unpatched.
 */
public class ShimCheck
{
    public static void main (String[] args) throws Exception
    {
        boolean shim = args[0].equals("shim");
        List<String> lines;
        Font baseReal = null;
        if (shim) {
            lines = Files.readAllLines(Paths.get(args[1]));
        } else {
            baseReal = Font.createFont(Font.TRUETYPE_FONT, new FileInputStream(args[1]));
            lines = Files.readAllLines(Paths.get(args[2]));
        }
        FontRenderContext frc = new FontRenderContext(null, true, true);
        int n = 0;
        for (String line : lines) {
            if (line.isBlank()) {
                continue;
            }
            String[] parts = line.split(",");
            int[] cps = new int[parts.length];
            for (int i = 0; i < parts.length; i++) {
                cps[i] = Integer.parseInt(parts[i].trim());
            }
            String s = new String(cps, 0, cps.length);
            for (int size : new int[] { 84, 92, 108 }) {
                Font font = shim ? new Font("Bravura", Font.PLAIN, size)
                        : baseReal.deriveFont((float) size);
                TextLayout layout = new TextLayout(s, font, frc);
                Rectangle2D b = layout.getBounds();
                System.out.println(line + " size=" + size
                        + " x=" + b.getX() + " y=" + b.getY()
                        + " w=" + b.getWidth() + " h=" + b.getHeight()
                        + " adv=" + layout.getAdvance());
                n++;
            }
        }
        System.out.println("CHECKED " + n);
    }
}
