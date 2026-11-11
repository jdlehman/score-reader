package javax.xml.stream;
/** Minimal javax.xml.stream.XMLOutputFactory (analysis stub). */
public abstract class XMLOutputFactory {
    public static final String IS_REPAIRING_NAMESPACES = "javax.xml.stream.isRepairingNamespaces";
    protected XMLOutputFactory() {}
    public static XMLOutputFactory newInstance() { return null; }
    public static XMLOutputFactory newFactory() { return null; }
    public static XMLOutputFactory newFactory(String factoryId, ClassLoader classLoader) { return null; }
    public abstract XMLStreamWriter createXMLStreamWriter(java.io.Writer stream);
    public abstract XMLStreamWriter createXMLStreamWriter(java.io.OutputStream stream);
    public abstract XMLStreamWriter createXMLStreamWriter(java.io.OutputStream stream, String encoding);
    public abstract XMLEventWriter createXMLEventWriter(java.io.Writer stream);
    public abstract XMLEventWriter createXMLEventWriter(java.io.OutputStream stream);
    public abstract XMLEventWriter createXMLEventWriter(java.io.OutputStream stream, String encoding);
    public abstract void setProperty(String name, Object value);
    public abstract Object getProperty(String name);
    public abstract boolean isPropertySupported(String name);
}
