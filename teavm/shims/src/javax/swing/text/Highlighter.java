package javax.swing.text;
/** Minimal javax.swing.text.Highlighter. */
public interface Highlighter {
    void install(javax.swing.text.JTextComponent c);
    void deinstall(javax.swing.text.JTextComponent c);
    void paint(java.awt.Graphics g);
    Object addHighlight(int p0, int p1, HighlightPainter p) throws BadLocationException;
    void removeHighlight(Object tag);
    void removeAllHighlights();
    void changeHighlight(Object tag, int p0, int p1) throws BadLocationException;
    Highlight[] getHighlights();
    interface Highlight {
        int getStartOffset();
        int getEndOffset();
        HighlightPainter getPainter();
    }
    interface HighlightPainter {
        void paint(java.awt.Graphics g, int p0, int p1, java.awt.Shape bounds, JTextComponent c);
    }
}
