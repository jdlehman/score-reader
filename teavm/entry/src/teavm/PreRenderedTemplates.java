// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
package teavm;

import java.awt.Rectangle;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.audiveris.omr.glyph.Shape;
import org.audiveris.omr.image.Anchored.Anchor;
import org.audiveris.omr.image.PixelDistance;
import org.audiveris.omr.image.Template;
import org.audiveris.omr.ui.symbol.MusicFamily;
import org.teavm.jso.JSBody;

/**
 * Audiveris's note-head templates, which this build can't draw (it has no fonts). Desktop Audiveris
 * draws them, a file a music font and point size (teavm/generate/TemplateDump.java, run by
 * teavm/build.sh), and the page hands over the one asked for, when asked
 * (globalThis.__teavmTemplates, app/teavm.js). So the templates are the desktop's, at the size the
 * page needs. TeaVM's TemplateFactory asks here first (make_patches.py, ROUND 12).
 */
public class PreRenderedTemplates
{
    /** The base64 of the file for a font and point size, or null if there is none. */
    @JSBody(params = { "family", "size" },
            script = "return globalThis.__teavmTemplates ? globalThis.__teavmTemplates(family, size) : null;")
    private static native String load (String family,
                                       int size);

    /** Without a file for the size asked for, the nearest within this many points is used. */
    private static final int MAX_DIFF = 8;

    /** The templates read so far, by "family-size" asked for (null: none found). */
    private static final Map<String, Map<Shape, Template>> catalogs = new HashMap<>();

    /**
     * The template for a head shape in a music font at a point size.
     *
     * @return the template, or null if there is none (TemplateFactory then draws it with no font)
     */
    public static Template getTemplate (Shape shape,
                                       MusicFamily family,
                                       int pointSize)
    {
        final String key = family.name() + "-" + pointSize;

        if (!catalogs.containsKey(key)) {
            Map<Shape, Template> catalog = null;

            for (int d = 0; (d <= MAX_DIFF) && (catalog == null); d++) {
                catalog = read(family, pointSize - d);

                if ((catalog == null) && (d > 0)) {
                    catalog = read(family, pointSize + d);
                }
            }

            if (catalog == null) {
                System.out.println("WARN No head templates for " + key);
            }

            catalogs.put(key, catalog);
        }

        final Map<Shape, Template> catalog = catalogs.get(key);

        return (catalog != null) ? catalog.get(shape) : null;
    }

    /** One file's templates (see TemplateDump for its layout), or null if there is no file. */
    private static Map<Shape, Template> read (MusicFamily family,
                                              int size)
    {
        final String b64 = load(family.name(), size);

        if (b64 == null) {
            return null;
        }

        try {
            final DataInputStream in = new DataInputStream(
                    new ByteArrayInputStream(Base64.getDecoder().decode(b64)));
            final byte[] magic = new byte[4];
            in.readFully(magic);

            if ((magic[0] != 'S') || (magic[1] != 'R') || (magic[2] != 'T') || (magic[3] != '1')) {
                throw new IOException("not a template file");
            }

            final Map<Shape, Template> templates = new HashMap<>();
            final int count = in.readShort();

            for (int i = 0; i < count; i++) {
                final Shape shape = Shape.valueOf(in.readUTF());
                final int width = in.readShort();
                final int height = in.readShort();
                final Rectangle slim = new Rectangle(in.readShort(), in.readShort(), in.readShort(),
                        in.readShort());
                final int anchors = in.readUnsignedByte();
                final List<Object[]> offsets = new ArrayList<>(anchors);

                for (int a = 0; a < anchors; a++) {
                    offsets.add(new Object[] { Anchor.valueOf(in.readUTF()), in.readDouble(), in.readDouble() });
                }

                final int points = in.readInt();
                final List<PixelDistance> keyPoints = new ArrayList<>(points);

                for (int p = 0; p < points; p++) {
                    final int x = in.readUnsignedByte();
                    final int y = in.readUnsignedByte();
                    keyPoints.add(new PixelDistance(x, y, in.readByte()));
                }

                final Template template = new Template(shape, family, size, width, height, keyPoints, slim);

                for (Object[] o : offsets) {
                    template.putOffset((Anchor) o[0], (Double) o[1], (Double) o[2]);
                }

                templates.put(shape, template);
            }

            return templates;
        } catch (IOException | RuntimeException ex) {
            System.out.println("WARN Head templates " + family.name() + "-" + size + " unreadable: " + ex);

            return null;
        }
    }
}
