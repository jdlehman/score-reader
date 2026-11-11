package javax.swing;
/** Minimal javax.swing.ListModel. */
public interface ListModel<E> {
    int getSize();
    E getElementAt(int index);
    void addListDataListener(javax.swing.event.ListDataListener l);
    void removeListDataListener(javax.swing.event.ListDataListener l);
}
