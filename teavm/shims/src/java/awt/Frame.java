package java.awt;
/** Minimal java.awt.Frame. */
public class Frame extends Window {
    public static final int NORMAL = 0;
    public static final int ICONIFIED = 1;
    public static final int MAXIMIZED_HORIZ = 2;
    public static final int MAXIMIZED_VERT = 4;
    public static final int MAXIMIZED_BOTH = MAXIMIZED_HORIZ | MAXIMIZED_VERT;
    protected String title;
    protected boolean resizable = true;
    protected MenuBar menuBar;
    public Frame() {}
    public Frame(String title) { this.title = title; }
    public Frame(GraphicsConfiguration gc) {}
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public boolean isResizable() { return resizable; }
    public void setResizable(boolean b) { resizable = b; }
    public MenuBar getMenuBar() { return menuBar; }
    public void setMenuBar(MenuBar mb) { menuBar = mb; }
    public void remove(MenuComponent m) {}
    public int getState() { return NORMAL; }
    public void setState(int state) {}
    public int getExtendedState() { return NORMAL; }
    public void setExtendedState(int state) {}
    public void setUndecorated(boolean b) {}
    public boolean isUndecorated() { return false; }
    public void setMaximizedBounds(Rectangle bounds) {}
    public Rectangle getMaximizedBounds() { return null; }
}
