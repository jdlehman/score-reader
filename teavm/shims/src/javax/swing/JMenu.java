package javax.swing;
/** Minimal javax.swing.JMenu. */
public class JMenu extends JMenuItem {
    private final java.util.List<java.awt.Component> items = new java.util.ArrayList<>();
    public JMenu() {}
    public JMenu(String s) { super(s); }
    public JMenu(String s, boolean b) { super(s); }
    public javax.swing.JMenuItem add(javax.swing.JMenuItem menuItem) { items.add(menuItem); return menuItem; }
    public java.awt.Component add(java.awt.Component c) { items.add(c); return c; }
    public void addSeparator() {}
    public void insert(javax.swing.JMenuItem mi, int pos) { items.add(pos, mi); }
    public void insertSeparator(int index) {}
    public javax.swing.JMenuItem getItem(int pos) { java.awt.Component c = items.get(pos); return (c instanceof javax.swing.JMenuItem) ? (javax.swing.JMenuItem) c : null; }
    public int getItemCount() { return items.size(); }
    public void remove(javax.swing.JMenuItem item) { items.remove(item); }
    public void remove(int pos) { items.remove(pos); }
    public void removeAll() { items.clear(); }
    public boolean isTopLevelMenu() { return false; }
    public boolean isMenuComponent(java.awt.Component c) { return items.contains(c); }
    public void setPopupMenuVisible(boolean b) {}
    public boolean isPopupMenuVisible() { return false; }
    public void setDelay(int d) {}
    public int getDelay() { return 0; }
}
