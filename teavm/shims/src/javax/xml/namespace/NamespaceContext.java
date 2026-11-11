package javax.xml.namespace;
/** Minimal javax.xml.namespace.NamespaceContext. */
public interface NamespaceContext {
    String getNamespaceURI(String prefix);
    String getPrefix(String namespaceURI);
    java.util.Iterator<String> getPrefixes(String namespaceURI);
}
