package javax.imageio;
/** Minimal javax.imageio.IIOMetadata. */
public abstract class IIOMetadata {
    public String[] getMetadataFormatNames() { return new String[0]; }
    public boolean isStandardMetadataFormatSupported() { return false; }
}
