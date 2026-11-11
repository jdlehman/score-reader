package java.awt;
/** Minimal java.awt.Toolkit (headless stub). */
public abstract class Toolkit {
    private static Toolkit toolkit;
    public static synchronized Toolkit getDefaultToolkit() {
        if (toolkit == null) toolkit = new HeadlessToolkit();
        return toolkit;
    }
    public abstract int getScreenResolution();
    public abstract Dimension getScreenSize();
    public java.awt.Insets getScreenInsets(java.awt.GraphicsConfiguration gc) { return new java.awt.Insets(0, 0, 0, 0); }
    public int getMenuShortcutKeyMask() { return 0; }
    public Object getDesktopProperty(String name) { return null; }
    public void beep() {}
    public java.awt.datatransfer.Clipboard getSystemClipboard() { return null; }
    public java.awt.Image createImage(String filename) { return null; }
    public java.awt.Image createImage(java.net.URL url) { return null; }
    public boolean getLockingKeyState(int keyCode) { return false; }
    public void setLockingKeyState(int keyCode, boolean on) {}
    static final class HeadlessToolkit extends Toolkit {
        @Override public int getScreenResolution() { return 72; }
        @Override public Dimension getScreenSize() { return new Dimension(0, 0); }
    }
}
