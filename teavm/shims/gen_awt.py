#!/usr/bin/env python3
"""Generate headless java.awt / java.awt.event / javax.swing.event stubs.

These exist only so TeaVM can COMPILE GUI code it never runs (ij's
ImageWindow/StackWindow/ImageCanvas, ij.ImageJ, and the gutted
StubsController). All methods are no-ops / return null or 0.
Run from teavm/ :  python3 shims/gen_awt.py
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")

FILES = {}

FILES["java/awt/Component.java"] = """package java.awt;
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
"""

FILES["java/awt/Container.java"] = """package java.awt;
import java.awt.event.*;
/** Minimal java.awt.Container. */
public class Container extends Component {
    public Component[] getComponents() { return new Component[0]; }
    public Component add(Component c) { if (c != null) c.parent = this; return c; }
    public Component add(Component c, int index) { return add(c); }
    public void add(Component c, Object constraints) { add(c); }
    public void add(Component c, Object constraints, int index) { add(c); }
    public void remove(Component c) {}
    public void remove(int index) {}
    public void removeAll() {}
    public int getComponentCount() { return 0; }
    public Component getComponent(int i) { throw new ArrayIndexOutOfBoundsException(i); }
    public Insets getInsets() { return new Insets(0, 0, 0, 0); }
    public void setLayout(LayoutManager lm) {}
    public LayoutManager getLayout() { return null; }
    public void addContainerListener(ContainerListener l) {}
    public void removeContainerListener(ContainerListener l) {}
    public Component add(String name, Component comp) { return add(comp); }
    public void validate() {}
    public void invalidate() {}
    public void doLayout() {}
    public void setFont(Font f) { super.setFont(f); }
}
"""

FILES["java/awt/Window.java"] = """package java.awt;
import java.awt.event.*;
/** Minimal java.awt.Window. */
public class Window extends Container {
    public Window() {}
    public Window(Frame owner) {}
    public Window(Window owner) {}
    public Window(GraphicsConfiguration gc) {}
    public void pack() {}
    public void dispose() {}
    public void toFront() {}
    public void toBack() {}
    public void setAlwaysOnTop(boolean b) {}
    public boolean isAlwaysOnTop() { return false; }
    public void setLocationRelativeTo(Component c) {}
    public Window getOwner() { return null; }
    public void addWindowListener(WindowListener l) {}
    public void removeWindowListener(WindowListener l) {}
    public WindowListener[] getWindowListeners() { return new WindowListener[0]; }
    public void addWindowStateListener(WindowStateListener l) {}
    public void removeWindowStateListener(WindowStateListener l) {}
    public void addWindowFocusListener(WindowFocusListener l) {}
    public void removeWindowFocusListener(WindowFocusListener l) {}
    public void setIconImage(Image image) {}
    public Image getIconImage() { return null; }
    public void setMinimumSize(Dimension d) {}
}
"""

FILES["java/awt/Frame.java"] = """package java.awt;
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
"""

FILES["java/awt/Dialog.java"] = """package java.awt;
/** Minimal java.awt.Dialog. */
public class Dialog extends Window {
    public static final int DEFAULT_MODALITY_TYPE = 0;
    protected String title;
    protected boolean modal;
    protected boolean resizable = true;
    public Dialog() {}
    public Dialog(Frame owner) {}
    public Dialog(Frame owner, String title) { this.title = title; }
    public Dialog(Frame owner, boolean modal) { this.modal = modal; }
    public Dialog(Frame owner, String title, boolean modal) { this.title = title; this.modal = modal; }
    public Dialog(Dialog owner) {}
    public Dialog(Dialog owner, String title) { this.title = title; }
    public Dialog(Window owner) {}
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public boolean isModal() { return modal; }
    public void setModal(boolean b) { modal = b; }
    public boolean isResizable() { return resizable; }
    public void setResizable(boolean b) { resizable = b; }
    public void setUndecorated(boolean b) {}
    public boolean isUndecorated() { return false; }
}
"""

FILES["java/awt/Canvas.java"] = """package java.awt;
/** Minimal java.awt.Canvas. */
public class Canvas extends Component {
    public Canvas() {}
    public Canvas(GraphicsConfiguration gc) {}
}
"""

FILES["java/awt/Panel.java"] = """package java.awt;
/** Minimal java.awt.Panel. */
public class Panel extends Container {
    public Panel() {}
    public Panel(LayoutManager layout) { setLayout(layout); }
}
"""

FILES["java/awt/Scrollbar.java"] = """package java.awt;
import java.awt.event.*;
/** Minimal java.awt.Scrollbar. */
public class Scrollbar extends Component implements Adjustable {
    public static final int HORIZONTAL = 0;
    public static final int VERTICAL = 1;
    protected int value, minimum, maximum, visibleAmount, orientation;
    protected int unitIncrement = 1, blockIncrement = 10;
    public Scrollbar() { this(VERTICAL, 0, 10, 0, 100); }
    public Scrollbar(int orientation) { this(orientation, 0, 10, 0, 100); }
    public Scrollbar(int orientation, int value, int visible, int minimum, int maximum) {
        this.orientation = orientation; this.value = value; this.visibleAmount = visible;
        this.minimum = minimum; this.maximum = maximum;
    }
    public int getOrientation() { return orientation; }
    public void setOrientation(int o) { orientation = o; }
    public int getValue() { return value; }
    public void setValue(int v) { value = v; }
    public int getMinimum() { return minimum; }
    public void setMinimum(int m) { minimum = m; }
    public int getMaximum() { return maximum; }
    public void setMaximum(int m) { maximum = m; }
    public int getVisibleAmount() { return visibleAmount; }
    public void setVisibleAmount(int v) { visibleAmount = v; }
    public int getUnitIncrement() { return unitIncrement; }
    public void setUnitIncrement(int u) { unitIncrement = u; }
    public int getBlockIncrement() { return blockIncrement; }
    public void setBlockIncrement(int b) { blockIncrement = b; }
    public void addAdjustmentListener(AdjustmentListener l) {}
    public void removeAdjustmentListener(AdjustmentListener l) {}
    public AdjustmentListener[] getAdjustmentListeners() { return new AdjustmentListener[0]; }
    public void setValues(int value, int visible, int minimum, int maximum) {
        this.value = value; visibleAmount = visible; this.minimum = minimum; this.maximum = maximum;
    }
}
"""

FILES["java/awt/MenuComponent.java"] = """package java.awt;
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
"""

FILES["java/awt/MenuContainer.java"] = """package java.awt;
/** Minimal java.awt.MenuContainer. */
public interface MenuContainer {
    Font getFont();
    void remove(MenuComponent comp);
}
"""

FILES["java/awt/MenuItem.java"] = """package java.awt;
import java.awt.event.*;
/** Minimal java.awt.MenuItem. */
public class MenuItem extends MenuComponent implements java.io.Serializable {
    protected String label;
    protected boolean enabled = true;
    protected String actionCommand;
    public MenuItem() {}
    public MenuItem(String label) { this.label = label; }
    public MenuItem(String label, MenuShortcut s) { this.label = label; }
    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean b) { enabled = b; }
    public String getActionCommand() { return actionCommand; }
    public void setActionCommand(String cmd) { actionCommand = cmd; }
    public void addActionListener(ActionListener l) {}
    public void removeActionListener(ActionListener l) {}
    public ActionListener[] getActionListeners() { return new ActionListener[0]; }
    public void setShortcut(MenuShortcut s) {}
    public MenuShortcut getShortcut() { return null; }
    public void deleteShortcut() {}
}
"""

FILES["java/awt/Menu.java"] = """package java.awt;
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
"""

FILES["java/awt/MenuBar.java"] = """package java.awt;
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
"""

FILES["java/awt/CheckboxMenuItem.java"] = """package java.awt;
import java.awt.event.*;
/** Minimal java.awt.CheckboxMenuItem. */
public class CheckboxMenuItem extends MenuItem implements ItemSelectable {
    protected boolean state;
    public CheckboxMenuItem() {}
    public CheckboxMenuItem(String label) { super(label); }
    public CheckboxMenuItem(String label, boolean state) { super(label); this.state = state; }
    public boolean getState() { return state; }
    public void setState(boolean state) { this.state = state; }
    public Object[] getSelectedObjects() { return state ? new Object[]{label} : new Object[0]; }
    public void addItemListener(ItemListener l) {}
    public void removeItemListener(ItemListener l) {}
    public ItemListener[] getItemListeners() { return new ItemListener[0]; }
}
"""

FILES["java/awt/PopupMenu.java"] = """package java.awt;
/** Minimal java.awt.PopupMenu. */
public class PopupMenu extends Menu {
    public PopupMenu() {}
    public PopupMenu(String label) { super(label); }
    public void show(Component origin, int x, int y) {}
}
"""

FILES["java/awt/MenuShortcut.java"] = """package java.awt;
/** Minimal java.awt.MenuShortcut. */
public class MenuShortcut implements java.io.Serializable {
    protected int key;
    protected boolean useShift;
    public MenuShortcut(int key) { this.key = key; }
    public MenuShortcut(int key, boolean useShift) { this.key = key; this.useShift = useShift; }
    public int getKey() { return key; }
    public boolean usesShiftModifier() { return useShift; }
}
"""

FILES["java/awt/LayoutManager.java"] = """package java.awt;
/** Minimal java.awt.LayoutManager. */
public interface LayoutManager {
    void addLayoutComponent(String name, Component comp);
    void removeLayoutComponent(Component comp);
    Dimension preferredLayoutSize(Container parent);
    Dimension minimumLayoutSize(Container parent);
    void layoutContainer(Container parent);
}
"""

FILES["java/awt/LayoutManager2.java"] = """package java.awt;
/** Minimal java.awt.LayoutManager2. */
public interface LayoutManager2 extends LayoutManager {
    void addLayoutComponent(Component comp, Object constraints);
    Dimension maximumLayoutSize(Container target);
    float getLayoutAlignmentX(Container target);
    float getLayoutAlignmentY(Container target);
    void invalidateLayout(Container target);
}
"""

FILES["java/awt/BorderLayout.java"] = """package java.awt;
/** Minimal java.awt.BorderLayout. */
public class BorderLayout implements LayoutManager2, java.io.Serializable {
    public static final String NORTH = "North";
    public static final String SOUTH = "South";
    public static final String EAST = "East";
    public static final String WEST = "West";
    public static final String CENTER = "Center";
    public static final String BEFORE_FIRST_LINE = "First";
    public static final String AFTER_LAST_LINE = "Last";
    public static final String BEFORE_LINE_BEGINS = "Before";
    public static final String AFTER_LINE_ENDS = "After";
    public static final String PAGE_START = BEFORE_FIRST_LINE;
    public static final String PAGE_END = AFTER_LAST_LINE;
    public static final String LINE_START = BEFORE_LINE_BEGINS;
    public static final String LINE_END = AFTER_LINE_ENDS;
    protected int hgap, vgap;
    public BorderLayout() {}
    public BorderLayout(int hgap, int vgap) { this.hgap = hgap; this.vgap = vgap; }
    public int getHgap() { return hgap; }
    public void setHgap(int hgap) { this.hgap = hgap; }
    public int getVgap() { return vgap; }
    public void setVgap(int vgap) { this.vgap = vgap; }
    public void addLayoutComponent(Component comp, Object constraints) {}
    public void addLayoutComponent(String name, Component comp) {}
    public void removeLayoutComponent(Component comp) {}
    public Dimension preferredLayoutSize(Container parent) { return new Dimension(0, 0); }
    public Dimension minimumLayoutSize(Container parent) { return new Dimension(0, 0); }
    public Dimension maximumLayoutSize(Container target) { return new Dimension(Integer.MAX_VALUE, Integer.MAX_VALUE); }
    public float getLayoutAlignmentX(Container target) { return 0.5f; }
    public float getLayoutAlignmentY(Container target) { return 0.5f; }
    public void invalidateLayout(Container target) {}
    public void layoutContainer(Container parent) {}
    public String getConstraints(Component comp) { return CENTER; }
}
"""

FILES["java/awt/FlowLayout.java"] = """package java.awt;
/** Minimal java.awt.FlowLayout. */
public class FlowLayout implements LayoutManager, java.io.Serializable {
    public static final int LEFT = 0;
    public static final int CENTER = 1;
    public static final int RIGHT = 2;
    public static final int LEADING = 3;
    public static final int TRAILING = 4;
    protected int align = CENTER, hgap = 5, vgap = 5;
    protected boolean alignOnBaseline;
    public FlowLayout() {}
    public FlowLayout(int align) { this.align = align; }
    public FlowLayout(int align, int hgap, int vgap) { this.align = align; this.hgap = hgap; this.vgap = vgap; }
    public int getAlignment() { return align; }
    public void setAlignment(int align) { this.align = align; }
    public int getHgap() { return hgap; }
    public void setHgap(int hgap) { this.hgap = hgap; }
    public int getVgap() { return vgap; }
    public void setVgap(int vgap) { this.vgap = vgap; }
    public void addLayoutComponent(String name, Component comp) {}
    public void removeLayoutComponent(Component comp) {}
    public Dimension preferredLayoutSize(Container parent) { return new Dimension(0, 0); }
    public Dimension minimumLayoutSize(Container parent) { return new Dimension(0, 0); }
    public void layoutContainer(Container parent) {}
}
"""

FILES["java/awt/GridLayout.java"] = """package java.awt;
/** Minimal java.awt.GridLayout. */
public class GridLayout implements LayoutManager, java.io.Serializable {
    protected int rows, cols, hgap, vgap;
    public GridLayout() { this(1, 0, 0, 0); }
    public GridLayout(int rows, int cols) { this(rows, cols, 0, 0); }
    public GridLayout(int rows, int cols, int hgap, int vgap) {
        this.rows = rows; this.cols = cols; this.hgap = hgap; this.vgap = vgap;
    }
    public int getRows() { return rows; }
    public void setRows(int rows) { this.rows = rows; }
    public int getColumns() { return cols; }
    public void setColumns(int cols) { this.cols = cols; }
    public int getHgap() { return hgap; }
    public void setHgap(int hgap) { this.hgap = hgap; }
    public int getVgap() { return vgap; }
    public void setVgap(int vgap) { this.vgap = vgap; }
    public void addLayoutComponent(String name, Component comp) {}
    public void removeLayoutComponent(Component comp) {}
    public Dimension preferredLayoutSize(Container parent) { return new Dimension(0, 0); }
    public Dimension minimumLayoutSize(Container parent) { return new Dimension(0, 0); }
    public void layoutContainer(Container parent) {}
}
"""

FILES["java/awt/EventQueue.java"] = """package java.awt;
/** Minimal java.awt.EventQueue. */
public class EventQueue {
    public static void invokeLater(Runnable r) { r.run(); }
    public static void invokeAndWait(Runnable r) throws InterruptedException, java.lang.reflect.InvocationTargetException { r.run(); }
    public static boolean isDispatchThread() { return false; }
    public static AWTEvent getCurrentEvent() { return null; }
    public static long getMostRecentEventTime() { return 0; }
    public void postEvent(AWTEvent e) {}
    public AWTEvent getNextEvent() throws InterruptedException { throw new InterruptedException(); }
    public AWTEvent peekEvent() { return null; }
    public void push(EventQueue q) {}
    protected void pop() {}
}
"""

FILES["java/awt/AWTEvent.java"] = """package java.awt;
import java.util.EventObject;
/** Minimal java.awt.AWTEvent. */
public class AWTEvent extends EventObject {
    public static final long COMPONENT_EVENT_MASK = 0x01;
    public static final long CONTAINER_EVENT_MASK = 0x02;
    public static final long FOCUS_EVENT_MASK = 0x04;
    public static final long KEY_EVENT_MASK = 0x08;
    public static final long MOUSE_EVENT_MASK = 0x10;
    public static final long MOUSE_MOTION_EVENT_MASK = 0x20;
    public static final long WINDOW_EVENT_MASK = 0x40;
    public static final long ACTION_EVENT_MASK = 0x80;
    public static final long ADJUSTMENT_EVENT_MASK = 0x100;
    public static final long ITEM_EVENT_MASK = 0x200;
    public static final long TEXT_EVENT_MASK = 0x400;
    public static final long RESERVED_ID_MAX = 1999;
    protected int id;
    protected boolean consumed;
    public AWTEvent(Object source, int id) { super(source); this.id = id; }
    public int getID() { return id; }
    public void setSource(Object source) { this.source = source; }
    public boolean isConsumed() { return consumed; }
    public void consume() { consumed = true; }
    protected void consumeImpl() {}
}
"""

FILES["java/awt/AWTEventMulticaster.java"] = """package java.awt;
import java.awt.event.*;
import java.util.EventListener;
/** Minimal java.awt.AWTEventMulticaster. */
public class AWTEventMulticaster implements ComponentListener, ContainerListener, FocusListener,
        KeyListener, MouseListener, MouseMotionListener, MouseWheelListener, WindowListener,
        WindowStateListener, WindowFocusListener, ActionListener, ItemListener, AdjustmentListener {
    protected final EventListener a, b;
    protected AWTEventMulticaster(EventListener a, EventListener b) { this.a = a; this.b = b; }
    protected static EventListener addInternal(EventListener a, EventListener b) { return a == null ? b : (b == null ? a : null); }
    protected static EventListener removeInternal(EventListener l, EventListener oldl) { return l == oldl ? null : l; }
    public static ComponentListener add(ComponentListener a, ComponentListener b) { return a == null ? b : b; }
    public static ComponentListener remove(ComponentListener l, ComponentListener oldl) { return l == oldl ? null : l; }
    public static ActionListener add(ActionListener a, ActionListener b) { return a == null ? b : b; }
    public static ActionListener remove(ActionListener l, ActionListener oldl) { return l == oldl ? null : l; }
    public static MouseListener add(MouseListener a, MouseListener b) { return a == null ? b : b; }
    public static MouseListener remove(MouseListener l, MouseListener oldl) { return l == oldl ? null : l; }
    public static MouseMotionListener add(MouseMotionListener a, MouseMotionListener b) { return a == null ? b : b; }
    public static MouseMotionListener remove(MouseMotionListener l, MouseMotionListener oldl) { return l == oldl ? null : l; }
    public static KeyListener add(KeyListener a, KeyListener b) { return a == null ? b : b; }
    public static KeyListener remove(KeyListener l, KeyListener oldl) { return l == oldl ? null : l; }
    public static FocusListener add(FocusListener a, FocusListener b) { return a == null ? b : b; }
    public static FocusListener remove(FocusListener l, FocusListener oldl) { return l == oldl ? null : l; }
    public static WindowListener add(WindowListener a, WindowListener b) { return a == null ? b : b; }
    public static WindowListener remove(WindowListener l, WindowListener oldl) { return l == oldl ? null : l; }
    public static ItemListener add(ItemListener a, ItemListener b) { return a == null ? b : b; }
    public static ItemListener remove(ItemListener l, ItemListener oldl) { return l == oldl ? null : l; }
    public static AdjustmentListener add(AdjustmentListener a, AdjustmentListener b) { return a == null ? b : b; }
    public static AdjustmentListener remove(AdjustmentListener l, AdjustmentListener oldl) { return l == oldl ? null : l; }
    public void componentResized(ComponentEvent e) {}
    public void componentMoved(ComponentEvent e) {}
    public void componentShown(ComponentEvent e) {}
    public void componentHidden(ComponentEvent e) {}
    public void componentAdded(ContainerEvent e) {}
    public void componentRemoved(ContainerEvent e) {}
    public void focusGained(FocusEvent e) {}
    public void focusLost(FocusEvent e) {}
    public void keyTyped(KeyEvent e) {}
    public void keyPressed(KeyEvent e) {}
    public void keyReleased(KeyEvent e) {}
    public void mouseClicked(MouseEvent e) {}
    public void mousePressed(MouseEvent e) {}
    public void mouseReleased(MouseEvent e) {}
    public void mouseEntered(MouseEvent e) {}
    public void mouseExited(MouseEvent e) {}
    public void mouseDragged(MouseEvent e) {}
    public void mouseMoved(MouseEvent e) {}
    public void mouseWheelMoved(MouseWheelEvent e) {}
    public void windowOpened(WindowEvent e) {}
    public void windowClosing(WindowEvent e) {}
    public void windowClosed(WindowEvent e) {}
    public void windowIconified(WindowEvent e) {}
    public void windowDeiconified(WindowEvent e) {}
    public void windowActivated(WindowEvent e) {}
    public void windowDeactivated(WindowEvent e) {}
    public void windowStateChanged(WindowEvent e) {}
    public void windowGainedFocus(WindowEvent e) {}
    public void windowLostFocus(WindowEvent e) {}
    public void actionPerformed(ActionEvent e) {}
    public void itemStateChanged(ItemEvent e) {}
    public void adjustmentValueChanged(AdjustmentEvent e) {}
}
"""

FILES["java/awt/Adjustable.java"] = """package java.awt;
/** Minimal java.awt.Adjustable. */
public interface Adjustable {
    int HORIZONTAL = 0;
    int VERTICAL = 1;
    int getOrientation();
    void setMinimum(int min);
    int getMinimum();
    void setMaximum(int max);
    int getMaximum();
    void setUnitIncrement(int u);
    int getUnitIncrement();
    void setBlockIncrement(int b);
    int getBlockIncrement();
    void setVisibleAmount(int v);
    int getVisibleAmount();
    void setValue(int v);
    int getValue();
    void addAdjustmentListener(java.awt.event.AdjustmentListener l);
    void removeAdjustmentListener(java.awt.event.AdjustmentListener l);
}
"""

FILES["java/awt/ContainerEvent.java"] = """package java.awt;
import java.awt.event.ComponentEvent;
/** Minimal java.awt.ContainerEvent. */
public class ContainerEvent extends ComponentEvent {
    public static final int CONTAINER_FIRST = 300;
    public static final int CONTAINER_LAST = 301;
    public static final int COMPONENT_ADDED = CONTAINER_FIRST;
    public static final int COMPONENT_REMOVED = 1 + CONTAINER_FIRST;
    protected Component child;
    public ContainerEvent(Component source, int id, Component child) { super(source, id); this.child = child; }
    public Component getChild() { return child; }
    public Container getContainer() { return (Container) getSource(); }
}
"""

FILES["java/awt/ContainerListener.java"] = """package java.awt;
/** Minimal java.awt.ContainerListener. */
public interface ContainerListener extends java.util.EventListener {
    void componentAdded(ContainerEvent e);
    void componentRemoved(ContainerEvent e);
}
"""

FILES["java/awt/ItemSelectable.java"] = """package java.awt;
/** Minimal java.awt.ItemSelectable. */
public interface ItemSelectable {
    Object[] getSelectedObjects();
    void addItemListener(java.awt.event.ItemListener l);
    void removeItemListener(java.awt.event.ItemListener l);
}
"""

FILES["java/awt/Cursor.java"] = """package java.awt;
/** Minimal java.awt.Cursor. */
public class Cursor implements java.io.Serializable {
    public static final int DEFAULT_CURSOR = 0;
    public static final int CROSSHAIR_CURSOR = 1;
    public static final int TEXT_CURSOR = 2;
    public static final int WAIT_CURSOR = 3;
    public static final int SW_RESIZE_CURSOR = 4;
    public static final int SE_RESIZE_CURSOR = 5;
    public static final int NW_RESIZE_CURSOR = 6;
    public static final int NE_RESIZE_CURSOR = 7;
    public static final int N_RESIZE_CURSOR = 8;
    public static final int S_RESIZE_CURSOR = 9;
    public static final int W_RESIZE_CURSOR = 10;
    public static final int E_RESIZE_CURSOR = 11;
    public static final int HAND_CURSOR = 12;
    public static final int MOVE_CURSOR = 13;
    protected int type;
    protected String name;
    public Cursor(int type) { this.type = type; }
    public int getType() { return type; }
    public String getName() { return "cursor" + type; }
    public static Cursor getDefaultCursor() { return new Cursor(DEFAULT_CURSOR); }
    public static Cursor getPredefinedCursor(int type) { return new Cursor(type); }
    public static Cursor getSystemCustomCursor(String name) { return null; }
}
"""

FILES["java/awt/image/DirectColorModel.java"] = """package java.awt.image;
/** Minimal java.awt.image.DirectColorModel. */
public class DirectColorModel extends ColorModel {
    protected int redMask, greenMask, blueMask, alphaMask;
    public DirectColorModel(int bits, int rmask, int gmask, int bmask) {
        this(bits, rmask, gmask, bmask, 0);
    }
    public DirectColorModel(int bits, int rmask, int gmask, int bmask, int amask) {
        super(bits);
        redMask = rmask; greenMask = gmask; blueMask = bmask; alphaMask = amask;
    }
    public int getRedMask() { return redMask; }
    public int getGreenMask() { return greenMask; }
    public int getBlueMask() { return blueMask; }
    public int getAlphaMask() { return alphaMask; }
    @Override public int getRed(int pixel) { return 0; }
    @Override public int getGreen(int pixel) { return 0; }
    @Override public int getBlue(int pixel) { return 0; }
    @Override public int getAlpha(int pixel) { return 255; }
    @Override public int getRGB(int pixel) { return pixel; }
}
"""

FILES["java/awt/image/PixelGrabber.java"] = """package java.awt.image;
import java.awt.Image;
/** Minimal java.awt.image.PixelGrabber. */
public class PixelGrabber implements ImageConsumer {
    protected Image image;
    protected int dstX, dstY, width, height;
    protected int[] pixels;
    protected boolean grabbing;
    public PixelGrabber(Image img, int x, int y, int w, int h, int[] pix, int off, int scansize) {
        image = img; dstX = x; dstY = y; width = w; height = h; pixels = pix;
    }
    public PixelGrabber(java.awt.image.ImageProducer ip, int x, int y, int w, int h, int[] pix, int off, int scansize) {
        dstX = x; dstY = y; width = w; height = h; pixels = pix;
    }
    public PixelGrabber(Image img, int x, int y, int w, int h, boolean grabPixels) {
        image = img; dstX = x; dstY = y; width = w; height = h;
    }
    public synchronized ColorModel getColorModel() { return null; }
    public synchronized boolean grabPixels() throws InterruptedException { return false; }
    public synchronized boolean grabPixels(long ms) throws InterruptedException { return false; }
    public synchronized int getStatus() { return 0; }
    public synchronized int getWidth() { return width; }
    public synchronized int getHeight() { return height; }
    public synchronized Object getPixels() { return pixels; }
    public synchronized int getPixel(int x, int y) { return 0; }
    public synchronized void abortGrabbing() {}
    public synchronized void startGrabbing() {}
    public void setDimensions(int width, int height) {}
    public void setProperties(java.util.Hashtable<?, ?> props) {}
    public void setColorModel(ColorModel model) {}
    public void setHints(int hintflags) {}
    public void setPixels(int x, int y, int w, int h, ColorModel model, byte[] pixels, int off, int scansize) {}
    public void setPixels(int x, int y, int w, int h, ColorModel model, int[] pixels, int off, int scansize) {}
    public void imageComplete(int status) {}
}
"""

FILES["java/awt/AlphaComposite.java"] = """package java.awt;
/** Minimal java.awt.AlphaComposite. */
public final class AlphaComposite implements Composite {
    public static final int CLEAR = 1;
    public static final int SRC = 2;
    public static final int DST = 9;
    public static final int SRC_OVER = 3;
    public static final int DST_OVER = 4;
    public static final int SRC_IN = 5;
    public static final int DST_IN = 6;
    public static final int SRC_OUT = 7;
    public static final int DST_OUT = 8;
    public static final int SRC_ATOP = 10;
    public static final int DST_ATOP = 11;
    public static final int XOR = 12;
    public static final AlphaComposite Clear = new AlphaComposite(CLEAR, 1.0f);
    public static final AlphaComposite Src = new AlphaComposite(SRC, 1.0f);
    public static final AlphaComposite SrcOver = new AlphaComposite(SRC_OVER, 1.0f);
    public static final AlphaComposite DstOver = new AlphaComposite(DST_OVER, 1.0f);
    protected int rule;
    protected float alpha;
    protected AlphaComposite(int rule, float alpha) { this.rule = rule; this.alpha = alpha; }
    public static AlphaComposite getInstance(int rule) { return new AlphaComposite(rule, 1.0f); }
    public static AlphaComposite getInstance(int rule, float alpha) { return new AlphaComposite(rule, alpha); }
    public int getRule() { return rule; }
    public float getAlpha() { return alpha; }
    public CompositeContext createContext(java.awt.image.ColorModel srcColorModel, java.awt.image.ColorModel dstColorModel, RenderingHints hints) { return null; }
    public int hashCode() { return rule * 31 + Float.floatToIntBits(alpha); }
    public boolean equals(Object obj) { return obj instanceof AlphaComposite && ((AlphaComposite) obj).rule == rule && ((AlphaComposite) obj).alpha == alpha; }
}
"""

# ---- java.awt.event ----
EV = "java/awt/event/"
FILES[EV + "InputEvent.java"] = """package java.awt.event;
import java.awt.Component;
/** Minimal java.awt.event.InputEvent. */
public abstract class InputEvent extends java.awt.AWTEvent {
    public static final int SHIFT_MASK = 1;
    public static final int CTRL_MASK = 2;
    public static final int META_MASK = 4;
    public static final int ALT_MASK = 8;
    public static final int ALT_GRAPH_MASK = 32;
    public static final int BUTTON1_MASK = 16;
    public static final int BUTTON2_MASK = 8;
    public static final int BUTTON3_MASK = 4;
    public static final int SHIFT_DOWN_MASK = 64;
    public static final int CTRL_DOWN_MASK = 128;
    public static final int META_DOWN_MASK = 256;
    public static final int ALT_DOWN_MASK = 512;
    public static final int BUTTON1_DOWN_MASK = 1024;
    public static final int BUTTON2_DOWN_MASK = 2048;
    public static final int BUTTON3_DOWN_MASK = 4096;
    protected long when;
    protected int modifiers;
    public InputEvent(Component source, int id, long when, int modifiers) { super(source, id); this.when = when; this.modifiers = modifiers; }
    public boolean isShiftDown() { return (modifiers & SHIFT_DOWN_MASK) != 0; }
    public boolean isControlDown() { return (modifiers & CTRL_DOWN_MASK) != 0; }
    public boolean isMetaDown() { return (modifiers & META_DOWN_MASK) != 0; }
    public boolean isAltDown() { return (modifiers & ALT_DOWN_MASK) != 0; }
    public boolean isAltGraphDown() { return (modifiers & ALT_GRAPH_MASK) != 0; }
    public long getWhen() { return when; }
    public int getModifiers() { return modifiers; }
    public int getModifiersEx() { return modifiers; }
    public void consume() { consumed = true; }
    public boolean isConsumed() { return consumed; }
}
"""

FILES[EV + "ActionEvent.java"] = """package java.awt.event;
/** Minimal java.awt.event.ActionEvent. */
public class ActionEvent extends java.awt.AWTEvent {
    public static final int SHIFT_MASK = 1;
    public static final int CTRL_MASK = 2;
    public static final int META_MASK = 4;
    public static final int ALT_MASK = 8;
    public static final int ACTION_FIRST = 1001;
    public static final int ACTION_LAST = 1001;
    public static final int ACTION_PERFORMED = ACTION_FIRST;
    protected String actionCommand;
    protected long when;
    protected int modifiers;
    public ActionEvent(Object source, int id, String command) { this(source, id, command, 0); }
    public ActionEvent(Object source, int id, String command, int modifiers) { this(source, id, command, 0, modifiers); }
    public ActionEvent(Object source, int id, String command, long when, int modifiers) {
        super(source, id); actionCommand = command; this.when = when; this.modifiers = modifiers;
    }
    public String getActionCommand() { return actionCommand; }
    public long getWhen() { return when; }
    public int getModifiers() { return modifiers; }
}
"""

FILES[EV + "ActionListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.ActionListener. */
public interface ActionListener extends java.util.EventListener {
    void actionPerformed(ActionEvent e);
}
"""

FILES[EV + "ComponentEvent.java"] = """package java.awt.event;
import java.awt.Component;
/** Minimal java.awt.event.ComponentEvent. */
public class ComponentEvent extends java.awt.AWTEvent {
    public static final int COMPONENT_FIRST = 100;
    public static final int COMPONENT_LAST = 103;
    public static final int COMPONENT_MOVED = COMPONENT_FIRST;
    public static final int COMPONENT_RESIZED = 1 + COMPONENT_FIRST;
    public static final int COMPONENT_SHOWN = 2 + COMPONENT_FIRST;
    public static final int COMPONENT_HIDDEN = 3 + COMPONENT_FIRST;
    public ComponentEvent(Component source, int id) { super(source, id); }
    public Component getComponent() { return (Component) getSource(); }
}
"""

FILES[EV + "ComponentListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.ComponentListener. */
public interface ComponentListener extends java.util.EventListener {
    void componentResized(ComponentEvent e);
    void componentMoved(ComponentEvent e);
    void componentShown(ComponentEvent e);
    void componentHidden(ComponentEvent e);
}
"""

FILES[EV + "ComponentAdapter.java"] = """package java.awt.event;
/** Minimal java.awt.event.ComponentAdapter. */
public abstract class ComponentAdapter implements ComponentListener {
    public void componentResized(ComponentEvent e) {}
    public void componentMoved(ComponentEvent e) {}
    public void componentShown(ComponentEvent e) {}
    public void componentHidden(ComponentEvent e) {}
}
"""

FILES[EV + "FocusEvent.java"] = """package java.awt.event;
import java.awt.Component;
/** Minimal java.awt.event.FocusEvent. */
public class FocusEvent extends ComponentEvent {
    public static final int FOCUS_FIRST = 1004;
    public static final int FOCUS_LAST = 1005;
    public static final int FOCUS_GAINED = FOCUS_FIRST;
    public static final int FOCUS_LOST = 1 + FOCUS_FIRST;
    protected boolean temporary;
    protected Component opposite;
    public FocusEvent(Component source, int id) { this(source, id, false); }
    public FocusEvent(Component source, int id, boolean temporary) { super(source, id); this.temporary = temporary; }
    public FocusEvent(Component source, int id, boolean temporary, Component opposite) {
        super(source, id); this.temporary = temporary; this.opposite = opposite;
    }
    public boolean isTemporary() { return temporary; }
    public Component getOppositeComponent() { return opposite; }
}
"""

FILES[EV + "FocusListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.FocusListener. */
public interface FocusListener extends java.util.EventListener {
    void focusGained(FocusEvent e);
    void focusLost(FocusEvent e);
}
"""

FILES[EV + "FocusAdapter.java"] = """package java.awt.event;
/** Minimal java.awt.event.FocusAdapter. */
public abstract class FocusAdapter implements FocusListener {
    public void focusGained(FocusEvent e) {}
    public void focusLost(FocusEvent e) {}
}
"""

FILES[EV + "ItemEvent.java"] = """package java.awt.event;
import java.awt.ItemSelectable;
/** Minimal java.awt.event.ItemEvent. */
public class ItemEvent extends java.awt.AWTEvent {
    public static final int ITEM_FIRST = 701;
    public static final int ITEM_LAST = 701;
    public static final int ITEM_STATE_CHANGED = ITEM_FIRST;
    public static final int SELECTED = 1;
    public static final int DESELECTED = 2;
    protected ItemSelectable itemSelectable;
    protected Object item;
    protected int stateChange;
    public ItemEvent(ItemSelectable source, int id, Object item, int stateChange) {
        super(source, id); itemSelectable = source; this.item = item; this.stateChange = stateChange;
    }
    public ItemSelectable getItemSelectable() { return itemSelectable; }
    public Object getItem() { return item; }
    public int getStateChange() { return stateChange; }
}
"""

FILES[EV + "ItemListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.ItemListener. */
public interface ItemListener extends java.util.EventListener {
    void itemStateChanged(ItemEvent e);
}
"""

FILES[EV + "KeyEvent.java"] = """package java.awt.event;
import java.awt.Component;
/** Minimal java.awt.event.KeyEvent (common VK_ constants included). */
public class KeyEvent extends InputEvent {
    public static final int KEY_FIRST = 400;
    public static final int KEY_LAST = 402;
    public static final int KEY_TYPED = KEY_FIRST;
    public static final int KEY_PRESSED = 1 + KEY_FIRST;
    public static final int KEY_RELEASED = 2 + KEY_FIRST;
    public static final int VK_UNDEFINED = 0x0;
    public static final int VK_ENTER = '\\n';
    public static final int VK_BACK_SPACE = '\\b';
    public static final int VK_TAB = '\\t';
    public static final int VK_CANCEL = 0x03;
    public static final int VK_CLEAR = 0x0C;
    public static final int VK_SHIFT = 0x10;
    public static final int VK_CONTROL = 0x11;
    public static final int VK_ALT = 0x12;
    public static final int VK_PAUSE = 0x13;
    public static final int VK_CAPS_LOCK = 0x14;
    public static final int VK_ESCAPE = 0x1B;
    public static final int VK_SPACE = 0x20;
    public static final int VK_PAGE_UP = 0x21;
    public static final int VK_PAGE_DOWN = 0x22;
    public static final int VK_END = 0x23;
    public static final int VK_HOME = 0x24;
    public static final int VK_LEFT = 0x25;
    public static final int VK_UP = 0x26;
    public static final int VK_RIGHT = 0x27;
    public static final int VK_DOWN = 0x28;
    public static final int VK_COMMA = 0x2C;
    public static final int VK_MINUS = 0x2D;
    public static final int VK_PERIOD = 0x2E;
    public static final int VK_SLASH = 0x2F;
    public static final int VK_0 = 0x30;
    public static final int VK_1 = 0x31;
    public static final int VK_2 = 0x32;
    public static final int VK_3 = 0x33;
    public static final int VK_4 = 0x34;
    public static final int VK_5 = 0x35;
    public static final int VK_6 = 0x36;
    public static final int VK_7 = 0x37;
    public static final int VK_8 = 0x38;
    public static final int VK_9 = 0x39;
    public static final int VK_SEMICOLON = 0x3B;
    public static final int VK_EQUALS = 0x3D;
    public static final int VK_A = 0x41;
    public static final int VK_B = 0x42;
    public static final int VK_C = 0x43;
    public static final int VK_D = 0x44;
    public static final int VK_E = 0x45;
    public static final int VK_F = 0x46;
    public static final int VK_G = 0x47;
    public static final int VK_H = 0x48;
    public static final int VK_I = 0x49;
    public static final int VK_J = 0x4A;
    public static final int VK_K = 0x4B;
    public static final int VK_L = 0x4C;
    public static final int VK_M = 0x4D;
    public static final int VK_N = 0x4E;
    public static final int VK_O = 0x4F;
    public static final int VK_P = 0x50;
    public static final int VK_Q = 0x51;
    public static final int VK_R = 0x52;
    public static final int VK_S = 0x53;
    public static final int VK_T = 0x54;
    public static final int VK_U = 0x55;
    public static final int VK_V = 0x56;
    public static final int VK_W = 0x57;
    public static final int VK_X = 0x58;
    public static final int VK_Y = 0x59;
    public static final int VK_Z = 0x5A;
    public static final int VK_OPEN_BRACKET = 0x5B;
    public static final int VK_BACK_SLASH = 0x5C;
    public static final int VK_CLOSE_BRACKET = 0x5D;
    public static final int VK_NUMPAD0 = 0x60;
    public static final int VK_NUMPAD1 = 0x61;
    public static final int VK_NUMPAD2 = 0x62;
    public static final int VK_NUMPAD3 = 0x63;
    public static final int VK_NUMPAD4 = 0x64;
    public static final int VK_NUMPAD5 = 0x65;
    public static final int VK_NUMPAD6 = 0x66;
    public static final int VK_NUMPAD7 = 0x67;
    public static final int VK_NUMPAD8 = 0x68;
    public static final int VK_NUMPAD9 = 0x69;
    public static final int VK_MULTIPLY = 0x6A;
    public static final int VK_ADD = 0x6B;
    public static final int VK_SEPARATOR = 0x6C;
    public static final int VK_SUBTRACT = 0x6D;
    public static final int VK_DECIMAL = 0x6E;
    public static final int VK_DIVIDE = 0x6F;
    public static final int VK_DELETE = 0x7F;
    public static final int VK_NUM_LOCK = 0x90;
    public static final int VK_SCROLL_LOCK = 0x91;
    public static final int VK_F1 = 0x70;
    public static final int VK_F2 = 0x71;
    public static final int VK_F3 = 0x72;
    public static final int VK_F4 = 0x73;
    public static final int VK_F5 = 0x74;
    public static final int VK_F6 = 0x75;
    public static final int VK_F7 = 0x76;
    public static final int VK_F8 = 0x77;
    public static final int VK_F9 = 0x78;
    public static final int VK_F10 = 0x79;
    public static final int VK_F11 = 0x7A;
    public static final int VK_F12 = 0x7B;
    public static final int VK_PRINTSCREEN = 0x9A;
    public static final int VK_INSERT = 0x9B;
    public static final int VK_HELP = 0x9C;
    public static final int VK_META = 0x9D;
    public static final int VK_QUOTE = 0xDE;
    public static final int VK_PLUS = 0xBB;
    public static final int VK_WINDOWS = 0x020C;
    public static final int VK_CONTEXT_MENU = 0x020D;
    public static final int VK_BACK_QUOTE = 0xC0;
    protected int keyCode;
    protected char keyChar;
    protected int keyLocation;
    public KeyEvent(Component source, int id, long when, int modifiers, int keyCode, char keyChar) {
        this(source, id, when, modifiers, keyCode, keyChar, KEY_LOCATION_UNKNOWN);
    }
    public KeyEvent(Component source, int id, long when, int modifiers, int keyCode, char keyChar, int keyLocation) {
        super(source, id, when, modifiers); this.keyCode = keyCode; this.keyChar = keyChar; this.keyLocation = keyLocation;
    }
    public int getKeyCode() { return keyCode; }
    public void setKeyCode(int keyCode) { this.keyCode = keyCode; }
    public char getKeyChar() { return keyChar; }
    public void setKeyChar(char keyChar) { this.keyChar = keyChar; }
    public int getKeyLocation() { return keyLocation; }
    public static final int KEY_LOCATION_UNKNOWN = 0;
    public static final int KEY_LOCATION_STANDARD = 1;
    public static final int KEY_LOCATION_LEFT = 2;
    public static final int KEY_LOCATION_RIGHT = 3;
    public static final int KEY_LOCATION_NUMPAD = 4;
    public static String getKeyText(int keyCode) { return "key" + keyCode; }
    public static String getKeyModifiersText(int modifiers) { return ""; }
    public boolean isActionKey() { return false; }
}
"""

FILES[EV + "KeyListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.KeyListener. */
public interface KeyListener extends java.util.EventListener {
    void keyTyped(KeyEvent e);
    void keyPressed(KeyEvent e);
    void keyReleased(KeyEvent e);
}
"""

FILES[EV + "KeyAdapter.java"] = """package java.awt.event;
/** Minimal java.awt.event.KeyAdapter. */
public abstract class KeyAdapter implements KeyListener {
    public void keyTyped(KeyEvent e) {}
    public void keyPressed(KeyEvent e) {}
    public void keyReleased(KeyEvent e) {}
}
"""

FILES[EV + "MouseEvent.java"] = """package java.awt.event;
import java.awt.Component;
import java.awt.Point;
/** Minimal java.awt.event.MouseEvent. */
public class MouseEvent extends InputEvent {
    public static final int MOUSE_FIRST = 500;
    public static final int MOUSE_LAST = 507;
    public static final int MOUSE_CLICKED = MOUSE_FIRST;
    public static final int MOUSE_PRESSED = 1 + MOUSE_FIRST;
    public static final int MOUSE_RELEASED = 2 + MOUSE_FIRST;
    public static final int MOUSE_MOVED = 3 + MOUSE_FIRST;
    public static final int MOUSE_ENTERED = 4 + MOUSE_FIRST;
    public static final int MOUSE_EXITED = 5 + MOUSE_FIRST;
    public static final int MOUSE_DRAGGED = 6 + MOUSE_FIRST;
    public static final int MOUSE_WHEEL = 7 + MOUSE_FIRST;
    public static final int NOBUTTON = 0;
    public static final int BUTTON1 = 1;
    public static final int BUTTON2 = 2;
    public static final int BUTTON3 = 3;
    protected int x, y, clickCount, button;
    protected boolean popupTrigger;
    public MouseEvent(Component source, int id, long when, int modifiers, int x, int y, int clickCount, boolean popupTrigger) {
        this(source, id, when, modifiers, x, y, clickCount, popupTrigger, NOBUTTON);
    }
    public MouseEvent(Component source, int id, long when, int modifiers, int x, int y, int clickCount, boolean popupTrigger, int button) {
        super(source, id, when, modifiers);
        this.x = x; this.y = y; this.clickCount = clickCount; this.popupTrigger = popupTrigger; this.button = button;
    }
    public int getX() { return x; }
    public int getY() { return y; }
    public Point getPoint() { return new Point(x, y); }
    public int getClickCount() { return clickCount; }
    public int getButton() { return button; }
    public boolean isPopupTrigger() { return popupTrigger; }
    public void translatePoint(int x, int y) { this.x += x; this.y += y; }
    public static String getMouseModifiersText(int modifiers) { return ""; }
}
"""

FILES[EV + "MouseListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.MouseListener. */
public interface MouseListener extends java.util.EventListener {
    void mouseClicked(MouseEvent e);
    void mousePressed(MouseEvent e);
    void mouseReleased(MouseEvent e);
    void mouseEntered(MouseEvent e);
    void mouseExited(MouseEvent e);
}
"""

FILES[EV + "MouseMotionListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.MouseMotionListener. */
public interface MouseMotionListener extends java.util.EventListener {
    void mouseDragged(MouseEvent e);
    void mouseMoved(MouseEvent e);
}
"""

FILES[EV + "MouseAdapter.java"] = """package java.awt.event;
/** Minimal java.awt.event.MouseAdapter. */
public abstract class MouseAdapter implements MouseListener, MouseMotionListener, MouseWheelListener {
    public void mouseClicked(MouseEvent e) {}
    public void mousePressed(MouseEvent e) {}
    public void mouseReleased(MouseEvent e) {}
    public void mouseEntered(MouseEvent e) {}
    public void mouseExited(MouseEvent e) {}
    public void mouseDragged(MouseEvent e) {}
    public void mouseMoved(MouseEvent e) {}
    public void mouseWheelMoved(MouseWheelEvent e) {}
}
"""

FILES[EV + "MouseMotionAdapter.java"] = """package java.awt.event;
/** Minimal java.awt.event.MouseMotionAdapter. */
public abstract class MouseMotionAdapter implements MouseMotionListener {
    public void mouseDragged(MouseEvent e) {}
    public void mouseMoved(MouseEvent e) {}
}
"""

FILES[EV + "MouseWheelEvent.java"] = """package java.awt.event;
import java.awt.Component;
/** Minimal java.awt.event.MouseWheelEvent. */
public class MouseWheelEvent extends MouseEvent {
    public static final int WHEEL_UNIT_SCROLL = 0;
    public static final int WHEEL_BLOCK_SCROLL = 1;
    protected int scrollType, scrollAmount, wheelRotation;
    protected double preciseWheelRotation;
    public MouseWheelEvent(Component source, int id, long when, int modifiers, int x, int y, int clickCount, boolean popupTrigger, int scrollType, int scrollAmount, int wheelRotation) {
        super(source, id, when, modifiers, x, y, clickCount, popupTrigger);
        this.scrollType = scrollType; this.scrollAmount = scrollAmount; this.wheelRotation = wheelRotation;
    }
    public MouseWheelEvent(Component source, int id, long when, int modifiers, int x, int y, int xAbs, int yAbs, int clickCount, boolean popupTrigger, int scrollType, int scrollAmount, int wheelRotation, double preciseWheelRotation) {
        this(source, id, when, modifiers, x, y, clickCount, popupTrigger, scrollType, scrollAmount, wheelRotation);
        this.preciseWheelRotation = preciseWheelRotation;
    }
    public int getScrollType() { return scrollType; }
    public int getScrollAmount() { return scrollAmount; }
    public int getWheelRotation() { return wheelRotation; }
    public double getPreciseWheelRotation() { return preciseWheelRotation; }
    public int getUnitsToScroll() { return scrollAmount * wheelRotation; }
}
"""

FILES[EV + "MouseWheelListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.MouseWheelListener. */
public interface MouseWheelListener extends java.util.EventListener {
    void mouseWheelMoved(MouseWheelEvent e);
}
"""

FILES[EV + "WindowEvent.java"] = """package java.awt.event;
import java.awt.Window;
/** Minimal java.awt.event.WindowEvent. */
public class WindowEvent extends ComponentEvent {
    public static final int WINDOW_FIRST = 200;
    public static final int WINDOW_LAST = 209;
    public static final int WINDOW_OPENED = WINDOW_FIRST;
    public static final int WINDOW_CLOSING = 1 + WINDOW_FIRST;
    public static final int WINDOW_CLOSED = 2 + WINDOW_FIRST;
    public static final int WINDOW_ICONIFIED = 3 + WINDOW_FIRST;
    public static final int WINDOW_DEICONIFIED = 4 + WINDOW_FIRST;
    public static final int WINDOW_ACTIVATED = 5 + WINDOW_FIRST;
    public static final int WINDOW_DEACTIVATED = 6 + WINDOW_FIRST;
    public static final int WINDOW_GAINED_FOCUS = 7 + WINDOW_FIRST;
    public static final int WINDOW_LOST_FOCUS = 8 + WINDOW_FIRST;
    public static final int WINDOW_STATE_CHANGED = 9 + WINDOW_FIRST;
    protected Window opposite;
    protected int oldState, newState;
    public WindowEvent(Window source, int id) { super(source, id); }
    public WindowEvent(Window source, int id, Window opposite) { super(source, id); this.opposite = opposite; }
    public WindowEvent(Window source, int id, int oldState, int newState) {
        super(source, id); this.oldState = oldState; this.newState = newState;
    }
    public Window getWindow() { return (Window) getSource(); }
    public Window getOppositeWindow() { return opposite; }
    public int getOldState() { return oldState; }
    public int getNewState() { return newState; }
}
"""

FILES[EV + "WindowListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.WindowListener. */
public interface WindowListener extends java.util.EventListener {
    void windowOpened(WindowEvent e);
    void windowClosing(WindowEvent e);
    void windowClosed(WindowEvent e);
    void windowIconified(WindowEvent e);
    void windowDeiconified(WindowEvent e);
    void windowActivated(WindowEvent e);
    void windowDeactivated(WindowEvent e);
}
"""

FILES[EV + "WindowAdapter.java"] = """package java.awt.event;
/** Minimal java.awt.event.WindowAdapter. */
public abstract class WindowAdapter implements WindowListener, WindowStateListener, WindowFocusListener {
    public void windowOpened(WindowEvent e) {}
    public void windowClosing(WindowEvent e) {}
    public void windowClosed(WindowEvent e) {}
    public void windowIconified(WindowEvent e) {}
    public void windowDeiconified(WindowEvent e) {}
    public void windowActivated(WindowEvent e) {}
    public void windowDeactivated(WindowEvent e) {}
    public void windowStateChanged(WindowEvent e) {}
    public void windowGainedFocus(WindowEvent e) {}
    public void windowLostFocus(WindowEvent e) {}
}
"""

FILES[EV + "WindowStateListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.WindowStateListener. */
public interface WindowStateListener extends java.util.EventListener {
    void windowStateChanged(WindowEvent e);
}
"""

FILES[EV + "WindowFocusListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.WindowFocusListener. */
public interface WindowFocusListener extends java.util.EventListener {
    void windowGainedFocus(WindowEvent e);
    void windowLostFocus(WindowEvent e);
}
"""

FILES[EV + "AdjustmentEvent.java"] = """package java.awt.event;
/** Minimal java.awt.event.AdjustmentEvent. */
public class AdjustmentEvent extends java.awt.AWTEvent {
    public static final int ADJUSTMENT_FIRST = 601;
    public static final int ADJUSTMENT_LAST = 601;
    public static final int ADJUSTMENT_VALUE_CHANGED = ADJUSTMENT_FIRST;
    public static final int UNIT_INCREMENT = 1;
    public static final int UNIT_DECREMENT = 2;
    public static final int BLOCK_DECREMENT = 3;
    public static final int BLOCK_INCREMENT = 4;
    public static final int TRACK = 5;
    protected java.awt.Adjustable adjustable;
    protected int value, adjustmentType;
    protected boolean isAdjusting;
    public AdjustmentEvent(java.awt.Adjustable source, int id, int type, int value) {
        this(source, id, type, value, false);
    }
    public AdjustmentEvent(java.awt.Adjustable source, int id, int type, int value, boolean isAdjusting) {
        super(source, id); adjustable = source; adjustmentType = type; this.value = value; this.isAdjusting = isAdjusting;
    }
    public java.awt.Adjustable getAdjustable() { return adjustable; }
    public int getValue() { return value; }
    public int getAdjustmentType() { return adjustmentType; }
    public boolean getValueIsAdjusting() { return isAdjusting; }
}
"""

FILES[EV + "AdjustmentListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.AdjustmentListener. */
public interface AdjustmentListener extends java.util.EventListener {
    void adjustmentValueChanged(AdjustmentEvent e);
}
"""

FILES[EV + "TextEvent.java"] = """package java.awt.event;
/** Minimal java.awt.event.TextEvent. */
public class TextEvent extends java.awt.AWTEvent {
    public static final int TEXT_FIRST = 900;
    public static final int TEXT_LAST = 900;
    public static final int TEXT_VALUE_CHANGED = TEXT_FIRST;
    public TextEvent(Object source, int id) { super(source, id); }
}
"""

FILES[EV + "TextListener.java"] = """package java.awt.event;
/** Minimal java.awt.event.TextListener. */
public interface TextListener extends java.util.EventListener {
    void textValueChanged(TextEvent e);
}
"""

# ---- java.awt.datatransfer ----
DT = "java/awt/datatransfer/"
FILES[DT + "DataFlavor.java"] = """package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.DataFlavor. */
public class DataFlavor implements java.io.Externalizable, Cloneable {
    public static final DataFlavor stringFlavor;
    public static final DataFlavor imageFlavor;
    public static final DataFlavor javaFileListFlavor;
    static {
        DataFlavor sf = null, imf = null, jfl = null;
        try {
            sf = new DataFlavor("application/x-java-serialized-object; class=java.lang.String");
            imf = new DataFlavor("image/x-java-image; class=java.awt.Image");
            jfl = new DataFlavor("application/x-java-file-list; class=java.util.List");
        } catch (Exception ignored) {
        }
        stringFlavor = sf; imageFlavor = imf; javaFileListFlavor = jfl;
    }
    protected String mimeType;
    protected Class<?> representationClass;
    protected String humanPresentableName;
    public DataFlavor() {}
    public DataFlavor(String mimeType) { this.mimeType = mimeType; }
    public DataFlavor(Class<?> representationClass, String humanPresentableName) {
        this.representationClass = representationClass; this.humanPresentableName = humanPresentableName;
    }
    public DataFlavor(String mimeType, String humanPresentableName) throws ClassNotFoundException {
        this.mimeType = mimeType; this.humanPresentableName = humanPresentableName;
    }
    public DataFlavor(String mimeType, String humanPresentableName, ClassLoader classLoader) throws ClassNotFoundException {
        this.mimeType = mimeType; this.humanPresentableName = humanPresentableName;
    }
    public String getMimeType() { return mimeType; }
    public Class<?> getRepresentationClass() { return representationClass; }
    public String getHumanPresentableName() { return humanPresentableName; }
    public void setHumanPresentableName(String name) { humanPresentableName = name; }
    public boolean isMimeTypeEqual(DataFlavor that) { return mimeType != null && mimeType.equals(that.mimeType); }
    public boolean isMimeTypeEqual(String mimeType) { return this.mimeType != null && this.mimeType.equals(mimeType); }
    public boolean equals(Object o) { return o instanceof DataFlavor && ((DataFlavor) o).mimeType != null && ((DataFlavor) o).mimeType.equals(mimeType); }
    public boolean equals(DataFlavor that) { return equals((Object) that); }
    public int hashCode() { return mimeType == null ? 0 : mimeType.hashCode(); }
    public String toString() { return mimeType; }
    public void writeExternal(java.io.ObjectOutput out) throws java.io.IOException {}
    public void readExternal(java.io.ObjectInput in) throws java.io.IOException, ClassNotFoundException {}
    public Object clone() { return this; }
}
"""

FILES[DT + "Transferable.java"] = """package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.Transferable. */
public interface Transferable {
    DataFlavor[] getTransferDataFlavors();
    boolean isDataFlavorSupported(DataFlavor flavor);
    Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, java.io.IOException;
}
"""

FILES[DT + "ClipboardOwner.java"] = """package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.ClipboardOwner. */
public interface ClipboardOwner {
    void lostOwnership(Clipboard clipboard, Transferable contents);
}
"""

FILES[DT + "Clipboard.java"] = """package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.Clipboard. */
public class Clipboard {
    protected String name;
    protected Transferable contents;
    protected ClipboardOwner owner;
    public Clipboard(String name) { this.name = name; }
    public String getName() { return name; }
    public synchronized void setContents(Transferable contents, ClipboardOwner owner) {
        this.contents = contents; this.owner = owner;
    }
    public synchronized Transferable getContents(Object requestor) { return contents; }
    public synchronized DataFlavor[] getAvailableDataFlavors() { return new DataFlavor[0]; }
    public synchronized boolean isDataFlavorAvailable(DataFlavor flavor) { return false; }
    public synchronized Object getData(DataFlavor flavor) throws UnsupportedFlavorException, java.io.IOException {
        throw new UnsupportedFlavorException(flavor);
    }
    public void addFlavorListener(java.awt.datatransfer.FlavorListener listener) {}
    public void removeFlavorListener(java.awt.datatransfer.FlavorListener listener) {}
    public FlavorListener[] getFlavorListeners() { return new FlavorListener[0]; }
}
"""

FILES[DT + "FlavorListener.java"] = """package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.FlavorListener. */
public interface FlavorListener extends java.util.EventListener {
    void flavorsChanged(FlavorEvent e);
}
"""

FILES[DT + "FlavorEvent.java"] = """package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.FlavorEvent. */
public class FlavorEvent extends java.util.EventObject {
    public FlavorEvent(Clipboard source) { super(source); }
}
"""

FILES[DT + "UnsupportedFlavorException.java"] = """package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.UnsupportedFlavorException. */
public class UnsupportedFlavorException extends Exception {
    public UnsupportedFlavorException(DataFlavor flavor) { super(flavor == null ? null : flavor.toString()); }
}
"""

FILES[DT + "StringSelection.java"] = """package java.awt.datatransfer;
/** Minimal java.awt.datatransfer.StringSelection. */
public class StringSelection implements Transferable, ClipboardOwner {
    protected String data;
    public StringSelection(String data) { this.data = data; }
    public DataFlavor[] getTransferDataFlavors() { return new DataFlavor[]{DataFlavor.stringFlavor}; }
    public boolean isDataFlavorSupported(DataFlavor flavor) { return DataFlavor.stringFlavor.equals(flavor); }
    public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException {
        if (!isDataFlavorSupported(flavor)) throw new UnsupportedFlavorException(flavor);
        return data;
    }
    public void lostOwnership(Clipboard clipboard, Transferable contents) {}
}
"""

# ---- javax.swing ----
SW = "javax/swing/"
FILES[SW + "JComponent.java"] = """package javax.swing;
import java.awt.*;
import javax.swing.border.Border;
/** Minimal javax.swing.JComponent. */
public class JComponent extends Container {
    protected boolean opaque;
    protected Border border;
    public void setOpaque(boolean b) { opaque = b; }
    public boolean isOpaque() { return opaque; }
    public void setBorder(Border b) { border = b; }
    public Border getBorder() { return border; }
    public void setToolTipText(String text) {}
    public String getToolTipText() { return null; }
    public InputMap getInputMap() { return null; }
    public InputMap getInputMap(int condition) { return null; }
    public ActionMap getActionMap() { return null; }
    public void setDoubleBuffered(boolean b) {}
    public boolean isDoubleBuffered() { return false; }
    public void putClientProperty(Object key, Object value) {}
    public Object getClientProperty(Object key) { return null; }
    public void setAlignmentX(float f) {}
    public float getAlignmentX() { return 0.5f; }
    public void setAlignmentY(float f) {}
    public float getAlignmentY() { return 0.5f; }
    public Container getTopLevelAncestor() { return null; }
    public void setFocusable(boolean b) {}
    public boolean isFocusable() { return true; }
    public boolean requestFocusInWindow() { return false; }
    public void setDragEnabled(boolean b) {}
    public void setTransferHandler(javax.swing.TransferHandler newHandler) {}
    public javax.swing.TransferHandler getTransferHandler() { return null; }
    public void addAncestorListener(javax.swing.event.AncestorListener l) {}
    public void removeAncestorListener(javax.swing.event.AncestorListener l) {}
    public void setRequestFocusEnabled(boolean b) {}
    public boolean isRequestFocusEnabled() { return false; }
    public void setVerifyInputWhenFocusTarget(boolean b) {}
    public boolean getVerifyInputWhenFocusTarget() { return false; }
    public void setInheritsPopupMenu(boolean b) {}
    public boolean getInheritsPopupMenu() { return false; }
    public void setComponentPopupMenu(JPopupMenu p) {}
    public JPopupMenu getComponentPopupMenu() { return null; }
}
"""

FILES[SW + "AbstractButton.java"] = """package javax.swing;
import java.awt.event.*;
/** Minimal javax.swing.AbstractButton. */
public abstract class AbstractButton extends JComponent implements java.awt.ItemSelectable, SwingConstants {
    protected String text;
    protected Icon icon;
    protected boolean selected;
    protected String actionCommand;
    protected int mnemonic;
    public String getText() { return text; }
    public void setText(String text) { this.text = text; }
    public Icon getIcon() { return icon; }
    public void setIcon(Icon icon) { this.icon = icon; }
    public boolean isSelected() { return selected; }
    public void setSelected(boolean b) { selected = b; }
    public String getActionCommand() { return actionCommand; }
    public void setActionCommand(String cmd) { actionCommand = cmd; }
    public int getMnemonic() { return mnemonic; }
    public void setMnemonic(int m) { mnemonic = m; }
    public void setMnemonic(char m) { mnemonic = m; }
    public void addActionListener(ActionListener l) {}
    public void removeActionListener(ActionListener l) {}
    public ActionListener[] getActionListeners() { return new ActionListener[0]; }
    public void addItemListener(ItemListener l) {}
    public void removeItemListener(ItemListener l) {}
    public ItemListener[] getItemListeners() { return new ItemListener[0]; }
    public Object[] getSelectedObjects() { return selected ? new Object[]{text} : new Object[0]; }
    public void doClick() {}
    public void doClick(int pressTime) {}
    public void setAction(Action a) {}
    public Action getAction() { return null; }
    public void setHorizontalAlignment(int a) {}
    public int getHorizontalAlignment() { return CENTER; }
    public void setVerticalAlignment(int a) {}
    public int getVerticalAlignment() { return CENTER; }
    public void setDisplayedMnemonicIndex(int i) {}
    public int getDisplayedMnemonicIndex() { return -1; }
    public void setIconTextGap(int g) {}
    public int getIconTextGap() { return 0; }
    public void setRolloverEnabled(boolean b) {}
    public boolean isRolloverEnabled() { return false; }
    public void setBorderPainted(boolean b) {}
    public boolean isBorderPainted() { return false; }
    public void setContentAreaFilled(boolean b) {}
    public boolean isContentAreaFilled() { return false; }
    public void setFocusPainted(boolean b) {}
    public boolean isFocusPainted() { return false; }
}
"""

FILES[SW + "JButton.java"] = """package javax.swing;
/** Minimal javax.swing.JButton. */
public class JButton extends AbstractButton {
    public JButton() {}
    public JButton(String text) { this.text = text; }
    public JButton(Icon icon) { this.icon = icon; }
    public JButton(String text, Icon icon) { this.text = text; this.icon = icon; }
    public JButton(Action a) {}
    public boolean isDefaultButton() { return false; }
    public boolean isDefaultCapable() { return false; }
    public void setDefaultCapable(boolean b) {}
}
"""

FILES[SW + "JLabel.java"] = """package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JLabel. */
public class JLabel extends JComponent implements SwingConstants {
    protected String text;
    protected Icon icon;
    protected int horizontalAlignment = LEADING, verticalAlignment = CENTER;
    protected Component labelFor;
    public JLabel() {}
    public JLabel(String text) { this.text = text; }
    public JLabel(String text, int horizontalAlignment) { this.text = text; this.horizontalAlignment = horizontalAlignment; }
    public JLabel(Icon image) { icon = image; }
    public JLabel(Icon image, int horizontalAlignment) { icon = image; this.horizontalAlignment = horizontalAlignment; }
    public JLabel(String text, Icon icon, int horizontalAlignment) {
        this.text = text; this.icon = icon; this.horizontalAlignment = horizontalAlignment;
    }
    public String getText() { return text; }
    public void setText(String text) { this.text = text; }
    public Icon getIcon() { return icon; }
    public void setIcon(Icon icon) { this.icon = icon; }
    public int getHorizontalAlignment() { return horizontalAlignment; }
    public void setHorizontalAlignment(int a) { horizontalAlignment = a; }
    public int getVerticalAlignment() { return verticalAlignment; }
    public void setVerticalAlignment(int a) { verticalAlignment = a; }
    public Component getLabelFor() { return labelFor; }
    public void setLabelFor(Component c) { labelFor = c; }
    public Icon getDisabledIcon() { return null; }
    public void setDisabledIcon(Icon icon) {}
    public int getDisplayedMnemonic() { return 0; }
    public void setDisplayedMnemonic(int m) {}
    public void setDisplayedMnemonic(char m) {}
    public int getDisplayedMnemonicIndex() { return -1; }
    public void setDisplayedMnemonicIndex(int i) {}
    public void setIconTextGap(int g) {}
    public int getIconTextGap() { return 0; }
}
"""

FILES[SW + "JTabbedPane.java"] = """package javax.swing;
import java.awt.*;
import javax.swing.event.ChangeListener;
/** Minimal javax.swing.JTabbedPane. */
public class JTabbedPane extends JComponent {
    public static final int WRAP_TAB_LAYOUT = 0;
    public static final int SCROLL_TAB_LAYOUT = 1;
    public static final int TOP = 1;
    public static final int BOTTOM = 3;
    public static final int LEFT = 2;
    public static final int RIGHT = 4;
    protected int tabPlacement = TOP;
    protected int selectedIndex = -1;
    public JTabbedPane() {}
    public JTabbedPane(int tabPlacement) { this.tabPlacement = tabPlacement; }
    public JTabbedPane(int tabPlacement, int tabLayoutPolicy) { this.tabPlacement = tabPlacement; }
    public void addTab(String title, Component component) {}
    public void addTab(String title, Icon icon, Component component) {}
    public void addTab(String title, Icon icon, Component component, String tip) {}
    public void insertTab(String title, Icon icon, Component component, String tip, int index) {}
    public void removeTabAt(int index) {}
    public int getTabCount() { return 0; }
    public int getSelectedIndex() { return selectedIndex; }
    public void setSelectedIndex(int index) { selectedIndex = index; }
    public Component getSelectedComponent() { return null; }
    public void setSelectedComponent(Component c) {}
    public String getTitleAt(int index) { return null; }
    public void setTitleAt(int index, String title) {}
    public Icon getIconAt(int index) { return null; }
    public void setIconAt(int index, Icon icon) {}
    public String getToolTipTextAt(int index) { return null; }
    public void setToolTipTextAt(int index, String text) {}
    public Component getComponentAt(int index) { return null; }
    public void setComponentAt(int index, Component component) {}
    public int getTabPlacement() { return tabPlacement; }
    public void setTabPlacement(int tabPlacement) { this.tabPlacement = tabPlacement; }
    public void setEnabledAt(int index, boolean enabled) {}
    public boolean isEnabledAt(int index) { return false; }
    public int indexOfComponent(Component component) { return -1; }
    public int indexOfTab(String title) { return -1; }
    public void setMnemonicAt(int index, int mnemonic) {}
    public int getMnemonicAt(int index) { return 0; }
    public void addChangeListener(ChangeListener l) {}
    public void removeChangeListener(ChangeListener l) {}
    public ChangeListener[] getChangeListeners() { return new ChangeListener[0]; }
    public void setTabLayoutPolicy(int policy) {}
    public int getTabLayoutPolicy() { return WRAP_TAB_LAYOUT; }
}
"""

FILES[SW + "JPopupMenu.java"] = """package javax.swing;
import java.awt.*;
import java.awt.event.*;
/** Minimal javax.swing.JPopupMenu. */
public class JPopupMenu extends JComponent {
    protected String label;
    public JPopupMenu() {}
    public JPopupMenu(String label) { this.label = label; }
    public JMenuItem add(JMenuItem menuItem) { return menuItem; }
    public JMenuItem add(String s) { return new JMenuItem(s); }
    public JMenuItem add(Action a) { return new JMenuItem(); }
    public void addSeparator() {}
    public void insert(Action a, int index) {}
    public void insert(Component component, int index) {}
    public void remove(int index) {}
    public void removeAll() {}
    public int getComponentCount() { return 0; }
    public void show(Component invoker, int x, int y) {}
    public void setLabel(String label) { this.label = label; }
    public String getLabel() { return label; }
    public void setLightWeightPopupEnabled(boolean b) {}
    public boolean isLightWeightPopupEnabled() { return false; }
    public void addPopupMenuListener(javax.swing.event.PopupMenuListener l) {}
    public void removePopupMenuListener(javax.swing.event.PopupMenuListener l) {}
    public javax.swing.event.PopupMenuListener[] getPopupMenuListeners() { return new javax.swing.event.PopupMenuListener[0]; }
    public void setInvoker(Component invoker) {}
    public Component getInvoker() { return null; }
    public void pack() {}
    public boolean isVisible() { return false; }
    public void setVisible(boolean b) {}
}
"""

FILES[SW + "JMenuItem.java"] = """package javax.swing;
/** Minimal javax.swing.JMenuItem. */
public class JMenuItem extends AbstractButton {
    public JMenuItem() {}
    public JMenuItem(String text) { this.text = text; }
    public JMenuItem(Icon icon) { this.icon = icon; }
    public JMenuItem(String text, Icon icon) { this.text = text; this.icon = icon; }
    public JMenuItem(String text, int mnemonic) { this.text = text; this.mnemonic = mnemonic; }
    public JMenuItem(Action a) {}
    public void setAccelerator(KeyStroke keyStroke) {}
    public KeyStroke getAccelerator() { return null; }
    public void setArmed(boolean b) {}
    public boolean isArmed() { return false; }
}
"""

FILES[SW + "event/PopupMenuListener.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.PopupMenuListener. */
public interface PopupMenuListener extends java.util.EventListener {
    void popupMenuWillBecomeVisible(PopupMenuEvent e);
    void popupMenuWillBecomeInvisible(PopupMenuEvent e);
    void popupMenuCanceled(PopupMenuEvent e);
}
"""

FILES[SW + "event/PopupMenuEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.PopupMenuEvent. */
public class PopupMenuEvent extends java.util.EventObject {
    public PopupMenuEvent(Object source) { super(source); }
}
"""

FILES[SW + "Icon.java"] = """package javax.swing;
import java.awt.Component;
import java.awt.Graphics;
/** Minimal javax.swing.Icon (replaces the round-1 version with the full contract). */
public interface Icon {
    void paintIcon(Component c, Graphics g, int x, int y);
    int getIconWidth();
    int getIconHeight();
}
"""

FILES[SW + "ImageIcon.java"] = """package javax.swing;
import java.awt.*;
import java.net.URL;
/** Minimal javax.swing.ImageIcon. */
public class ImageIcon implements Icon, java.io.Serializable {
    protected String filename;
    protected Image image;
    protected String description;
    public ImageIcon() {}
    public ImageIcon(String filename) { this.filename = filename; }
    public ImageIcon(String filename, String description) { this.filename = filename; this.description = description; }
    public ImageIcon(URL location) {}
    public ImageIcon(URL location, String description) {}
    public ImageIcon(Image image) { this.image = image; }
    public ImageIcon(Image image, String description) { this.image = image; this.description = description; }
    public ImageIcon(byte[] imageData) {}
    public ImageIcon(byte[] imageData, String description) {}
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public Image getImage() { return image; }
    public void setImage(Image image) { this.image = image; }
    public int getIconWidth() { return image == null ? 0 : image.getWidth(null); }
    public int getIconHeight() { return image == null ? 0 : image.getHeight(null); }
    public void paintIcon(Component c, Graphics g, int x, int y) {}
    public void setImageObserver(java.awt.image.ImageObserver observer) {}
    public java.awt.image.ImageObserver getImageObserver() { return null; }
    public int getImageLoadStatus() { return 0; }
}
"""

FILES[SW + "Action.java"] = """package javax.swing;
import java.awt.event.ActionListener;
import java.beans.PropertyChangeListener;
/** Minimal javax.swing.Action. */
public interface Action extends ActionListener {
    String DEFAULT = "Default";
    String NAME = "Name";
    String SHORT_DESCRIPTION = "ShortDescription";
    String LONG_DESCRIPTION = "LongDescription";
    String SMALL_ICON = "SmallIcon";
    String ACTION_COMMAND_KEY = "ActionCommandKey";
    String ACCELERATOR_KEY = "AcceleratorKey";
    String MNEMONIC_KEY = "MnemonicKey";
    String SELECTED_KEY = "SwingSelectedKey";
    String DISPLAYED_MNEMONIC_INDEX_KEY = "SwingDisplayedMnemonicIndexKey";
    String LARGE_ICON_KEY = "SwingLargeIconKey";
    Object getValue(String key);
    void putValue(String key, Object value);
    void setEnabled(boolean b);
    boolean isEnabled();
    void addPropertyChangeListener(PropertyChangeListener listener);
    void removePropertyChangeListener(PropertyChangeListener listener);
}
"""

FILES[SW + "ActionMap.java"] = """package javax.swing;
/** Minimal javax.swing.ActionMap. */
public class ActionMap implements java.io.Serializable {
    public ActionMap() {}
    public void setParent(ActionMap map) {}
    public ActionMap getParent() { return null; }
    public void put(Object key, Action action) {}
    public Action get(Object key) { return null; }
    public void remove(Object key) {}
    public void clear() {}
    public Object[] keys() { return new Object[0]; }
    public int size() { return 0; }
    public Object[] allKeys() { return new Object[0]; }
}
"""

FILES[SW + "InputMap.java"] = """package javax.swing;
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
"""

FILES[SW + "KeyStroke.java"] = """package javax.swing;
/** Minimal javax.swing.KeyStroke. */
public class KeyStroke implements java.io.Serializable {
    protected int keyCode, modifiers;
    protected char keyChar;
    protected boolean onKeyRelease;
    protected KeyStroke() {}
    protected KeyStroke(int keyCode, int modifiers, boolean onKeyRelease) {
        this.keyCode = keyCode; this.modifiers = modifiers; this.onKeyRelease = onKeyRelease;
    }
    protected KeyStroke(char keyChar, int modifiers) { this.keyChar = keyChar; this.modifiers = modifiers; }
    public static KeyStroke getKeyStroke(int keyCode, int modifiers, boolean onKeyRelease) {
        return new KeyStroke(keyCode, modifiers, onKeyRelease);
    }
    public static KeyStroke getKeyStroke(int keyCode, int modifiers) { return new KeyStroke(keyCode, modifiers, false); }
    public static KeyStroke getKeyStroke(char keyChar) { return new KeyStroke(keyChar, 0); }
    public static KeyStroke getKeyStroke(String s) { return new KeyStroke(); }
    public static KeyStroke getKeyStrokeForEvent(java.awt.event.KeyEvent e) { return new KeyStroke(); }
    public static KeyStroke getKeyStroke(int keyCode, int modifiers, boolean onKeyRelease, int dummy) { return new KeyStroke(keyCode, modifiers, onKeyRelease); }
    public int getKeyCode() { return keyCode; }
    public char getKeyChar() { return keyChar; }
    public int getModifiers() { return modifiers; }
    public boolean isOnKeyRelease() { return onKeyRelease; }
    public int getKeyEventType() { return 0; }
}
"""

FILES[SW + "SwingConstants.java"] = """package javax.swing;
/** Minimal javax.swing.SwingConstants. */
public interface SwingConstants {
    int CENTER = 0;
    int TOP = 1;
    int LEFT = 2;
    int BOTTOM = 3;
    int RIGHT = 4;
    int NORTH = 1;
    int NORTH_EAST = 2;
    int EAST = 3;
    int SOUTH_EAST = 4;
    int SOUTH = 5;
    int SOUTH_WEST = 6;
    int WEST = 7;
    int NORTH_WEST = 8;
    int HORIZONTAL = 0;
    int VERTICAL = 1;
    int LEADING = 10;
    int TRAILING = 11;
    int NEXT = 12;
    int PREVIOUS = 13;
}
"""

FILES[SW + "SwingWorker.java"] = """package javax.swing;
/** Minimal javax.swing.SwingWorker. */
public abstract class SwingWorker<T, V> implements java.util.concurrent.Future<T>, Runnable {
    public static final int PENDING = 0;
    public static final int STARTED = 1;
    public static final int DONE = 2;
    protected SwingWorker() {}
    protected abstract T doInBackground() throws Exception;
    public final void execute() { run(); }
    public void run() {
        try { doInBackground(); } catch (Exception ignored) {}
        done();
    }
    protected void done() {}
    protected void process(java.util.List<V> chunks) {}
    protected final void publish(V... chunks) {}
    public final T get() throws InterruptedException, java.util.concurrent.ExecutionException { return null; }
    public final T get(long timeout, java.util.concurrent.TimeUnit unit)
            throws InterruptedException, java.util.concurrent.ExecutionException, java.util.concurrent.TimeoutException { return null; }
    public final boolean cancel(boolean mayInterruptIfRunning) { return false; }
    public final boolean isCancelled() { return false; }
    public final boolean isDone() { return true; }
    public final int getState() { return DONE; }
    public final int getProgress() { return 0; }
    protected final void setProgress(int progress) {}
    public final void addPropertyChangeListener(java.beans.PropertyChangeListener l) {}
    public final void removePropertyChangeListener(java.beans.PropertyChangeListener l) {}
    public final void firePropertyChange(String name, Object oldV, Object newV) {}
}
"""

FILES[SW + "event/ChangeEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.ChangeEvent. */
public class ChangeEvent extends java.util.EventObject {
    public ChangeEvent(Object source) { super(source); }
}
"""

FILES[SW + "event/ChangeListener.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.ChangeListener. */
public interface ChangeListener extends java.util.EventListener {
    void stateChanged(ChangeEvent e);
}
"""

FILES[SW + "event/AncestorListener.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.AncestorListener. */
public interface AncestorListener extends java.util.EventListener {
    void ancestorAdded(AncestorEvent event);
    void ancestorRemoved(AncestorEvent event);
    void ancestorMoved(AncestorEvent event);
}
"""

FILES[SW + "event/AncestorEvent.java"] = """package javax.swing.event;
import javax.swing.JComponent;
/** Minimal javax.swing.event.AncestorEvent. */
public class AncestorEvent extends java.util.EventObject {
    public static final int ANCESTOR_ADDED = 1;
    public static final int ANCESTOR_REMOVED = 2;
    public static final int ANCESTOR_MOVED = 3;
    protected int id;
    protected JComponent ancestor, ancestorParent;
    public AncestorEvent(JComponent source, int id, JComponent ancestor, JComponent ancestorParent) {
        super(source); this.id = id; this.ancestor = ancestor; this.ancestorParent = ancestorParent;
    }
    public int getID() { return id; }
    public JComponent getAncestor() { return ancestor; }
    public JComponent getAncestorParent() { return ancestorParent; }
    public JComponent getComponent() { return (JComponent) getSource(); }
}
"""

FILES[SW + "border/Border.java"] = """package javax.swing.border;
import java.awt.Component;
import java.awt.Graphics;
import java.awt.Insets;
/** Minimal javax.swing.border.Border. */
public interface Border {
    void paintBorder(Component c, Graphics g, int x, int y, int width, int height);
    Insets getBorderInsets(Component c);
    boolean isBorderOpaque();
}
"""

FILES[SW + "border/EmptyBorder.java"] = """package javax.swing.border;
import java.awt.Component;
import java.awt.Graphics;
import java.awt.Insets;
/** Minimal javax.swing.border.EmptyBorder. */
public class EmptyBorder implements Border, java.io.Serializable {
    protected int top, left, bottom, right;
    public EmptyBorder(int top, int left, int bottom, int right) {
        this.top = top; this.left = left; this.bottom = bottom; this.right = right;
    }
    public EmptyBorder(Insets insets) { this(insets.top, insets.left, insets.bottom, insets.right); }
    public void paintBorder(Component c, Graphics g, int x, int y, int width, int height) {}
    public Insets getBorderInsets(Component c) { return getBorderInsets(); }
    public Insets getBorderInsets() { return new Insets(top, left, bottom, right); }
    public boolean isBorderOpaque() { return false; }
}
"""

FILES["java/awt/dnd/DropTargetAdapter.java"] = """package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetAdapter. */
public abstract class DropTargetAdapter implements DropTargetListener {
    public void dragEnter(DropTargetDragEvent dtde) {}
    public void dragOver(DropTargetDragEvent dtde) {}
    public void dropActionChanged(DropTargetDragEvent dtde) {}
    public void dragExit(DropTargetEvent dte) {}
    public void drop(DropTargetDropEvent dtde) {}
}
"""

FILES["java/awt/dnd/DropTarget.java"] = """package java.awt.dnd;
/** Minimal java.awt.dnd.DropTarget. */
public class DropTarget implements java.io.Serializable {
    public DropTarget() {}
    public DropTarget(java.awt.Component comp, DropTargetListener dtl) {}
    public DropTarget(java.awt.Component comp, int ops, DropTargetListener dtl) {}
    public DropTarget(java.awt.Component comp, int ops, DropTargetListener dtl, boolean active) {}
    public DropTarget(java.awt.Component comp, int ops, DropTargetListener dtl, boolean active, java.awt.datatransfer.FlavorMap fm) {}
    public void setComponent(java.awt.Component comp) {}
    public java.awt.Component getComponent() { return null; }
    public void setDefaultActions(int ops) {}
    public int getDefaultActions() { return 0; }
    public void setActive(boolean isActive) {}
    public boolean isActive() { return false; }
    public void addDropTargetListener(DropTargetListener dtl) {}
    public void removeDropTargetListener(DropTargetListener dtl) {}
}
"""

FILES["java/awt/dnd/DropTargetListener.java"] = """package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetListener. */
public interface DropTargetListener extends java.util.EventListener {
    void dragEnter(DropTargetDragEvent dtde);
    void dragOver(DropTargetDragEvent dtde);
    void dropActionChanged(DropTargetDragEvent dtde);
    void dragExit(DropTargetEvent dte);
    void drop(DropTargetDropEvent dtde);
}
"""

FILES["java/awt/dnd/DropTargetEvent.java"] = """package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetEvent. */
public class DropTargetEvent extends java.util.EventObject {
    protected DropTargetContext context;
    public DropTargetEvent(DropTargetContext context) { super(context.getDropTarget()); this.context = context; }
    public DropTargetContext getDropTargetContext() { return context; }
}
"""

FILES["java/awt/dnd/DropTargetContext.java"] = """package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetContext. */
public class DropTargetContext implements java.io.Serializable {
    public DropTarget getDropTarget() { return null; }
    public java.awt.Component getComponent() { return null; }
    public void addNotify(java.awt.peer.DropTargetPeer dtp) {}
    public void removeNotify() {}
    protected void setDropTargetContextPeer(java.awt.peer.DropTargetPeer dtp) {}
}
"""

FILES["java/awt/dnd/DropTargetDragEvent.java"] = """package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetDragEvent. */
public class DropTargetDragEvent extends DropTargetEvent {
    public DropTargetDragEvent(DropTargetContext context, java.awt.Point location, int dropAction, int srcActions) {
        super(context);
    }
    public java.awt.Point getLocation() { return new java.awt.Point(0, 0); }
    public int getDropAction() { return 0; }
    public int getSourceActions() { return 0; }
    public void acceptDrag(int dragOperation) {}
    public void rejectDrag() {}
}
"""

FILES["java/awt/dnd/DropTargetDropEvent.java"] = """package java.awt.dnd;
/** Minimal java.awt.dnd.DropTargetDropEvent. */
public class DropTargetDropEvent extends DropTargetEvent {
    public DropTargetDropEvent(DropTargetContext context, java.awt.Point location, int dropAction, int srcActions) {
        super(context);
    }
    public java.awt.Point getLocation() { return new java.awt.Point(0, 0); }
    public int getDropAction() { return 0; }
    public int getSourceActions() { return 0; }
    public boolean isLocalTransfer() { return false; }
    public java.awt.datatransfer.Transferable getTransferable() { return null; }
    public void acceptDrop(int dropAction) {}
    public void rejectDrop() {}
    public void dropComplete(boolean success) {}
}
"""

FILES["java/awt/peer/DropTargetPeer.java"] = """package java.awt.peer;
/** Minimal java.awt.peer.DropTargetPeer. */
public interface DropTargetPeer {
    void addDropTarget(java.awt.dnd.DropTarget dt);
    void removeDropTarget(java.awt.dnd.DropTarget dt);
}
"""

def main():
    for rel, src in FILES.items():
        path = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        print("wrote", rel)
    print(f"{len(FILES)} files")

if __name__ == "__main__":
    main()
