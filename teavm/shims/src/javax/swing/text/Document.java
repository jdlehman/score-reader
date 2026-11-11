package javax.swing.text;
/** Minimal javax.swing.text.Document. */
public interface Document {
    int getLength();
    void addDocumentListener(javax.swing.event.DocumentListener listener);
    void removeDocumentListener(javax.swing.event.DocumentListener listener);
    void addUndoableEditListener(javax.swing.event.UndoableEditListener listener);
    void removeUndoableEditListener(javax.swing.event.UndoableEditListener listener);
    Object getProperty(Object key);
    void putProperty(Object key, Object value);
    void remove(int offs, int len) throws BadLocationException;
    void insertString(int offset, String str, AttributeSet a) throws BadLocationException;
    String getText(int offset, int length) throws BadLocationException;
    void getText(int offset, int length, Segment txt) throws BadLocationException;
    Position getStartPosition();
    Position getEndPosition();
    Position createPosition(int offs) throws BadLocationException;
    Element[] getRootElements();
    Element getDefaultRootElement();
    void render(Runnable r);
}
