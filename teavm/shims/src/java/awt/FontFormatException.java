package java.awt;
/** Minimal java.awt.FontFormatException (thrown when a font file is malformed).
 *  Added 2026-11-08: it was missing from TeaVM's classpath, which made TeaVM
 *  emit an empty root struct for it and Node reject the module at function
 *  #19489 (OmrFont.createFont catch dispatch, br_on_cast Throwable ->
 *  FontFormatException). Same defect class as #18066 (TimeoutException). */
public class FontFormatException extends Exception {
    public FontFormatException(String reason) { super(reason); }
}
