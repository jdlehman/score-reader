package java.awt.event;
/** Minimal java.awt.event.KeyAdapter. */
public abstract class KeyAdapter implements KeyListener {
    public void keyTyped(KeyEvent e) {}
    public void keyPressed(KeyEvent e) {}
    public void keyReleased(KeyEvent e) {}
}
