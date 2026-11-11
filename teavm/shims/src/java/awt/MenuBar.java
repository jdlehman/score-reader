package java.awt;
/** Minimal java.awt.MenuBar. */
public class MenuBar extends MenuComponent implements MenuContainer {
    public MenuBar() {}
    public Menu add(Menu m) { return m; }
    public void remove(int index) {}
    public void remove(MenuComponent m) {}
    public int getMenuCount() { return 0; }
    public Menu getMenu(int i) { throw new ArrayIndexOutOfBoundsException(i); }
    public Menu getHelpMenu() { return null; }
    public void setHelpMenu(Menu m) {}
    public Font getFont() { return font; }
}
