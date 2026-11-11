package java.awt.event;
/** Minimal java.awt.event.ComponentListener. */
public interface ComponentListener extends java.util.EventListener {
    void componentResized(ComponentEvent e);
    void componentMoved(ComponentEvent e);
    void componentShown(ComponentEvent e);
    void componentHidden(ComponentEvent e);
}
