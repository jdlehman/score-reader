package java.awt;
/** Minimal java.awt.FontFormatException (thrown when a font file is malformed).
 *  The program catches it, and TeaVM has no class for it: without one, TeaVM emits an empty
 *  type for it and the module fails to load at that catch. (OmrFont.createFont) */
public class FontFormatException extends Exception {
    public FontFormatException(String reason) { super(reason); }
}
