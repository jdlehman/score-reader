package javax.swing;
/** Minimal javax.swing.JMenuBar. */
public class JMenuBar extends JComponent {
    private final java.util.List<javax.swing.JMenu> menus = new java.util.ArrayList<>();
    public javax.swing.JMenu add(javax.swing.JMenu c) { menus.add(c); return c; }
    public javax.swing.JMenu getMenu(int index) { return menus.get(index); }
    public int getMenuCount() { return menus.size(); }
}
