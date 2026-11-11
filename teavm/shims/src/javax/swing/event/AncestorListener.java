package javax.swing.event;
/** Minimal javax.swing.event.AncestorListener. */
public interface AncestorListener extends java.util.EventListener {
    void ancestorAdded(AncestorEvent event);
    void ancestorRemoved(AncestorEvent event);
    void ancestorMoved(AncestorEvent event);
}
