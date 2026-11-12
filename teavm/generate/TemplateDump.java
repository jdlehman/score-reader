// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
import java.awt.Rectangle;
import java.awt.geom.Point2D;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import org.audiveris.omr.glyph.Shape;
import org.audiveris.omr.glyph.ShapeSet;
import org.audiveris.omr.image.Anchored.Anchor;
import org.audiveris.omr.image.PixelDistance;
import org.audiveris.omr.image.Template;
import org.audiveris.omr.image.TemplateFactory;
import org.audiveris.omr.ui.symbol.MusicFamily;
import org.audiveris.omr.ui.symbol.MusicFont;

/**
 * Audiveris's note-head templates, as desktop Audiveris draws them from its music fonts, saved for
 * the WebAssembly build, which has no fonts (teavm/entry/src/teavm/PreRenderedTemplates.java reads
 * them). One file a font and point size: &lt;out&gt;/&lt;Family&gt;-&lt;size&gt;.bin.
 *   java -Djava.awt.headless=true -cp .work/patched.jar:.work/lib/*:&lt;classes&gt; TemplateDump &lt;out&gt; &lt;from&gt; &lt;to&gt; &lt;Family&gt;...
 * <p>
 * A file: "SRT1", the count of templates (short), then each: its shape's name (UTF), width and
 * height (shorts), slim bounds (x, y, width, height: shorts), the count of anchors (byte) and each
 * anchor's name (UTF) and offset (two doubles), the count of key points (int) and each point's x, y
 * (bytes, 0 to 255) and distance (a signed byte: whole numbers, negative inside a hollow head;
 * checked).
 */
public class TemplateDump
{
    public static void main (String[] args)
        throws Exception
    {
        final Path out = Path.of(args[0]);
        final int from = Integer.parseInt(args[1]);
        final int to = Integer.parseInt(args[2]);
        Files.createDirectories(out);
        MusicFont.checkMusicFont();

        for (int a = 3; a < args.length; a++) {
            final MusicFamily family = MusicFamily.valueOf(args[a]);

            for (int size = from; size <= to; size++) {
                final TemplateFactory.Catalog catalog = TemplateFactory.getInstance().getCatalog(family, size);
                final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                final DataOutputStream data = new DataOutputStream(bytes);
                data.writeBytes("SRT1");
                data.writeShort(ShapeSet.Heads.size());

                for (Shape shape : ShapeSet.Heads) {
                    final Template t = catalog.getTemplate(shape);
                    data.writeUTF(shape.name());
                    data.writeShort(t.getWidth());
                    data.writeShort(t.getHeight());

                    final Rectangle slim = t.getSlimBounds();
                    data.writeShort(slim.x);
                    data.writeShort(slim.y);
                    data.writeShort(slim.width);
                    data.writeShort(slim.height);

                    final Map<Anchor, Point2D> offsets = t.getOffsets();
                    data.writeByte(offsets.size());

                    for (Map.Entry<Anchor, Point2D> e : offsets.entrySet()) {
                        data.writeUTF(e.getKey().name());
                        data.writeDouble(e.getValue().getX());
                        data.writeDouble(e.getValue().getY());
                    }

                    final List<PixelDistance> points = t.getKeyPoints();
                    data.writeInt(points.size());

                    for (PixelDistance p : points) {
                        if ((p.x < 0) || (p.x > 255) || (p.y < 0) || (p.y > 255) || (p.d < -128) || (p.d > 127)
                                || (p.d != Math.rint(p.d))) {
                            throw new IllegalStateException(family + " " + size + " " + shape + ": key point "
                                    + p.x + "," + p.y + "," + p.d + " doesn't fit in bytes");
                        }

                        data.writeByte(p.x);
                        data.writeByte(p.y);
                        data.writeByte((int) p.d);
                    }
                }

                data.flush();
                Files.write(out.resolve(family.name() + "-" + size + ".bin"), bytes.toByteArray());
            }
        }
    }
}
