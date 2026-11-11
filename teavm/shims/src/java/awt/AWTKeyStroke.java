package java.awt;
/** Minimal java.awt.AWTKeyStroke. */
public class AWTKeyStroke implements java.io.Serializable {
    protected int keyCode, modifiers;
    protected char keyChar;
    protected boolean onKeyRelease;
    protected AWTKeyStroke() {}
    protected AWTKeyStroke(int keyCode, int modifiers, boolean onKeyRelease) {
        this.keyCode = keyCode; this.modifiers = modifiers; this.onKeyRelease = onKeyRelease;
    }
    public static AWTKeyStroke getAWTKeyStroke(int keyCode, int modifiers, boolean onKeyRelease) {
        return new AWTKeyStroke(keyCode, modifiers, onKeyRelease);
    }
    public static AWTKeyStroke getAWTKeyStroke(int keyCode, int modifiers) {
        return new AWTKeyStroke(keyCode, modifiers, false);
    }
    public static AWTKeyStroke getAWTKeyStroke(char keyChar) {
        AWTKeyStroke k = new AWTKeyStroke();
        k.keyChar = keyChar;
        return k;
    }
    public static AWTKeyStroke getAWTKeyStroke(String s) { return new AWTKeyStroke(); }
    public int getKeyCode() { return keyCode; }
    public char getKeyChar() { return keyChar; }
    public int getModifiers() { return modifiers; }
    public boolean isOnKeyRelease() { return onKeyRelease; }
}
