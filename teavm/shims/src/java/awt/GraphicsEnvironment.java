package java.awt;
/** Minimal java.awt.GraphicsEnvironment (headless stub). */
public abstract class GraphicsEnvironment {
    private static GraphicsEnvironment env;
    public static synchronized GraphicsEnvironment getLocalGraphicsEnvironment() {
        if (env == null) env = new HeadlessEnvironment();
        return env;
    }
    public abstract Font[] getAllFonts();
    public abstract String[] getAvailableFontFamilyNames();
    public abstract GraphicsDevice getDefaultScreenDevice();
    public GraphicsDevice[] getScreenDevices() { return new GraphicsDevice[0]; }
    public static boolean isHeadless() { return true; }
    public boolean registerFont(Font font) { return true; }
    static final class HeadlessEnvironment extends GraphicsEnvironment {
        @Override public Font[] getAllFonts() { return new Font[0]; }
        @Override public String[] getAvailableFontFamilyNames() { return new String[0]; }
        @Override public GraphicsDevice getDefaultScreenDevice() { return null; }
    }
}
