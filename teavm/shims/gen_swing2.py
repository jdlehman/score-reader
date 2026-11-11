#!/usr/bin/env python3
"""Generate the second batch of headless Swing/AWT stubs (JPanel, text
components, scroll/tab/split panes, SwingPropertyChangeSupport, AWT
Button/Label/KeyboardFocusManager). Same contract as gen_awt.py: no-op
stubs so TeaVM can compile GUI code it never runs.
Run from teavm/ :  python3 shims/gen_swing2.py
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
SW = "javax/swing/"
FILES = {}

FILES["java/awt/AWTKeyStroke.java"] = """package java.awt;
/** Minimal java.awt.AWTKeyStroke. */
public class AWTKeyStroke implements java.io.Serializable {
    protected int keyCode, modifiers;
    protected char keyChar;
    protected boolean onKeyRelease;
    protected AWTKeyStroke() {}
    protected AWTKeyStroke(int keyCode, int modifiers, boolean onKeyRelease) {
        this.keyCode = keyCode; this.modifiers = modifiers; this.onKeyRelease = onKeyRelease;
    }
    public static AWTKeyStroke getAWTKeyStroke(int keyCode, int modifiers, boolean onKeyRelease) {
        return new AWTKeyStroke(keyCode, modifiers, onKeyRelease);
    }
    public static AWTKeyStroke getAWTKeyStroke(int keyCode, int modifiers) {
        return new AWTKeyStroke(keyCode, modifiers, false);
    }
    public static AWTKeyStroke getAWTKeyStroke(char keyChar) {
        AWTKeyStroke k = new AWTKeyStroke();
        k.keyChar = keyChar;
        return k;
    }
    public static AWTKeyStroke getAWTKeyStroke(String s) { return new AWTKeyStroke(); }
    public int getKeyCode() { return keyCode; }
    public char getKeyChar() { return keyChar; }
    public int getModifiers() { return modifiers; }
    public boolean isOnKeyRelease() { return onKeyRelease; }
}
"""

FILES["java/awt/Button.java"] = """package java.awt;
import java.awt.event.*;
/** Minimal java.awt.Button. */
public class Button extends Component {
    protected String label;
    protected String actionCommand;
    public Button() {}
    public Button(String label) { this.label = label; }
    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public String getActionCommand() { return actionCommand; }
    public void setActionCommand(String command) { actionCommand = command; }
    public void addActionListener(ActionListener l) {}
    public void removeActionListener(ActionListener l) {}
    public ActionListener[] getActionListeners() { return new ActionListener[0]; }
}
"""

FILES["java/awt/Label.java"] = """package java.awt;
/** Minimal java.awt.Label. */
public class Label extends Component {
    public static final int LEFT = 0;
    public static final int CENTER = 1;
    public static final int RIGHT = 2;
    protected String text;
    protected int alignment = LEFT;
    public Label() {}
    public Label(String text) { this.text = text; }
    public Label(String text, int alignment) { this.text = text; this.alignment = alignment; }
    public String getText() { return text; }
    public void setText(String text) { this.text = text; }
    public int getAlignment() { return alignment; }
    public void setAlignment(int alignment) { this.alignment = alignment; }
}
"""

FILES["java/awt/KeyboardFocusManager.java"] = """package java.awt;
import java.beans.PropertyChangeListener;
/** Minimal java.awt.KeyboardFocusManager. */
public abstract class KeyboardFocusManager implements java.awt.event.KeyEventDispatcher, java.awt.event.KeyEventPostProcessor {
    protected KeyboardFocusManager() {}
    public static KeyboardFocusManager getCurrentKeyboardFocusManager() { return null; }
    public static void setCurrentKeyboardFocusManager(KeyboardFocusManager m) {}
    public Window getActiveWindow() { return null; }
    public Window getFocusedWindow() { return null; }
    public Component getFocusOwner() { return null; }
    public Component getPermanentFocusOwner() { return null; }
    public void clearGlobalFocusOwner() {}
    public void clearFocusOwner() {}
    public void focusNextComponent(Component c) {}
    public void focusPreviousComponent(Component c) {}
    public void upFocusCycle(Component c) {}
    public void downFocusCycle() {}
    public boolean dispatchEvent(java.awt.AWTEvent e) { return false; }
    public boolean dispatchKeyEvent(java.awt.event.KeyEvent e) { return false; }
    public boolean postProcessKeyEvent(java.awt.event.KeyEvent e) { return false; }
    public void addPropertyChangeListener(PropertyChangeListener l) {}
    public void removePropertyChangeListener(PropertyChangeListener l) {}
    public void addPropertyChangeListener(String name, PropertyChangeListener l) {}
    public void removePropertyChangeListener(String name, PropertyChangeListener l) {}
    public void addKeyEventDispatcher(java.awt.event.KeyEventDispatcher d) {}
    public void removeKeyEventDispatcher(java.awt.event.KeyEventDispatcher d) {}
    public void addKeyEventPostProcessor(java.awt.event.KeyEventPostProcessor p) {}
    public void removeKeyEventPostProcessor(java.awt.event.KeyEventPostProcessor p) {}
}
"""

FILES["java/awt/event/KeyEventDispatcher.java"] = """package java.awt.event;
/** Minimal java.awt.event.KeyEventDispatcher. */
public interface KeyEventDispatcher {
    boolean dispatchKeyEvent(KeyEvent e);
}
"""

FILES["java/awt/event/KeyEventPostProcessor.java"] = """package java.awt.event;
/** Minimal java.awt.event.KeyEventPostProcessor. */
public interface KeyEventPostProcessor {
    boolean postProcessKeyEvent(KeyEvent e);
}
"""

FILES[SW + "JPanel.java"] = """package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JPanel. */
public class JPanel extends JComponent {
    public JPanel() {}
    public JPanel(LayoutManager layout) { setLayout(layout); }
    public JPanel(LayoutManager layout, boolean isDoubleBuffered) { setLayout(layout); }
    public JPanel(boolean isDoubleBuffered) {}
}
"""

FILES[SW + "text/JTextComponent.java"] = """package javax.swing.text;
import javax.swing.*;
import java.awt.*;
/** Minimal javax.swing.text.JTextComponent. */
public abstract class JTextComponent extends JComponent {
    protected String text = "";
    protected boolean editable = true;
    public String getText() { return text; }
    public void setText(String t) { text = t == null ? "" : t; }
    public String getText(int offs, int len) throws BadLocationException { return text.substring(offs, offs + len); }
    public boolean isEditable() { return editable; }
    public void setEditable(boolean b) { editable = b; }
    public Document getDocument() { return null; }
    public void setDocument(Document doc) {}
    public int getCaretPosition() { return 0; }
    public void setCaretPosition(int p) {}
    public int getSelectionStart() { return 0; }
    public int getSelectionEnd() { return 0; }
    public String getSelectedText() { return null; }
    public void selectAll() {}
    public void select(int start, int end) {}
    public void setSelectionStart(int s) {}
    public void setSelectionEnd(int e) {}
    public void replaceSelection(String content) {}
    public void moveCaretPosition(int pos) {}
    public void setCaretColor(Color c) {}
    public Color getCaretColor() { return null; }
    public void setSelectionColor(Color c) {}
    public Color getSelectionColor() { return null; }
    public void setSelectedTextColor(Color c) {}
    public Color getSelectedTextColor() { return null; }
    public void setDisabledTextColor(Color c) {}
    public Color getDisabledTextColor() { return null; }
    public void setMargin(Insets m) {}
    public Insets getMargin() { return new Insets(0, 0, 0, 0); }
    public void addCaretListener(javax.swing.event.CaretListener l) {}
    public void removeCaretListener(javax.swing.event.CaretListener l) {}
    public javax.swing.event.CaretListener[] getCaretListeners() { return new javax.swing.event.CaretListener[0]; }
    public void setDragEnabled(boolean b) {}
    public boolean getDragEnabled() { return false; }
    public void setHighlighter(Highlighter h) {}
    public Highlighter getHighlighter() { return null; }
    public void setKeymap(Keymap map) {}
    public Keymap getKeymap() { return null; }
    public static Keymap addKeymap(String name, Keymap parent) { return null; }
    public static Keymap getKeymap(String name) { return null; }
    public static void removeKeymap(String name) {}
    public void setNavigationFilter(NavigationFilter filter) {}
    public NavigationFilter getNavigationFilter() { return null; }
    public void setFocusAccelerator(char key) {}
    public char getFocusAccelerator() { return 0; }
    public void copy() {}
    public void cut() {}
    public void paste() {}
}
"""

FILES[SW + "JTextField.java"] = """package javax.swing;
import java.awt.event.*;
/** Minimal javax.swing.JTextField. */
public class JTextField extends javax.swing.text.JTextComponent {
    protected int columns;
    protected int horizontalAlignment = javax.swing.SwingConstants.LEADING;
    protected String actionCommand;
    public JTextField() {}
    public JTextField(String text) { setText(text); }
    public JTextField(int columns) { this.columns = columns; }
    public JTextField(String text, int columns) { setText(text); this.columns = columns; }
    public JTextField(javax.swing.text.Document doc, String text, int columns) { setText(text); this.columns = columns; }
    public int getColumns() { return columns; }
    public void setColumns(int columns) { this.columns = columns; }
    public int getHorizontalAlignment() { return horizontalAlignment; }
    public void setHorizontalAlignment(int a) { horizontalAlignment = a; }
    public void addActionListener(ActionListener l) {}
    public void removeActionListener(ActionListener l) {}
    public ActionListener[] getActionListeners() { return new ActionListener[0]; }
    public String getActionCommand() { return actionCommand; }
    public void setActionCommand(String command) { actionCommand = command; }
    public void setAction(Action a) {}
    public Action getAction() { return null; }
    public void postActionEvent() {}
}
"""

FILES[SW + "JToggleButton.java"] = """package javax.swing;
/** Minimal javax.swing.JToggleButton. */
public class JToggleButton extends AbstractButton {
    public JToggleButton() {}
    public JToggleButton(String text) { this.text = text; }
    public JToggleButton(Icon icon) { this.icon = icon; }
    public JToggleButton(String text, Icon icon) { this.text = text; this.icon = icon; }
    public JToggleButton(String text, boolean selected) { this.text = text; this.selected = selected; }
    public JToggleButton(Action a) {}
}
"""

FILES[SW + "JCheckBox.java"] = """package javax.swing;
/** Minimal javax.swing.JCheckBox. */
public class JCheckBox extends JToggleButton {
    public JCheckBox() {}
    public JCheckBox(String text) { this.text = text; }
    public JCheckBox(String text, boolean selected) { this.text = text; this.selected = selected; }
    public JCheckBox(Icon icon) { this.icon = icon; }
    public JCheckBox(Icon icon, boolean selected) { this.icon = icon; this.selected = selected; }
    public JCheckBox(String text, Icon icon) { this.text = text; this.icon = icon; }
    public JCheckBox(String text, Icon icon, boolean selected) {
        this.text = text; this.icon = icon; this.selected = selected;
    }
    public JCheckBox(Action a) {}
}
"""

FILES[SW + "JEditorPane.java"] = """package javax.swing;
import javax.swing.text.*;
import java.net.URL;
/** Minimal javax.swing.JEditorPane. */
public class JEditorPane extends JTextComponent {
    protected String contentType = "text/plain";
    public JEditorPane() {}
    public JEditorPane(String type, String text) { contentType = type; setText(text); }
    public JEditorPane(String url) throws java.io.IOException {}
    public JEditorPane(URL url) throws java.io.IOException {}
    public String getContentType() { return contentType; }
    public void setContentType(String type) { contentType = type; }
    public void setPage(String url) throws java.io.IOException {}
    public void setPage(URL url) throws java.io.IOException {}
    public URL getPage() { return null; }
    public void setEditorKit(EditorKit kit) {}
    public EditorKit getEditorKit() { return null; }
    public void addHyperlinkListener(javax.swing.event.HyperlinkListener l) {}
    public void removeHyperlinkListener(javax.swing.event.HyperlinkListener l) {}
    public javax.swing.event.HyperlinkListener[] getHyperlinkListeners() {
        return new javax.swing.event.HyperlinkListener[0];
    }
}
"""

FILES[SW + "JTextPane.java"] = """package javax.swing;
import javax.swing.text.*;
/** Minimal javax.swing.JTextPane. */
public class JTextPane extends JEditorPane {
    public JTextPane() {}
    public JTextPane(StyledDocument doc) { setDocument(doc); }
    public StyledDocument getStyledDocument() { return null; }
    public void setStyledDocument(StyledDocument doc) {}
    public void setLogicalStyle(Style s) {}
    public Style getLogicalStyle() { return null; }
    public void insertComponent(java.awt.Component c) {}
    public void insertIcon(Icon g) {}
    public Style addStyle(String name, Style parent) { return null; }
    public void removeStyle(String name) {}
    public Style getStyle(String name) { return null; }
    public void setParagraphAttributes(AttributeSet attr, boolean replace) {}
    public void setCharacterAttributes(AttributeSet attr, boolean replace) {}
    public AttributeSet getParagraphAttributes() { return null; }
    public AttributeSet getCharacterAttributes() { return null; }
}
"""

FILES[SW + "JScrollPane.java"] = """package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JScrollPane. */
public class JScrollPane extends JComponent {
    public static final int VERTICAL_SCROLLBAR_AS_NEEDED = 20;
    public static final int VERTICAL_SCROLLBAR_NEVER = 21;
    public static final int VERTICAL_SCROLLBAR_ALWAYS = 22;
    public static final int HORIZONTAL_SCROLLBAR_AS_NEEDED = 30;
    public static final int HORIZONTAL_SCROLLBAR_NEVER = 31;
    public static final int HORIZONTAL_SCROLLBAR_ALWAYS = 32;
    protected Component view;
    protected int vsbPolicy = VERTICAL_SCROLLBAR_AS_NEEDED;
    protected int hsbPolicy = HORIZONTAL_SCROLLBAR_AS_NEEDED;
    public JScrollPane() {}
    public JScrollPane(Component view) { this.view = view; }
    public JScrollPane(Component view, int vsbPolicy, int hsbPolicy) {
        this.view = view; this.vsbPolicy = vsbPolicy; this.hsbPolicy = hsbPolicy;
    }
    public JScrollPane(int vsbPolicy, int hsbPolicy) { this.vsbPolicy = vsbPolicy; this.hsbPolicy = hsbPolicy; }
    public void setViewportView(Component view) { this.view = view; }
    public Component getViewportView() { return view; }
    public JViewport getViewport() { return null; }
    public void setViewport(JViewport viewport) {}
    public JScrollBar getVerticalScrollBar() { return null; }
    public JScrollBar getHorizontalScrollBar() { return null; }
    public void setVerticalScrollBar(JScrollBar sb) {}
    public void setHorizontalScrollBar(JScrollBar sb) {}
    public int getVerticalScrollBarPolicy() { return vsbPolicy; }
    public void setVerticalScrollBarPolicy(int p) { vsbPolicy = p; }
    public int getHorizontalScrollBarPolicy() { return hsbPolicy; }
    public void setHorizontalScrollBarPolicy(int p) { hsbPolicy = p; }
    public void setColumnHeaderView(Component view) {}
    public void setRowHeaderView(Component view) {}
    public void setWheelScrollingEnabled(boolean b) {}
    public boolean isWheelScrollingEnabled() { return false; }
}
"""

FILES[SW + "JViewport.java"] = """package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JViewport. */
public class JViewport extends JComponent {
    protected Component view;
    public JViewport() {}
    public void setView(Component view) { this.view = view; }
    public Component getView() { return view; }
    public void setViewPosition(Point p) {}
    public Point getViewPosition() { return new Point(0, 0); }
    public Rectangle getViewRect() { return new Rectangle(0, 0, 0, 0); }
    public Dimension getExtentSize() { return new Dimension(0, 0); }
    public void setExtentSize(Dimension d) {}
    public void setViewSize(Dimension d) {}
    public void scrollRectToVisible(Rectangle r) {}
    public void addChangeListener(javax.swing.event.ChangeListener l) {}
    public void removeChangeListener(javax.swing.event.ChangeListener l) {}
    public void setScrollMode(int mode) {}
    public int getScrollMode() { return 0; }
}
"""

FILES[SW + "JScrollBar.java"] = """package javax.swing;
import javax.swing.event.ChangeListener;
/** Minimal javax.swing.JScrollBar. */
public class JScrollBar extends JComponent implements java.awt.Adjustable {
    public static final int HORIZONTAL = 0;
    public static final int VERTICAL = 1;
    protected int value, minimum, maximum, visibleAmount, orientation;
    protected int unitIncrement = 1, blockIncrement = 10;
    public JScrollBar() { this(VERTICAL, 0, 10, 0, 100); }
    public JScrollBar(int orientation) { this(orientation, 0, 10, 0, 100); }
    public JScrollBar(int orientation, int value, int visible, int minimum, int maximum) {
        this.orientation = orientation; this.value = value; visibleAmount = visible;
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
    public void setValues(int value, int extent, int min, int max) {
        this.value = value; visibleAmount = extent; minimum = min; maximum = max;
    }
    public void addAdjustmentListener(java.awt.event.AdjustmentListener l) {}
    public void removeAdjustmentListener(java.awt.event.AdjustmentListener l) {}
    public java.awt.event.AdjustmentListener[] getAdjustmentListeners() {
        return new java.awt.event.AdjustmentListener[0];
    }
    public void addChangeListener(ChangeListener l) {}
    public void removeChangeListener(ChangeListener l) {}
    public javax.swing.BoundedRangeModel getModel() { return null; }
    public void setModel(javax.swing.BoundedRangeModel model) {}
}
"""

FILES[SW + "JSplitPane.java"] = """package javax.swing;
import java.awt.*;
/** Minimal javax.swing.JSplitPane. */
public class JSplitPane extends JComponent {
    public static final int VERTICAL_SPLIT = 0;
    public static final int HORIZONTAL_SPLIT = 1;
    protected Component left, right;
    protected int orientation = HORIZONTAL_SPLIT;
    protected int dividerLocation = -1;
    protected int dividerSize = 10;
    public JSplitPane() {}
    public JSplitPane(int orientation) { this.orientation = orientation; }
    public JSplitPane(int orientation, Component left, Component right) {
        this.orientation = orientation; this.left = left; this.right = right;
    }
    public JSplitPane(int orientation, boolean continuousLayout, Component left, Component right) {
        this.orientation = orientation; this.left = left; this.right = right;
    }
    public void setLeftComponent(Component c) { left = c; }
    public Component getLeftComponent() { return left; }
    public void setRightComponent(Component c) { right = c; }
    public Component getRightComponent() { return right; }
    public void setTopComponent(Component c) { left = c; }
    public Component getTopComponent() { return left; }
    public void setBottomComponent(Component c) { right = c; }
    public Component getBottomComponent() { return right; }
    public int getOrientation() { return orientation; }
    public void setOrientation(int o) { orientation = o; }
    public int getDividerLocation() { return dividerLocation; }
    public void setDividerLocation(int loc) { dividerLocation = loc; }
    public void setDividerLocation(double proportional) {}
    public int getDividerSize() { return dividerSize; }
    public void setDividerSize(int size) { dividerSize = size; }
    public void setOneTouchExpandable(boolean b) {}
    public boolean isOneTouchExpandable() { return false; }
    public void setResizeWeight(double w) {}
    public double getResizeWeight() { return 0; }
    public void setContinuousLayout(boolean b) {}
    public boolean isContinuousLayout() { return false; }
    public void setLastDividerLocation(int loc) {}
    public int getLastDividerLocation() { return -1; }
    public void resetToPreferredSizes() {}
}
"""

FILES[SW + "BoundedRangeModel.java"] = """package javax.swing;
import javax.swing.event.ChangeListener;
/** Minimal javax.swing.BoundedRangeModel. */
public interface BoundedRangeModel {
    int getMinimum();
    void setMinimum(int newMinimum);
    int getMaximum();
    void setMaximum(int newMaximum);
    int getValue();
    void setValue(int newValue);
    void setValueIsAdjusting(boolean b);
    boolean getValueIsAdjusting();
    int getExtent();
    void setExtent(int newExtent);
    void setRangeProperties(int value, int extent, int min, int max, boolean adjusting);
    void addChangeListener(ChangeListener l);
    void removeChangeListener(ChangeListener l);
}
"""

FILES[SW + "event/SwingPropertyChangeSupport.java"] = """package javax.swing.event;
import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeListener;
import java.beans.PropertyChangeSupport;
/** Minimal javax.swing.event.SwingPropertyChangeSupport. */
public class SwingPropertyChangeSupport extends PropertyChangeSupport {
    protected boolean notifyOnEDT;
    public SwingPropertyChangeSupport(Object sourceBean) { super(sourceBean); }
    public SwingPropertyChangeSupport(Object sourceBean, boolean notifyOnEDT) {
        super(sourceBean); this.notifyOnEDT = notifyOnEDT;
    }
    public boolean isNotifyOnEDT() { return notifyOnEDT; }
    @Override public void firePropertyChange(String propertyName, Object oldValue, Object newValue) {}
    @Override public void firePropertyChange(String propertyName, boolean oldValue, boolean newValue) {}
    @Override public void firePropertyChange(String propertyName, int oldValue, int newValue) {}
    @Override public void firePropertyChange(PropertyChangeEvent evt) {}
    public void fireIndexedPropertyChange(String propertyName, int index, Object oldValue, Object newValue) {}
    public void fireIndexedPropertyChange(String propertyName, int index, boolean oldValue, boolean newValue) {}
    public void fireIndexedPropertyChange(String propertyName, int index, int oldValue, int newValue) {}
}
"""

FILES[SW + "event/CaretListener.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.CaretListener. */
public interface CaretListener extends java.util.EventListener {
    void caretUpdate(CaretEvent e);
}
"""

FILES[SW + "event/CaretEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.CaretEvent. */
public abstract class CaretEvent extends java.util.EventObject {
    public CaretEvent(Object source) { super(source); }
    public abstract int getDot();
    public abstract int getMark();
}
"""

FILES[SW + "event/HyperlinkListener.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.HyperlinkListener. */
public interface HyperlinkListener extends java.util.EventListener {
    void hyperlinkUpdate(HyperlinkEvent e);
}
"""

FILES[SW + "event/HyperlinkEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.HyperlinkEvent. */
public class HyperlinkEvent extends java.util.EventObject {
    public enum EventType { ACTIVATED, ENTERED, EXITED }
    protected EventType type;
    protected java.net.URL url;
    protected String desc;
    public HyperlinkEvent(Object source, EventType type, java.net.URL url) { super(source); this.type = type; this.url = url; }
    public HyperlinkEvent(Object source, EventType type, java.net.URL url, String desc) {
        super(source); this.type = type; this.url = url; this.desc = desc;
    }
    public EventType getEventType() { return type; }
    public String getDescription() { return desc; }
    public java.net.URL getURL() { return url; }
}
"""

FILES[SW + "text/Document.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.Document. */
public interface Document {
    int getLength();
    void addDocumentListener(javax.swing.event.DocumentListener listener);
    void removeDocumentListener(javax.swing.event.DocumentListener listener);
    void addUndoableEditListener(javax.swing.event.UndoableEditListener listener);
    void removeUndoableEditListener(javax.swing.event.UndoableEditListener listener);
    Object getProperty(Object key);
    void putProperty(Object key, Object value);
    void remove(int offs, int len) throws BadLocationException;
    void insertString(int offset, String str, AttributeSet a) throws BadLocationException;
    String getText(int offset, int length) throws BadLocationException;
    void getText(int offset, int length, Segment txt) throws BadLocationException;
    Position getStartPosition();
    Position getEndPosition();
    Position createPosition(int offs) throws BadLocationException;
    Element[] getRootElements();
    Element getDefaultRootElement();
    void render(Runnable r);
}
"""

FILES[SW + "text/BadLocationException.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.BadLocationException. */
public class BadLocationException extends Exception {
    protected int offs;
    public BadLocationException(String s, int offs) { super(s); this.offs = offs; }
    public int offsetRequested() { return offs; }
}
"""

FILES[SW + "text/AttributeSet.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.AttributeSet. */
public interface AttributeSet {
    int getAttributeCount();
    boolean isDefined(Object attrName);
    boolean isEqual(AttributeSet attr);
    AttributeSet copyAttributes();
    Object getAttribute(Object key);
    java.util.Enumeration<?> getAttributeNames();
    boolean containsAttribute(Object name, Object value);
    boolean containsAttributes(AttributeSet attributes);
    AttributeSet getResolveParent();
    interface CharacterAttribute {}
    interface ColorAttribute {}
    interface FontAttribute {}
    interface ParagraphAttribute {}
}
"""

FILES[SW + "text/StyledDocument.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.StyledDocument. */
public interface StyledDocument extends Document {
    Style addStyle(String name, Style parent);
    void removeStyle(String name);
    Style getStyle(String name);
    void setLogicalStyle(int pos, Style s);
    Style getLogicalStyle(int p);
    void setParagraphAttributes(int offset, int length, AttributeSet s, boolean replace);
    void setCharacterAttributes(int offset, int length, AttributeSet s, boolean replace);
    Element getParagraphElement(int pos);
    Element getCharacterElement(int pos);
    java.awt.Color getForeground(AttributeSet attr);
    java.awt.Color getBackground(AttributeSet attr);
    java.awt.Font getFont(AttributeSet attr);
}
"""

FILES[SW + "text/Style.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.Style. */
public interface Style extends MutableAttributeSet {
    String getName();
    void addChangeListener(javax.swing.event.ChangeListener l);
    void removeChangeListener(javax.swing.event.ChangeListener l);
}
"""

FILES[SW + "text/MutableAttributeSet.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.MutableAttributeSet. */
public interface MutableAttributeSet extends AttributeSet {
    void addAttribute(Object name, Object value);
    void addAttributes(AttributeSet attributes);
    void removeAttribute(Object name);
    void removeAttributes(AttributeSet attributes);
    void removeAttributes(java.util.Enumeration<?> names);
    void setResolveParent(AttributeSet parent);
}
"""

FILES[SW + "text/Element.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.Element. */
public interface Element {
    Document getDocument();
    Element getParentElement();
    String getName();
    AttributeSet getAttributes();
    int getStartOffset();
    int getEndOffset();
    int getElementIndex(int offset);
    int getElementCount();
    Element getElement(int index);
    boolean isLeaf();
}
"""

FILES[SW + "text/Position.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.Position. */
public interface Position {
    int getOffset();
    interface Bias {
        Bias Forward = new Bias() {};
        Bias Backward = new Bias() {};
    }
}
"""

FILES[SW + "text/Segment.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.Segment. */
public class Segment implements java.text.CharacterIterator, Cloneable {
    public char[] array;
    public int offset;
    public int count;
    public boolean partialReturn;
    public Segment() {}
    public Segment(char[] array, int offset, int count) { this.array = array; this.offset = offset; this.count = count; }
    public char first() { return count == 0 ? DONE : array[offset]; }
    public char last() { return count == 0 ? DONE : array[offset + count - 1]; }
    public char current() { return DONE; }
    public char next() { return DONE; }
    public char previous() { return DONE; }
    public char setIndex(int position) { return DONE; }
    public int getBeginIndex() { return offset; }
    public int getEndIndex() { return offset + count; }
    public int getIndex() { return offset; }
    public Object clone() { return this; }
}
"""

FILES[SW + "text/Highlighter.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.Highlighter. */
public interface Highlighter {
    void install(javax.swing.text.JTextComponent c);
    void deinstall(javax.swing.text.JTextComponent c);
    void paint(java.awt.Graphics g);
    Object addHighlight(int p0, int p1, HighlightPainter p) throws BadLocationException;
    void removeHighlight(Object tag);
    void removeAllHighlights();
    void changeHighlight(Object tag, int p0, int p1) throws BadLocationException;
    Highlight[] getHighlights();
    interface Highlight {
        int getStartOffset();
        int getEndOffset();
        HighlightPainter getPainter();
    }
    interface HighlightPainter {
        void paint(java.awt.Graphics g, int p0, int p1, java.awt.Shape bounds, JTextComponent c);
    }
}
"""

FILES[SW + "text/Keymap.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.Keymap. */
public interface Keymap {
    String getName();
    javax.swing.Action getDefaultAction();
    void setDefaultAction(javax.swing.Action a);
    javax.swing.Action getAction(javax.swing.KeyStroke key);
    javax.swing.KeyStroke[] getBoundKeyStrokes();
    javax.swing.Action[] getBoundActions();
    javax.swing.KeyStroke[] getKeyStrokesForAction(javax.swing.Action a);
    boolean isLocallyDefined(javax.swing.KeyStroke key);
    void addActionForKeyStroke(javax.swing.KeyStroke key, javax.swing.Action a);
    void removeKeyStrokeBinding(javax.swing.KeyStroke keys);
    void removeBindings();
    Keymap getResolveParent();
    void setResolveParent(Keymap parent);
}
"""

FILES[SW + "text/NavigationFilter.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.NavigationFilter. */
public abstract class NavigationFilter {
    public void setDot(NavigationFilter.FilterBypass fb, int dot, Position.Bias bias) { fb.setDot(dot, bias); }
    public void moveDot(NavigationFilter.FilterBypass fb, int dot, Position.Bias bias) { fb.moveDot(dot, bias); }
    public int getNextVisualPositionFrom(JTextComponent text, int pos, Position.Bias bias, int direction, Position.Bias[] biasRet) throws BadLocationException { return pos; }
    public abstract static class FilterBypass {
        public abstract void setDot(int dot, Position.Bias bias);
        public abstract void moveDot(int dot, Position.Bias bias);
    }
}
"""

FILES[SW + "text/EditorKit.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.EditorKit. */
public abstract class EditorKit implements Cloneable, java.io.Serializable {
    public Object clone() { return this; }
    public abstract String getContentType();
    public abstract ViewFactory getViewFactory();
    public abstract javax.swing.Action[] getActions();
    public abstract Caret createCaret();
    public abstract Document createDefaultDocument();
    public abstract void read(java.io.InputStream in, Document doc, int pos) throws java.io.IOException, BadLocationException;
    public abstract void write(java.io.OutputStream out, Document doc, int pos, int len) throws java.io.IOException, BadLocationException;
    public abstract void read(java.io.Reader in, Document doc, int pos) throws java.io.IOException, BadLocationException;
    public abstract void write(java.io.Writer out, Document doc, int pos, int len) throws java.io.IOException, BadLocationException;
    public void install(JTextComponent c) {}
    public void deinstall(JTextComponent c) {}
}
"""

FILES[SW + "text/ViewFactory.java"] = """package javax.swing.text;
/** Minimal javax.swing.text.ViewFactory. */
public interface ViewFactory {
    View create(Element elem);
}
"""

FILES[SW + "text/View.java"] = """package javax.swing.text;
import java.awt.Container;
/** Minimal javax.swing.text.View. */
public abstract class View {
    public View(Element elem) {}
    public Element getElement() { return null; }
    public abstract float getPreferredSpan(int axis);
    public abstract void paint(java.awt.Graphics g, java.awt.Shape allocation);
    public abstract java.awt.Shape modelToView(int pos, java.awt.Shape a, Position.Bias b) throws BadLocationException;
    public abstract int viewToModel(float x, float y, java.awt.Shape a, Position.Bias[] biasReturn);
    public Container getContainer() { return null; }
    public View getParent() { return null; }
    public void setParent(View parent) {}
    public int getViewCount() { return 0; }
    public View getView(int n) { return null; }
    public void replace(int offset, int length, View[] views) {}
    public float getMinimumSpan(int axis) { return 0; }
    public float getMaximumSpan(int axis) { return 0; }
    public float getAlignment(int axis) { return 0; }
    public void setSize(float width, float height) {}
    public void preferenceChanged(View child, boolean width, boolean height) {}
    public int getResizeWeight(int axis) { return 0; }
    public void insert(int offs, View view) {}
    public void remove(int i) {}
    public void removeAll() {}
    public void append(View v) {}
    public int getViewIndex(int pos, Position.Bias b) { return -1; }
    public int getNextVisualPositionFrom(int pos, Position.Bias b, java.awt.Shape a, int direction, Position.Bias[] biasRet) throws BadLocationException { return pos; }
    public int getViewIndex(float x, float y, java.awt.Shape allocation) { return -1; }
    public Document getDocument() { return null; }
    public int getStartOffset() { return 0; }
    public int getEndOffset() { return 0; }
}
"""

FILES[SW + "event/DocumentListener.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.DocumentListener. */
public interface DocumentListener extends java.util.EventListener {
    void insertUpdate(DocumentEvent e);
    void removeUpdate(DocumentEvent e);
    void changedUpdate(DocumentEvent e);
}
"""

FILES[SW + "event/DocumentEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.DocumentEvent. */
public interface DocumentEvent {
    int getOffset();
    int getLength();
    javax.swing.text.Document getDocument();
    EventType getType();
    ElementChange getChange(javax.swing.text.Element elem);
    enum EventType { INSERT, REMOVE, CHANGE }
    interface ElementChange {
        javax.swing.text.Element getElement();
        int getIndex();
        javax.swing.text.Element[] getChildrenRemoved();
        javax.swing.text.Element[] getChildrenAdded();
    }
}
"""

FILES[SW + "event/UndoableEditListener.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.UndoableEditListener. */
public interface UndoableEditListener extends java.util.EventListener {
    void undoableEditHappened(UndoableEditEvent e);
}
"""

FILES[SW + "event/UndoableEditEvent.java"] = """package javax.swing.event;
/** Minimal javax.swing.event.UndoableEditEvent. */
public class UndoableEditEvent extends java.util.EventObject {
    protected javax.swing.undo.UndoableEdit edit;
    public UndoableEditEvent(Object source, javax.swing.undo.UndoableEdit edit) { super(source); this.edit = edit; }
    public javax.swing.undo.UndoableEdit getEdit() { return edit; }
}
"""

FILES[SW + "undo/UndoableEdit.java"] = """package javax.swing.undo;
/** Minimal javax.swing.undo.UndoableEdit. */
public interface UndoableEdit {
    void undo() throws CannotUndoException;
    boolean canUndo();
    void redo() throws CannotRedoException;
    boolean canRedo();
    void die();
    boolean addEdit(UndoableEdit anEdit);
    boolean replaceEdit(UndoableEdit anEdit);
    boolean isSignificant();
    String getPresentationName();
    String getUndoPresentationName();
    String getRedoPresentationName();
}
"""

FILES[SW + "undo/CannotUndoException.java"] = """package javax.swing.undo;
/** Minimal javax.swing.undo.CannotUndoException. */
public class CannotUndoException extends RuntimeException {}
"""

FILES[SW + "undo/CannotRedoException.java"] = """package javax.swing.undo;
/** Minimal javax.swing.undo.CannotRedoException. */
public class CannotRedoException extends RuntimeException {}
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
