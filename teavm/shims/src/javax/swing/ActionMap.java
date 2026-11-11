package javax.swing;
/** Minimal javax.swing.ActionMap. */
public class ActionMap implements java.io.Serializable {
    public ActionMap() {}
    public void setParent(ActionMap map) {}
    public ActionMap getParent() { return null; }
    public void put(Object key, Action action) {}
    public Action get(Object key) { return null; }
    public void remove(Object key) {}
    public void clear() {}
    public Object[] keys() { return new Object[0]; }
    public int size() { return 0; }
    public Object[] allKeys() { return new Object[0]; }
}
