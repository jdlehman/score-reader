// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
package teavm;

import java.awt.image.BufferedImage;
import java.awt.image.DataBufferByte;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.util.Base64;
import java.util.List;

import org.audiveris.omr.constant.ConstantManager;
import org.audiveris.omr.score.Score;
import org.audiveris.omr.sheet.Book;
import org.audiveris.omr.sheet.SheetStub;
import org.audiveris.omr.step.OmrStep;
import org.audiveris.omr.text.SheetScanner;
import org.audiveris.omr.ui.symbol.MusicFont;
import org.audiveris.omr.util.OmrExecutors;
import org.teavm.jso.JSBody;
import org.teavm.jso.JSExport;

/**
 * Audiveris in the browser: what app/teavm.js calls. A read is a book of pages. Each page is read
 * in two calls, so that its words can be read in between: Tesseract (tesseract.js) is
 * asynchronous JavaScript, and a call into WebAssembly can't wait for it.
 * <ol>
 * <li>{@link #setConstant} for each setting, as Audiveris's -constant gives them</li>
 * <li>{@link #openBook}</li>
 * <li>for each page: set globalThis.__greyB64, __greyW and __greyH to its grey pixels, then
 * {@link #startPage}, which reads it up to its words and leaves the image Tesseract should read in
 * globalThis.__ocrImageB64 (with __ocrImageW, __ocrImageH, __ocrLang and __ocrPsm); set
 * globalThis.__ocrText to what Tesseract read (BrowserOCR's lines), then {@link #finishPage}</li>
 * <li>{@link #scores}: the pages gathered into scores, as MusicXML</li>
 * </ol>
 * Progress: globalThis.__teavmStep(page, step) is called as each step of a page starts.
 */
public class TeavmMain
{
    @JSBody(params = {}, script = "return globalThis.__greyB64;")
    private static native String greyB64 ();

    @JSBody(params = {}, script = "return globalThis.__greyW;")
    private static native int greyW ();

    @JSBody(params = {}, script = "return globalThis.__greyH;")
    private static native int greyH ();

    @JSBody(params = {}, script = "globalThis.__ocrText = null; globalThis.__ocrImageB64 = null;")
    private static native void clearOcr ();

    @JSBody(params = { "page", "step" },
            script = "if (globalThis.__teavmStep) globalThis.__teavmStep(page, step);")
    private static native void stepStarts (int page,
                                           String step);

    /** The book being read. */
    private static Book book;

    public static void main (String[] args)
    {
        // nothing: the page calls the methods below
    }

    /** A setting, as Audiveris's command line takes it: -constant name=value. */
    @JSExport
    public static void setConstant (String name,
                                    String value)
    {
        ConstantManager.TEAVM_CONSTANTS.put(name, value);
    }

    /**
     * Start a book of so many pages.
     *
     * @param pages     the count of pages
     * @param languages the language(s) of the words, as Tesseract names them ("deu", "eng+lat")
     */
    @JSExport
    public static void openBook (int pages,
                                 String languages)
    {
        OmrExecutors.restart();
        // Audiveris's Main reads the music font's symbols at start: without them, finding heads fails
        MusicFont.checkMusicFont();
        book = new Book(Paths.get("score.pdf"));

        for (int n = 1; n <= pages; n++) {
            final SheetStub stub = new SheetStub(book, n);
            book.addStub(stub);

            if ((languages != null) && !languages.isEmpty()) {
                stub.getOcrLanguagesParam().setSpecific(languages);
            }
        }
    }

    /**
     * Read page n, from the grey pixels in globalThis.__greyB64, up to its words.
     *
     * @return true if it left an image for Tesseract; false if the page could not be read (it is
     *         then left out of the score)
     */
    @JSExport
    public static boolean startPage (int n)
    {
        final SheetStub stub = book.getStub(n);
        clearOcr();

        try {
            final int w = greyW();
            final int h = greyH();
            final BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_BYTE_GRAY);
            final byte[] data = ((DataBufferByte) img.getRaster().getDataBuffer()).getData();
            final byte[] grey = Base64.getDecoder().decode(greyB64());
            System.arraycopy(grey, 0, data, 0, Math.min(grey.length, data.length));
            TeavmImageHolder.image = img;

            for (OmrStep step : OmrStep.values()) {
                if (step.compareTo(OmrStep.CUE_BEAMS) > 0) {
                    break;
                }

                stepStarts(n, step.name());
                stub.reachStep(step, false);
                TeavmImageHolder.image = null; // the sheet has it now
            }

            // what the TEXTS step will give Tesseract (BrowserOCR leaves it for the page, as there
            // is no text for it yet): built now, from the page as it is before that step
            new SheetScanner(stub.getSheet()).scanSheet();

            return true;
        } catch (Throwable ex) {
            leaveOut(stub, ex);

            return false;
        }
    }

    /**
     * Read the rest of page n, with the words Tesseract read in globalThis.__ocrText.
     *
     * @return false if the page could not be read (it is then left out of the score)
     */
    @JSExport
    public static boolean finishPage (int n)
    {
        final SheetStub stub = book.getStub(n);

        try {
            for (OmrStep step : OmrStep.values()) {
                if (step.compareTo(OmrStep.CUE_BEAMS) <= 0) {
                    continue;
                }

                stepStarts(n, step.name());
                stub.reachStep(step, false);

                if (step == OmrStep.TEXTS) {
                    // the page's words are used: any later OCR (a boxed rehearsal letter) gets none
                    clearOcr();
                }
            }

            // keep the page, but only what the score needs (as the page's CheerpJ reading does)
            stub.getSheet().lightenForExport();

            return true;
        } catch (Throwable ex) {
            leaveOut(stub, ex);

            return false;
        } finally {
            clearOcr();
        }
    }

    /**
     * The pages read, gathered into scores (one a movement), each as MusicXML.
     *
     * @return a JSON array of base64 strings (of the UTF-8 MusicXML), empty if no page was read
     */
    @JSExport
    public static String scores ()
    {
        stepStarts(0, "EXPORT");

        final List<SheetStub> stubs = book.getValidSelectedStubs();
        final StringBuilder json = new StringBuilder("[");

        if (!stubs.isEmpty()) {
            // what Book.transcribe does once every page is read (the pages were read above, page by
            // page; TeaVM's Book can't drive them itself): the parts of each score, the voices
            // across its pages. The scores themselves were made as the pages were read.
            book.reduceScores(stubs, book.getScores());

            for (Score score : book.getScores()) {
                final String xml = MxlWriter.build(score);

                if (json.length() > 1) {
                    json.append(',');
                }

                json.append('"')
                        .append(Base64.getEncoder().encodeToString(xml.getBytes(StandardCharsets.UTF_8)))
                        .append('"');
            }
        }

        return json.append(']').toString();
    }

    /** A page that failed is left out of the book, so the other pages still make a score. */
    private static void leaveOut (SheetStub stub,
                                  Throwable ex)
    {
        System.out.println("WARN Sheet ignored: " + stub + " could not be read, and is left out: " + ex);
        TeavmImageHolder.image = null;

        if (stub.isValid()) {
            stub.invalidate();
        }
    }
}
