package java.awt;
/** Minimal java.awt.Menu. */
public class Menu extends MenuItem implements MenuContainer {
    protected boolean tearOff;
    public Menu() {}
    public Menu(String label) { super(label); }
    public Menu(String label, boolean tearOff) { super(label); this.tearOff = tearOff; }
    public MenuItem add(MenuItem mi) { return mi; }
    public void add(String label) {}
    public void addSeparator() {}
    public void insert(MenuItem mi, int index) {}
    public void insert(String label, int index) {}
    public void insertSeparator(int index) {}
    public void remove(int index) {}
    public void remove(MenuComponent item) {}
    public void removeAll() {}
    public int getItemCount() { return 0; }
    public MenuItem getItem(int index) { throw new ArrayIndexOutOfBoundsException(index); }
    public boolean isTearOff() { return tearOff; }
    public int countItems() { return 0; }
    public Font getFont() { return font; }
}
