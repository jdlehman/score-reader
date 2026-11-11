package java.awt;
/** Minimal java.awt.MenuShortcut. */
public class MenuShortcut implements java.io.Serializable {
    protected int key;
    protected boolean useShift;
    public MenuShortcut(int key) { this.key = key; }
    public MenuShortcut(int key, boolean useShift) { this.key = key; this.useShift = useShift; }
    public int getKey() { return key; }
    public boolean usesShiftModifier() { return useShift; }
}
