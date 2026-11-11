package java.awt.event;
/** Minimal java.awt.event.KeyListener. */
public interface KeyListener extends java.util.EventListener {
    void keyTyped(KeyEvent e);
    void keyPressed(KeyEvent e);
    void keyReleased(KeyEvent e);
}
