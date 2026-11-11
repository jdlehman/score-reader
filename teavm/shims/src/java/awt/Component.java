package java.awt;
import java.awt.event.*;
import java.beans.PropertyChangeListener;
/** Minimal java.awt.Component (headless stub). */
public abstract class Component {
    protected Container parent;
    protected String name;
    protected boolean visible = true;
    protected boolean enabled = true;
    protected int x, y, width, height;
    protected Font font;
    protected Color background, foreground;
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Container getParent() { return parent; }
    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean b) { enabled = b; }
    public boolean isVisible() { return visible; }
    public void setVisible(boolean b) { visible = b; }
    public boolean isShowing() { return visible; }
    public boolean isDisplayable() { return false; }
    public void setSize(int w, int h) { width = w; height = h; }
    public void setSize(Dimension d) { width = d.width; height = d.height; }
    public Dimension getSize() { return new Dimension(width, height); }
    public int getWidth() { return width; }
    public int getHeight() { return height; }
    public void setBounds(int x, int y, int w, int h) { this.x = x; this.y = y; width = w; height = h; }
    public void setBounds(Rectangle r) { setBounds(r.x, r.y, r.width, r.height); }
    public Rectangle getBounds() { return new Rectangle(x, y, width, height); }
    public void setLocation(int x, int y) { this.x = x; this.y = y; }
    public void setLocation(Point p) { x = p.x; y = p.y; }
    public Point getLocation() { return new Point(x, y); }
    public int getX() { return x; }
    public int getY() { return y; }
    public void setPreferredSize(Dimension d) {}
    public Dimension getPreferredSize() { return new Dimension(width, height); }
    public void setMinimumSize(Dimension d) {}
    public Dimension getMinimumSize() { return new Dimension(0, 0); }
    public void setMaximumSize(Dimension d) {}
    public Dimension getMaximumSize() { return new Dimension(Integer.MAX_VALUE, Integer.MAX_VALUE); }
    public void setBackground(Color c) { background = c; }
    public Color getBackground() { return background; }
    public void setForeground(Color c) { foreground = c; }
    public Color getForeground() { return foreground; }
    public void setFont(Font f) { font = f; }
    public Font getFont() { return font; }
    public void setCursor(Cursor c) {}
    public Cursor getCursor() { return null; }
    public void setFocusable(boolean b) {}
    public boolean isFocusable() { return false; }
    public boolean requestFocus() { return false; }
    public boolean requestFocusInWindow() { return false; }
    public boolean isFocusOwner() { return false; }
    public void repaint() {}
    public void repaint(int x, int y, int w, int h) {}
    public void repaint(long tm) {}
    public void validate() {}
    public void invalidate() {}
    public Graphics getGraphics() { return null; }
    public GraphicsConfiguration getGraphicsConfiguration() { return null; }
    public java.awt.Toolkit getToolkit() { return null; }
    public void show() { visible = true; }
    public void hide() { visible = false; }
    public void addMouseListener(MouseListener l) {}
    public void removeMouseListener(MouseListener l) {}
    public void addMouseMotionListener(MouseMotionListener l) {}
    public void removeMouseMotionListener(MouseMotionListener l) {}
    public void addMouseWheelListener(MouseWheelListener l) {}
    public void removeMouseWheelListener(MouseWheelListener l) {}
    public void addKeyListener(KeyListener l) {}
    public void removeKeyListener(KeyListener l) {}
    public void addFocusListener(FocusListener l) {}
    public void removeFocusListener(FocusListener l) {}
    public void addComponentListener(ComponentListener l) {}
    public void removeComponentListener(ComponentListener l) {}
    public void addPropertyChangeListener(PropertyChangeListener l) {}
    public void removePropertyChangeListener(PropertyChangeListener l) {}
    public void addPropertyChangeListener(String name, PropertyChangeListener l) {}
    public void removePropertyChangeListener(String name, PropertyChangeListener l) {}
    public void firePropertyChange(String name, Object oldV, Object newV) {}
    public boolean contains(int x, int y) { return false; }
    public boolean contains(Point p) { return false; }
    public Object getTreeLock() { return this; }
    public void addNotify() {}
    public void removeNotify() {}
    public void setLocale(java.util.Locale l) {}
    public java.util.Locale getLocale() { return java.util.Locale.getDefault(); }
    public void setDropTarget(java.awt.dnd.DropTarget dt) {}
    public java.awt.dnd.DropTarget getDropTarget() { return null; }
    public void setFocusTraversalKeysEnabled(boolean b) {}
    public boolean isFocusTraversalKeysEnabled() { return false; }
    protected void enableEvents(long eventsToEnable) {}
    public void setFocusTraversalKeys(int id, java.util.Set<? extends java.awt.AWTKeyStroke> keys) {}
    public java.util.Set<java.awt.AWTKeyStroke> getFocusTraversalKeys(int id) { return new java.util.HashSet<>(); }
    public boolean isValid() { return true; }
    public boolean prepareImage(Image image, java.awt.image.ImageObserver observer) { return true; }
    public boolean prepareImage(Image image, int width, int height, java.awt.image.ImageObserver observer) { return true; }
    public Image createImage(int width, int height) { return null; }
    public Image createImage(java.awt.image.ImageProducer producer) { return null; }
    public java.awt.FontMetrics getFontMetrics() { return new java.awt.FontMetrics(font); }
    public java.awt.FontMetrics getFontMetrics(Font f) { return new java.awt.FontMetrics(f); }
    public void add(java.awt.PopupMenu popup) {}
    public void remove(java.awt.MenuComponent popup) {}
}
