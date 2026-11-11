package javax.swing.event;
/** Minimal javax.swing.event.DocumentListener. */
public interface DocumentListener extends java.util.EventListener {
    void insertUpdate(DocumentEvent e);
    void removeUpdate(DocumentEvent e);
    void changedUpdate(DocumentEvent e);
}
