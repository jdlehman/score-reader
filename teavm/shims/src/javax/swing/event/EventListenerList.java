package javax.swing.event;
/** Minimal javax.swing.event.EventListenerList. */
public class EventListenerList implements java.io.Serializable {
    private final java.util.List<Object[]> listeners = new java.util.ArrayList<>();
    public <T extends java.util.EventListener> void add(Class<T> t, T l) { listeners.add(new Object[]{ t, l }); }
    public <T extends java.util.EventListener> void remove(Class<T> t, T l) { listeners.removeIf(e -> e[0] == t && e[1] == l); }
    public <T extends java.util.EventListener> T[] getListeners(Class<T> t) {
        java.util.List<T> out = new java.util.ArrayList<>();
        for (Object[] e : listeners) { if (e[0] == t) out.add(t.cast(e[1])); }
        @SuppressWarnings("unchecked") T[] arr = (T[]) out.toArray(new java.util.EventListener[0]);
        return arr;
    }
    public int getListenerCount() { return listeners.size(); }
    public int getListenerCount(Class<?> t) { int n = 0; for (Object[] e : listeners) { if (e[0] == t) n++; } return n; }
    public Object[] getListenerList() { java.util.List<Object> out = new java.util.ArrayList<>(); for (Object[] e : listeners) { out.add(e[0]); out.add(e[1]); } return out.toArray(); }
}
