package javax.swing.event;
/** Minimal javax.swing.event.DocumentEvent. */
public interface DocumentEvent {
    int getOffset();
    int getLength();
    javax.swing.text.Document getDocument();
    EventType getType();
    ElementChange getChange(javax.swing.text.Element elem);
    enum EventType { INSERT, REMOVE, CHANGE }
    interface ElementChange {
        javax.swing.text.Element getElement();
        int getIndex();
        javax.swing.text.Element[] getChildrenRemoved();
        javax.swing.text.Element[] getChildrenAdded();
    }
}
