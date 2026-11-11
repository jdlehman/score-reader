package java.awt.event;
/** Minimal java.awt.event.FocusListener. */
public interface FocusListener extends java.util.EventListener {
    void focusGained(FocusEvent e);
    void focusLost(FocusEvent e);
}
