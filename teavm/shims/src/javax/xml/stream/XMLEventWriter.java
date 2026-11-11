package javax.xml.stream;
/** Minimal javax.xml.stream.XMLEventWriter (analysis stub). */
public interface XMLEventWriter {
    void flush() throws XMLStreamException;
    void close() throws XMLStreamException;
    void add(javax.xml.stream.events.XMLEvent event) throws XMLStreamException;
    void add(javax.xml.stream.XMLEventReader reader) throws XMLStreamException;
    String getPrefix(String uri) throws XMLStreamException;
    void setPrefix(String prefix, String uri) throws XMLStreamException;
    void setDefaultNamespace(String uri) throws XMLStreamException;
    void setNamespaceContext(javax.xml.namespace.NamespaceContext context) throws XMLStreamException;
    javax.xml.namespace.NamespaceContext getNamespaceContext();
}
