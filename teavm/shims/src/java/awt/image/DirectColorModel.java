package java.awt.image;
/** Minimal java.awt.image.DirectColorModel. */
public class DirectColorModel extends ColorModel {
    protected int redMask, greenMask, blueMask, alphaMask;
    public DirectColorModel(int bits, int rmask, int gmask, int bmask) {
        this(bits, rmask, gmask, bmask, 0);
    }
    public DirectColorModel(int bits, int rmask, int gmask, int bmask, int amask) {
        super(bits);
        redMask = rmask; greenMask = gmask; blueMask = bmask; alphaMask = amask;
    }
    public int getRedMask() { return redMask; }
    public int getGreenMask() { return greenMask; }
    public int getBlueMask() { return blueMask; }
    public int getAlphaMask() { return alphaMask; }
    @Override public int getRed(int pixel) { return 0; }
    @Override public int getGreen(int pixel) { return 0; }
    @Override public int getBlue(int pixel) { return 0; }
    @Override public int getAlpha(int pixel) { return 255; }
    @Override public int getRGB(int pixel) { return pixel; }
}
