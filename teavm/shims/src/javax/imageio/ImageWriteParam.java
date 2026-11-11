package javax.imageio;
/** Minimal javax.imageio.ImageWriteParam. */
public class ImageWriteParam {
    public static final int MODE_DISABLED = 0;
    public static final int MODE_DEFAULT = 1;
    public static final int MODE_EXPLICIT = 2;
    public static final int MODE_COPY_FROM_METADATA = 3;
    protected ImageWriteParam() {}
    public ImageWriteParam(java.util.Locale locale) {}
    public java.util.Locale getLocale() { return java.util.Locale.getDefault(); }
    public int getCompressionMode() { return MODE_DEFAULT; }
    public void setCompressionMode(int mode) {}
    public void setSourceSubsampling(int sourceXSubsampling, int sourceYSubsampling, int subsamplingXOffset, int subsamplingYOffset) {}
    public int getSourceXSubsampling() { return 1; }
    public int getSourceYSubsampling() { return 1; }
    public int getSubsamplingXOffset() { return 0; }
    public int getSubsamplingYOffset() { return 0; }
    public float getCompressionQuality() { return 1.0f; }
    public void setCompressionQuality(float quality) {}
    public String[] getCompressionTypes() { return new String[0]; }
    public String getCompressionType() { return null; }
    public void setCompressionType(String compressionType) {}
    public boolean isCompressionLossless() { return true; }
    public void unsetCompression() {}
    public int getTilingMode() { return MODE_DEFAULT; }
    public void setTilingMode(int mode) {}
    public boolean canWriteTiles() { return false; }
    public int getTileWidth() { return 0; }
    public int getTileHeight() { return 0; }
    public void setTiling(int tileWidth, int tileHeight, int tileGridXOffset, int tileGridYOffset) {}
    public void unsetTiling() {}
    public boolean canWriteProgressive() { return false; }
    public int getProgressiveMode() { return MODE_DEFAULT; }
    public void setProgressiveMode(int mode) {}
}
