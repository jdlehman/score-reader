package javax.xml.stream.events;
/** Minimal javax.xml.stream.events.XMLEvent. */
public interface XMLEvent {
    int getEventType();
    boolean isStartElement();
    boolean isEndElement();
    boolean isCharacters();
}
