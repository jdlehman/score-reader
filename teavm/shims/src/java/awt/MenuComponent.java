package java.awt;
/** Minimal java.awt.MenuComponent. */
public abstract class MenuComponent {
    protected String name;
    protected Font font;
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public MenuContainer getParent() { return null; }
    public Font getFont() { return font; }
    public void setFont(Font f) { font = f; }
    public void dispatchEvent(java.awt.AWTEvent e) {}
    public void removeNotify() {}
}
