package javax.imageio.metadata;
/** Minimal javax.imageio.metadata.IIOMetadata (correct package; the
 *  javax.imageio.IIOMetadata stub is a separate, legacy-named class). */
public abstract class IIOMetadata {
    public String[] getMetadataFormatNames() { return new String[0]; }
    public boolean isStandardMetadataFormatSupported() { return false; }
    public String getNativeMetadataFormatName() { return null; }
    public org.w3c.dom.Node getAsTree(String formatName) { return null; }
    public void setFromTree(String formatName, org.w3c.dom.Node root) {}
    public void mergeTree(String formatName, org.w3c.dom.Node root) {}
    public void reset() {}
}
