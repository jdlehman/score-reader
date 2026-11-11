package java.awt.event;
/** Minimal java.awt.event.MouseListener. */
public interface MouseListener extends java.util.EventListener {
    void mouseClicked(MouseEvent e);
    void mousePressed(MouseEvent e);
    void mouseReleased(MouseEvent e);
    void mouseEntered(MouseEvent e);
    void mouseExited(MouseEvent e);
}
