package javax.swing;
/** Minimal javax.swing.KeyStroke. */
public class KeyStroke implements java.io.Serializable {
    protected int keyCode, modifiers;
    protected char keyChar;
    protected boolean onKeyRelease;
    protected KeyStroke() {}
    protected KeyStroke(int keyCode, int modifiers, boolean onKeyRelease) {
        this.keyCode = keyCode; this.modifiers = modifiers; this.onKeyRelease = onKeyRelease;
    }
    protected KeyStroke(char keyChar, int modifiers) { this.keyChar = keyChar; this.modifiers = modifiers; }
    public static KeyStroke getKeyStroke(int keyCode, int modifiers, boolean onKeyRelease) {
        return new KeyStroke(keyCode, modifiers, onKeyRelease);
    }
    public static KeyStroke getKeyStroke(int keyCode, int modifiers) { return new KeyStroke(keyCode, modifiers, false); }
    public static KeyStroke getKeyStroke(char keyChar) { return new KeyStroke(keyChar, 0); }
    public static KeyStroke getKeyStroke(String s) { return new KeyStroke(); }
    public static KeyStroke getKeyStrokeForEvent(java.awt.event.KeyEvent e) { return new KeyStroke(); }
    public static KeyStroke getKeyStroke(int keyCode, int modifiers, boolean onKeyRelease, int dummy) { return new KeyStroke(keyCode, modifiers, onKeyRelease); }
    public int getKeyCode() { return keyCode; }
    public char getKeyChar() { return keyChar; }
    public int getModifiers() { return modifiers; }
    public boolean isOnKeyRelease() { return onKeyRelease; }
    public int getKeyEventType() { return 0; }
}
