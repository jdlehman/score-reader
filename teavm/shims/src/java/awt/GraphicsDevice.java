package java.awt;
public abstract class GraphicsDevice {
    public static final int TYPE_RASTER_SCREEN = 0;
    public static final int TYPE_PRINTER = 1;
    public static final int TYPE_IMAGE_BUFFER = 2;
    public abstract int getType();
    public abstract String getIDstring();
    public abstract GraphicsConfiguration[] getConfigurations();
    public abstract GraphicsConfiguration getDefaultConfiguration();
    public java.awt.DisplayMode getDisplayMode() { return null; }
}
