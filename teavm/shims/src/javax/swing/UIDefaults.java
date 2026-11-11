package javax.swing;
/** Minimal javax.swing.UIDefaults. */
public class UIDefaults extends java.util.Hashtable<Object, Object> {
    public Object get(Object key) { return super.get(key); }
    public Object put(Object key, Object value) { return super.put(key, value); }
    public void addResourceBundle(String bundleName) {}
    public void removeResourceBundle(String bundleName) {}
}
