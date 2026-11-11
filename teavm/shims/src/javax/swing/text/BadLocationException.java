package javax.swing.text;
/** Minimal javax.swing.text.BadLocationException. */
public class BadLocationException extends Exception {
    protected int offs;
    public BadLocationException(String s, int offs) { super(s); this.offs = offs; }
    public int offsetRequested() { return offs; }
}
