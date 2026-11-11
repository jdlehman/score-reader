package java.awt;
/** Minimal java.awt.DisplayMode (analysis stub). */
public class DisplayMode {
    public static final int BIT_DEPTH_MULTI = -1;
    public static final int REFRESH_RATE_UNKNOWN = 0;
    private final int width, height, bitDepth, refreshRate;
    public DisplayMode(int width, int height, int bitDepth, int refreshRate) {
        this.width = width; this.height = height; this.bitDepth = bitDepth; this.refreshRate = refreshRate;
    }
    public int getWidth() { return width; }
    public int getHeight() { return height; }
    public int getBitDepth() { return bitDepth; }
    public int getRefreshRate() { return refreshRate; }
}
