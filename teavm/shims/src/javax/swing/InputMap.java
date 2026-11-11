package javax.swing;
/** Minimal javax.swing.InputMap. */
public class InputMap implements java.io.Serializable {
    public static final int WHEN_FOCUSED = 0;
    public static final int WHEN_ANCESTOR_OF_FOCUSED_COMPONENT = 1;
    public static final int WHEN_IN_FOCUSED_WINDOW = 2;
    public InputMap() {}
    public void setParent(InputMap map) {}
    public InputMap getParent() { return null; }
    public void put(KeyStroke keyStroke, Object actionMapKey) {}
    public Object get(KeyStroke keyStroke) { return null; }
    public void remove(KeyStroke keyStroke) {}
    public void clear() {}
    public KeyStroke[] keys() { return new KeyStroke[0]; }
    public int size() { return 0; }
    public KeyStroke[] allKeys() { return new KeyStroke[0]; }
}
