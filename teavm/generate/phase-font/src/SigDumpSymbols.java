import java.awt.image.BufferedImage;
import java.io.PrintWriter;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.imageio.ImageIO;

import org.audiveris.omr.sheet.Book;
import org.audiveris.omr.sheet.Sheet;
import org.audiveris.omr.sheet.SheetStub;
import org.audiveris.omr.sheet.SystemInfo;
import org.audiveris.omr.sig.inter.Inter;
import org.audiveris.omr.step.OmrStep;
import org.audiveris.omr.ui.symbol.MusicFont;
import org.audiveris.omr.util.OmrExecutors;

/**
 * §19 SYMBOLS probe desktop counterpart of TeavmMain's DIAG18: run the hymn
 * through SYMBOLS and dump every inter in every system's SIG, same format.
 * Usage: SigDump <png> <outfile>
 */
public class SigDumpSymbols
{
    public static void main (String[] args) throws Exception
    {
        String png = args[0];
        String out = args[1];
        BufferedImage img = ImageIO.read(new java.io.File(png));

        java.lang.reflect.Field cliField = org.audiveris.omr.Main.class.getDeclaredField("cli");
        cliField.setAccessible(true);
        cliField.set(null, new org.audiveris.omr.CLI(org.audiveris.omr.WellKnowns.TOOL_NAME));

        OmrExecutors.restart();
        MusicFont.checkMusicFont();

        Book book = new Book(Paths.get(png));
        book.addStub(new SheetStub(book, 1));
        SheetStub stub = book.getStub(1);
        stub.reachStep(OmrStep.SYMBOLS, false);

        Sheet sheet = stub.getSheet();
        List<SystemInfo> systems = sheet.getSystems();

        // §19: same post-step counts as TeavmMain (HeadInter count AFTER
        // SYMBOLS — the step prunes the BLACK/VOID duplicate pairs).
        int staves = 0;
        int heads = 0;
        long chk = 0;
        for (SystemInfo system : systems) {
            staves += system.getStaves().size();
            List<Inter> hs = system.getSig().inters(org.audiveris.omr.sig.inter.HeadInter.class);
            heads += hs.size();
            for (Inter inter : hs) {
                java.awt.Rectangle b = inter.getBounds();
                chk += b.x + b.y + b.width + b.height;
            }
        }
        System.out.println("SYSTEMS " + systems.size() + " STAVES " + staves
                + " HEADS " + heads + " CHECK " + chk);

        List<String> sigDump = new ArrayList<>();
        for (SystemInfo system : systems) {
            for (Inter inter : system.getSig().inters(inter -> true)) {
                java.awt.Rectangle b = inter.getBounds();
                sigDump.add(system.getId() + " " + inter.getClass().getSimpleName()
                        + " shape=" + inter.getShape()
                        + " grade=" + String.format("%.4f", inter.getGrade())
                        + " good=" + inter.isGood()
                        + " box=" + b.x + "," + b.y + "," + b.width + "," + b.height);
            }
        }
        Collections.sort(sigDump);
        try (PrintWriter w = new PrintWriter(out)) {
            for (String line : sigDump) {
                w.println("SIG " + line);
            }
        }
        System.out.println("SIGDUMP DONE " + sigDump.size() + " inters -> " + out);

        // DIAG19 (§18): same source-image fingerprints as TeavmMain (FNV-1a;
        // TeaVM's MessageDigest/String.format proved unusable in full-out34).
        for (org.audiveris.omr.sheet.Picture.SourceKey key
                : new org.audiveris.omr.sheet.Picture.SourceKey[] {
                        org.audiveris.omr.sheet.Picture.SourceKey.BINARY,
                        org.audiveris.omr.sheet.Picture.SourceKey.NO_STAFF }) {
            ij.process.ByteProcessor bp = sheet.getPicture().getSource(key);
            byte[] px = (byte[]) bp.getPixels();
            long fnv = 0xcbf29ce484222325L;
            long sum = 0;
            int zeros = 0;
            for (int i = 0; i < px.length; i++) {
                int v = px[i] & 0xff;
                fnv = (fnv ^ v) * 0x100000001b3L;
                sum += v;
                if (v == 0) {
                    zeros++;
                }
            }
            System.out.println("DIAG19 " + key + " w=" + bp.getWidth() + " h=" + bp.getHeight()
                    + " fnv=" + Long.toHexString(fnv) + " sum=" + sum + " zeros=" + zeros);
        }

        // DIAG20 (§18): same header-range dump as TeavmMain.
        for (org.audiveris.omr.sheet.SystemInfo system : sheet.getSystems()) {
            for (org.audiveris.omr.sheet.Staff staff : system.getStaves()) {
                org.audiveris.omr.sheet.header.StaffHeader header = staff.getHeader();
                org.audiveris.omr.sig.inter.ClefInter clef = header.clef;
                String clefBox = (clef == null) ? "null"
                        : (clef.getBounds() + " glyph=" + ((clef.getGlyph() == null) ? "null"
                                : clef.getGlyph().getBounds()));
                System.out.println("DIAG20 sys=" + system.getId() + " staff=" + staff.getId()
                        + " headerStart=" + header.start + " clefRange=" + header.clefRange
                        + " clefStop=" + staff.getClefStop() + " clef=" + clefBox);
            }
        }
    }
}
