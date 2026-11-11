package javax.swing;
/** Minimal javax.swing.AbstractListModel. */
public abstract class AbstractListModel<E> implements ListModel<E>, java.io.Serializable {
    protected javax.swing.event.EventListenerList listenerList = new javax.swing.event.EventListenerList();
    public void addListDataListener(javax.swing.event.ListDataListener l) { listenerList.add(javax.swing.event.ListDataListener.class, l); }
    public void removeListDataListener(javax.swing.event.ListDataListener l) { listenerList.remove(javax.swing.event.ListDataListener.class, l); }
    public javax.swing.event.ListDataListener[] getListDataListeners() { return listenerList.getListeners(javax.swing.event.ListDataListener.class); }
    protected void fireContentsChanged(Object source, int index0, int index1) {}
    protected void fireIntervalAdded(Object source, int index0, int index1) {}
    protected void fireIntervalRemoved(Object source, int index0, int index1) {}
}
