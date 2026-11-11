package java.awt.event;
/** Minimal java.awt.event.WindowFocusListener. */
public interface WindowFocusListener extends java.util.EventListener {
    void windowGainedFocus(WindowEvent e);
    void windowLostFocus(WindowEvent e);
}
