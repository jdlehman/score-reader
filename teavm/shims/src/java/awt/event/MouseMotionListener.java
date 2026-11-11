package java.awt.event;
/** Minimal java.awt.event.MouseMotionListener. */
public interface MouseMotionListener extends java.util.EventListener {
    void mouseDragged(MouseEvent e);
    void mouseMoved(MouseEvent e);
}
