package javax.xml.stream;
/** Minimal javax.xml.stream.XMLStreamWriter (analysis stub). */
public interface XMLStreamWriter {
    void writeStartDocument() throws XMLStreamException;
    void writeStartDocument(String version) throws XMLStreamException;
    void writeStartDocument(String encoding, String version) throws XMLStreamException;
    void writeEndDocument() throws XMLStreamException;
    void close() throws XMLStreamException;
    void flush() throws XMLStreamException;
    void writeStartElement(String localName) throws XMLStreamException;
    void writeStartElement(String namespaceURI, String localName) throws XMLStreamException;
    void writeStartElement(String prefix, String localName, String namespaceURI) throws XMLStreamException;
    void writeEmptyElement(String localName) throws XMLStreamException;
    void writeEmptyElement(String namespaceURI, String localName) throws XMLStreamException;
    void writeEmptyElement(String prefix, String localName, String namespaceURI) throws XMLStreamException;
    void writeEndElement() throws XMLStreamException;
    void writeCharacters(String text) throws XMLStreamException;
    void writeCharacters(char[] text, int start, int len) throws XMLStreamException;
    void writeAttribute(String localName, String value) throws XMLStreamException;
    void writeAttribute(String prefix, String namespaceURI, String localName, String value) throws XMLStreamException;
    void writeAttribute(String namespaceURI, String localName, String value) throws XMLStreamException;
    void writeComment(String data) throws XMLStreamException;
    void writeProcessingInstruction(String target) throws XMLStreamException;
    void writeProcessingInstruction(String target, String data) throws XMLStreamException;
    void writeCData(String data) throws XMLStreamException;
    void writeDTD(String dtd) throws XMLStreamException;
    void writeEntityRef(String name) throws XMLStreamException;
    void writeNamespace(String prefix, String namespaceURI) throws XMLStreamException;
    void writeDefaultNamespace(String namespaceURI) throws XMLStreamException;
    String getPrefix(String uri) throws XMLStreamException;
    void setPrefix(String prefix, String uri) throws XMLStreamException;
    void setDefaultNamespace(String uri) throws XMLStreamException;
    void setNamespaceContext(javax.xml.namespace.NamespaceContext context) throws XMLStreamException;
    javax.xml.namespace.NamespaceContext getNamespaceContext();
    Object getProperty(String name);
}
