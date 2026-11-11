package teavm;

import java.awt.image.BufferedImage;
import java.awt.image.DataBufferByte;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.util.Base64;
import java.util.List;

import org.audiveris.omr.sheet.Book;
import org.audiveris.omr.sheet.Sheet;
import org.audiveris.omr.sheet.SheetStub;
import org.audiveris.omr.sheet.SystemInfo;
import org.audiveris.omr.sig.inter.HeadInter;
import org.audiveris.omr.sig.inter.Inter;
import org.audiveris.omr.step.OmrStep;
import org.audiveris.omr.util.OmrExecutors;
import org.teavm.jso.JSBody;

/**
 * Headless TeaVM entry point: grey image bytes come from JS (base64),
 * then the Audiveris reading pipeline runs LOAD..HEADS on one sheet stub.
 */
public class TeavmMain
{
    @JSBody(params = {}, script = "return globalThis.__greyB64;")
    private static native String greyB64 ();

    @JSBody(params = {}, script = "return globalThis.__greyW;")
    private static native int greyW ();

    @JSBody(params = {}, script = "return globalThis.__greyH;")
    private static native int greyH ();

    @JSBody(params = {}, script = "return globalThis.__ocrText;")
    private static native String ocrText ();

    @JSBody(params = {}, script = "return globalThis.__ocrLang;")
    private static native String ocrLang ();

    @JSBody(params = { "s" }, script = "globalThis.__mxlB64 = s;")
    private static native void setMxlB64 (String s);

    // §37: all scores as a JSON array of base64 strings (see export loop).
    @JSBody(params = { "s" }, script = "globalThis.__mxlB64List = s;")
    private static native void setMxlB64List (String s);

    public static void main (String[] args)
    {
        try {
            run();
        } catch (Throwable t) {
            System.out.println("TEAVM FAILED: " + t);
            t.printStackTrace(System.out);
        }
    }

    private static void run ()
        throws Exception
    {
        int w = greyW();
        int h = greyH();
        System.out.println("IMAGE w=" + w + " h=" + h);

        byte[] grey = Base64.getDecoder().decode(greyB64());
        System.out.println("GREY BYTES " + grey.length);

        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_BYTE_GRAY);
        byte[] data = ((DataBufferByte) img.getRaster().getDataBuffer()).getData();
        System.arraycopy(grey, 0, data, 0, Math.min(grey.length, data.length));
        TeavmImageHolder.image = img;

        OmrExecutors.restart();

        // §14: Main.main calls MusicFont.checkMusicFont() at startup
        // (Main.java:269), which populates every family's symbol table via
        // populateAllSymbols(). TeavmMain bypasses Main, so without this
        // call Symbols.symbolMap stays empty, Symbols.getSymbol() returns
        // null for small heads, and TemplateSymbol.getParams() NPEs in HEADS
        // (trap in TemplateFactory template building, full-out22/23).
        org.audiveris.omr.ui.symbol.MusicFont.checkMusicFont();

        Book book = new Book(Paths.get("hymn-satb.png"));
        book.addStub(new SheetStub(book, 1));
        SheetStub stub = book.getStub(1);

        // §23: OCR language from the runner (globalThis.__ocrLang, e.g. "deu"
        // for Lindenbaum); default is the stub's own default ("eng").
        // Set before TEXTS runs so SheetScanner asks for the right languages.
        String ocrLang = ocrLang();
        if ((ocrLang != null) && !ocrLang.isEmpty()) {
            stub.getOcrLanguagesParam().setSpecific(ocrLang);
            System.out.println("OCR LANG " + ocrLang);
        }

        // §37 (DIAG43): the shipped app (reader.js:260) and the desktop
        // comparison harness both run Audiveris with
        // ProcessingSwitches.indentations=false. TeavmMain never set it, so
        // the switch defaulted to true and SystemManager.checkIndentations
        // flagged mid-page systems as movement starts — BWV 227 p01: systems
        // #1 and #3 — splitting the book into two scores where desktop makes
        // one (desktop control with the switch ON splits identically and
        // exports p01.mvt1.mxl + p01.mvt2.mxl). Set it on the stub, the same
        // Param.setSpecific mechanism the OCR language uses above.
        // checkIndentations runs in GRID, before reachStep(HEADS) below.
        stub.getProcessingSwitches().getParam(
                org.audiveris.omr.sheet.ProcessingSwitch.indentations).setSpecific(Boolean.FALSE);
        System.out.println("INDENTATIONS false");

        long t0 = System.nanoTime();
        try {
            stub.reachStep(OmrStep.HEADS, false);
        } catch (Throwable t) {
            throw t;
        }
        long t1 = System.nanoTime();
        System.out.println("REACH HEADS ms=" + ((t1 - t0) / 1_000_000));
        System.out.println("LATEST STEP " + stub.getLatestStep());

        Sheet sheet = stub.getSheet();
        System.out.println("INTERLINE " + sheet.getInterline());

        List<SystemInfo> systems = sheet.getSystems();
        System.out.println("SYSTEMS " + systems.size());

        int staves = 0;
        int heads = 0;
        long chk = 0;

        for (SystemInfo system : systems) {
            staves += system.getStaves().size();

            List<Inter> hs = system.getSig().inters(HeadInter.class);
            heads += hs.size();

            for (Inter inter : hs) {
                java.awt.Rectangle b = inter.getBounds();
                chk += b.x + b.y + b.width + b.height;
            }
        }

        System.out.println("STAVES " + staves + " HEADS " + heads + " CHECK " + chk);

        // §23: two-phase OCR. Phase 1 (no __ocrText): TEXTS has just run
        // SheetScanner, whose BrowserOCR.recognize exported the clean image
        // to JS and returned no lines — stop here so the runner can OCR it
        // and re-run with __ocrText set. Phase 2 (__ocrText present): run
        // the full pipeline as before; recognize() parses the prefed text.
        final String prefed = ocrText();
        final boolean hasOcr = (prefed != null) && !prefed.isEmpty();
        System.out.println("OCR PREFED " + hasOcr);

        if (!hasOcr) {
            long ts = System.nanoTime();
            stub.reachStep(OmrStep.TEXTS, false);
            long te = System.nanoTime();
            System.out.println("PHASE1 TEXTS ms=" + ((te - ts) / 1_000_000)
                    + " totalMs=" + ((te - t0) / 1_000_000)
                    + " LATEST=" + stub.getLatestStep());
            System.out.println("PHASE1 DONE — clean image exported to JS, OCR pending");
            return;
        }

        // §20: continue step by step past HEADS — SYMBOLS, LINKS, RHYTHMS,
        // PAGE — printing per-step timing and SIG totals at each, so the run
        // stays comparable to the HEADS numbers above and to the desktop
        // mirror (SigDumpPage). reachStep is incremental: each call runs
        // only the steps after the latest reached one.
        for (OmrStep step : new OmrStep[] { OmrStep.SYMBOLS, OmrStep.LINKS, OmrStep.RHYTHMS, OmrStep.PAGE }) {
            long ts = System.nanoTime();
            stub.reachStep(step, false);
            long te = System.nanoTime();

            int heads20 = 0;
            int total20 = 0;
            long chk20 = 0;

            for (SystemInfo system : sheet.getSystems()) {
                List<Inter> hs = system.getSig().inters(HeadInter.class);
                heads20 += hs.size();
                total20 += system.getSig().inters(inter -> true).size();

                for (Inter inter : hs) {
                    java.awt.Rectangle b = inter.getBounds();
                    chk20 += b.x + b.y + b.width + b.height;
                }
            }

            System.out.println("REACH " + step + " ms=" + ((te - ts) / 1_000_000)
                    + " totalMs=" + ((te - t0) / 1_000_000)
                    + " LATEST=" + stub.getLatestStep()
                    + " HEADS=" + heads20 + " SIG=" + total20 + " CHECK=" + chk20);
        }

        // Score summary after PAGE (no .mxl yet — export is the next wall).
        for (org.audiveris.omr.score.Score score : book.getScores()) {
            org.audiveris.omr.score.Page page = score.getFirstPage();
            System.out.println("SCORE parts=" + score.getLogicalParts().size()
                    + " measures=" + ((page == null) ? -1 : page.getMeasureCount()));
        }

        // §22 Phase D: hand-rolled non-JAXB export (MxlWriter). The §21
        // ScoreExporter/JAXB call is gone for good — JAXB RI cannot build
        // under TeaVM. MxlWriter walks the Score model directly and returns
        // the MusicXML text; it is base64'd out to JS for the runner to save.
        // §37: export ALL scores, not just the last one. TeavmMain used to
        // call setMxlB64 once per score, so the runner saved only the last
        // score of a multi-score book (BWV 227 p01: 13 + 8 measures, only
        // the 8 survived — 920 of the 937-note BWV shortfall in the
        // full-out82 multi-page run). Desktop exports one BOOK.mvt#.ext file
        // per score (Book.export); the runner mirrors that. __mxlB64 keeps
        // the FIRST score (movement 1) for old runners; __mxlB64List carries
        // all of them as a JSON array of base64 strings (base64 has no
        // JSON-special characters, so plain concatenation is safe).
        java.util.List<String> mxlB64s = new java.util.ArrayList<>();

        for (org.audiveris.omr.score.Score score : book.getScores()) {
            long te = System.nanoTime();
            String xml = MxlWriter.build(score);
            long tx = System.nanoTime();
            mxlB64s.add(Base64.getEncoder().encodeToString(xml.getBytes(StandardCharsets.UTF_8)));
            System.out.println("MXL len=" + xml.length()
                    + " exportMs=" + ((tx - te) / 1_000_000)
                    + " totalMs=" + ((tx - t0) / 1_000_000));
        }

        if (!mxlB64s.isEmpty()) {
            setMxlB64(mxlB64s.get(0));

            StringBuilder list = new StringBuilder("[");
            for (int i = 0; i < mxlB64s.size(); i++) {
                if (i > 0) {
                    list.append(',');
                }
                list.append('"').append(mxlB64s.get(i)).append('"');
            }
            list.append(']');
            setMxlB64List(list.toString());
            System.out.println("MXL count=" + mxlB64s.size());
        }

        System.out.println("TEAVM DONE");
    }
}
