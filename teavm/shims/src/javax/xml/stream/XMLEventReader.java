package javax.xml.stream;
/** Minimal javax.xml.stream.XMLEventReader. */
public interface XMLEventReader extends java.util.Iterator<javax.xml.stream.events.XMLEvent> {
    javax.xml.stream.events.XMLEvent nextEvent() throws XMLStreamException;
    boolean hasNext();
    javax.xml.stream.events.XMLEvent peek() throws XMLStreamException;
    String getElementText() throws XMLStreamException;
    javax.xml.stream.events.XMLEvent nextTag() throws XMLStreamException;
    Object getProperty(String name);
    void close() throws XMLStreamException;
}
