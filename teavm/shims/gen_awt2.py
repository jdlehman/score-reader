#!/usr/bin/env python3
"""Generate round-6 AWT stub sources (widgets, FontMetrics, geom, SystemColor).

Round-6 follow-up to gen_awt.py: these classes were unblocked for analysis
once Frame/JPanel shims landed (round 4), and ij + Audiveris UI code
references them. Same conventions as gen_awt.py: minimal headless stubs,
only the API surface referenced by ij / Audiveris / appframework.
ROOT is shims/src.
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")

FILES = {}

FILES["java/awt/TextComponent.java"] = """package java.awt;
import java.awt.event.TextListener;
/** Minimal java.awt.TextComponent. */
public class TextComponent extends Component {
    protected String text = "";
    protected boolean editable = true;
    protected int selectionStart, selectionEnd;
    public String getText() { return text; }
    public void setText(String t) { text = (t == null) ? "" : t; }
    public boolean isEditable() { return editable; }
    public void setEditable(boolean b) { editable = b; }
    public String getSelectedText() { return ""; }
    public void select(int start, int end) { selectionStart = start; selectionEnd = end; }
    public void selectAll() {}
    public int getSelectionStart() { return selectionStart; }
    public int getSelectionEnd() { return selectionEnd; }
    public int getCaretPosition() { return 0; }
    public void setCaretPosition(int p) {}
    public void addTextListener(TextListener l) {}
    public void removeTextListener(TextListener l) {}
}
"""

FILES["java/awt/TextArea.java"] = """package java.awt;
/** Minimal java.awt.TextArea. */
public class TextArea extends TextComponent {
    public static final int SCROLLBARS_BOTH = 0;
    public static final int SCROLLBARS_VERTICAL_ONLY = 1;
    public static final int SCROLLBARS_HORIZONTAL_ONLY = 2;
    public static final int SCROLLBARS_NONE = 3;
    private int rows, columns;
    public TextArea() {}
    public TextArea(String text) { setText(text); }
    public TextArea(int rows, int columns) { this.rows = rows; this.columns = columns; }
    public TextArea(String text, int rows, int columns) { setText(text); this.rows = rows; this.columns = columns; }
    public TextArea(String text, int rows, int columns, int scrollbars) { setText(text); this.rows = rows; this.columns = columns; }
    public int getRows() { return rows; }
    public void setRows(int rows) { this.rows = rows; }
    public int getColumns() { return columns; }
    public void setColumns(int columns) { this.columns = columns; }
    public int getScrollbarVisibility() { return SCROLLBARS_BOTH; }
    public void append(String str) { setText(getText() + str); }
    public void appendText(String str) { append(str); }
    public void insert(String str, int pos) {}
    public void insertText(String str, int pos) {}
    public void replaceRange(String str, int start, int end) {}
    public void replaceText(String str, int start, int end) {}
}
"""

FILES["java/awt/TextField.java"] = """package java.awt;
/** Minimal java.awt.TextField. */
public class TextField extends TextComponent {
    private int columns;
    private char echoChar;
    public TextField() {}
    public TextField(String text) { setText(text); }
    public TextField(int columns) { this.columns = columns; }
    public TextField(String text, int columns) { setText(text); this.columns = columns; }
    public int getColumns() { return columns; }
    public void setColumns(int columns) { this.columns = columns; }
    public char getEchoChar() { return echoChar; }
    public void setEchoChar(char c) { echoChar = c; }
    public void setEchoCharacter(char c) { echoChar = c; }
    public boolean echoCharIsSet() { return echoChar != 0; }
    public void addActionListener(java.awt.event.ActionListener l) {}
    public void removeActionListener(java.awt.event.ActionListener l) {}
    public java.awt.event.ActionListener[] getActionListeners() { return new java.awt.event.ActionListener[0]; }
    public java.awt.Dimension getPreferredSize(int columns) { return new java.awt.Dimension(0, 0); }
}
"""

FILES["java/awt/Checkbox.java"] = """package java.awt;
import java.awt.event.ItemListener;
/** Minimal java.awt.Checkbox. */
public class Checkbox extends Component implements ItemSelectable {
    private String label = "";
    private boolean state;
    private CheckboxGroup group;
    public Checkbox() {}
    public Checkbox(String label) { this.label = label; }
    public Checkbox(String label, boolean state) { this.label = label; this.state = state; }
    public Checkbox(String label, boolean state, CheckboxGroup group) { this.label = label; this.state = state; this.group = group; }
    public Checkbox(String label, CheckboxGroup group, boolean state) { this.label = label; this.group = group; this.state = state; }
    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public boolean getState() { return state; }
    public void setState(boolean state) { this.state = state; }
    public CheckboxGroup getCheckboxGroup() { return group; }
    public void setCheckboxGroup(CheckboxGroup g) { group = g; }
    public void addItemListener(ItemListener l) {}
    public void removeItemListener(ItemListener l) {}
    public Object[] getSelectedObjects() { return state ? new Object[]{ label } : null; }
}
"""

FILES["java/awt/CheckboxGroup.java"] = """package java.awt;
/** Minimal java.awt.CheckboxGroup. */
public class CheckboxGroup implements java.io.Serializable {
    private Checkbox selected;
    public Checkbox getSelectedCheckbox() { return selected; }
    public void setSelectedCheckbox(Checkbox box) { selected = box; }
    public String toString() { return "CheckboxGroup"; }
}
"""

FILES["java/awt/Choice.java"] = """package java.awt;
import java.awt.event.ItemListener;
/** Minimal java.awt.Choice. */
public class Choice extends Component implements ItemSelectable {
    private final java.util.List<String> items = new java.util.ArrayList<>();
    private int selected;
    public Choice() {}
    public int getItemCount() { return items.size(); }
    public String getItem(int index) { return items.get(index); }
    public void add(String item) { items.add(item); }
    public void addItem(String item) { add(item); }
    public void insert(String item, int index) { items.add(index, item); }
    public void remove(String item) { items.remove(item); }
    public void remove(int index) { items.remove(index); }
    public void removeAll() { items.clear(); }
    public int getSelectedIndex() { return selected; }
    public String getSelectedItem() { return items.isEmpty() ? null : items.get(selected); }
    public void select(int pos) { selected = pos; }
    public void select(String str) { int i = items.indexOf(str); if (i >= 0) selected = i; }
    public void addItemListener(ItemListener l) {}
    public void removeItemListener(ItemListener l) {}
    public Object[] getSelectedObjects() { return items.isEmpty() ? null : new Object[]{ getSelectedItem() }; }
}
"""

FILES["java/awt/FileDialog.java"] = """package java.awt;
import java.io.FilenameFilter;
/** Minimal java.awt.FileDialog. */
public class FileDialog extends Dialog {
    public static final int LOAD = 0;
    public static final int SAVE = 1;
    private int mode = LOAD;
    private String directory, file;
    private FilenameFilter filter;
    private boolean multipleMode;
    public FileDialog(Frame parent) { super(parent); }
    public FileDialog(Frame parent, String title) { super(parent, title); }
    public FileDialog(Frame parent, String title, int mode) { super(parent, title); this.mode = mode; }
    public FileDialog(Dialog parent) { super(parent); }
    public FileDialog(Dialog parent, String title) { super(parent, title); }
    public FileDialog(Dialog parent, String title, int mode) { super(parent, title); this.mode = mode; }
    public int getMode() { return mode; }
    public void setMode(int mode) { this.mode = mode; }
    public String getDirectory() { return directory; }
    public void setDirectory(String dir) { directory = dir; }
    public String getFile() { return file; }
    public void setFile(String file) { this.file = file; }
    public FilenameFilter getFilenameFilter() { return filter; }
    public void setFilenameFilter(FilenameFilter filter) { this.filter = filter; }
    public java.io.File[] getFiles() { return new java.io.File[0]; }
    public boolean isMultipleMode() { return multipleMode; }
    public void setMultipleMode(boolean b) { multipleMode = b; }
}
"""

FILES["java/awt/GridBagConstraints.java"] = """package java.awt;
/** Minimal java.awt.GridBagConstraints (public fields, as in the JDK). */
public class GridBagConstraints implements Cloneable, java.io.Serializable {
    public static final int RELATIVE = -1;
    public static final int REMAINDER = 0;
    public static final int NONE = 0;
    public static final int BOTH = 1;
    public static final int HORIZONTAL = 2;
    public static final int VERTICAL = 3;
    public static final int CENTER = 10;
    public static final int NORTH = 11;
    public static final int NORTHEAST = 12;
    public static final int EAST = 13;
    public static final int SOUTHEAST = 14;
    public static final int SOUTH = 15;
    public static final int SOUTHWEST = 16;
    public static final int WEST = 17;
    public static final int NORTHWEST = 18;
    public static final int PAGE_START = 19;
    public static final int PAGE_END = 20;
    public static final int LINE_START = 21;
    public static final int LINE_END = 22;
    public static final int FIRST_LINE_START = 23;
    public static final int FIRST_LINE_END = 24;
    public static final int LAST_LINE_START = 25;
    public static final int LAST_LINE_END = 26;
    public static final int BASELINE = 0x100;
    public static final int BASELINE_LEADING = 0x200;
    public static final int BASELINE_TRAILING = 0x300;
    public static final int ABOVE_BASELINE = 0x400;
    public static final int ABOVE_BASELINE_LEADING = 0x500;
    public static final int ABOVE_BASELINE_TRAILING = 0x600;
    public static final int BELOW_BASELINE = 0x700;
    public static final int BELOW_BASELINE_LEADING = 0x800;
    public static final int BELOW_BASELINE_TRAILING = 0x900;
    public int gridx = RELATIVE;
    public int gridy = RELATIVE;
    public int gridwidth = 1;
    public int gridheight = 1;
    public double weightx = 0;
    public double weighty = 0;
    public int anchor = CENTER;
    public int fill = NONE;
    public Insets insets = new Insets(0, 0, 0, 0);
    public int ipadx = 0;
    public int ipady = 0;
    public GridBagConstraints() {}
    public GridBagConstraints(int gridx, int gridy, int gridwidth, int gridheight,
            double weightx, double weighty, int anchor, int fill, Insets insets, int ipadx, int ipady) {
        this.gridx = gridx; this.gridy = gridy; this.gridwidth = gridwidth; this.gridheight = gridheight;
        this.weightx = weightx; this.weighty = weighty; this.anchor = anchor; this.fill = fill;
        this.insets = insets; this.ipadx = ipadx; this.ipady = ipady;
    }
    public Object clone() { try { return super.clone(); } catch (CloneNotSupportedException e) { return null; } }
}
"""

FILES["java/awt/GridBagLayout.java"] = """package java.awt;
/** Minimal java.awt.GridBagLayout. */
public class GridBagLayout implements LayoutManager2, java.io.Serializable {
    protected GridBagConstraints defaultConstraints = new GridBagConstraints();
    public GridBagLayout() {}
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
    public GridBagConstraints getConstraints(Component comp) { return new GridBagConstraints(); }
    public void setConstraints(Component comp, GridBagConstraints constraints) {}
    protected GridBagConstraints lookupConstraints(Component comp) { return new GridBagConstraints(); }
    public java.awt.Point getLayoutOrigin() { return new java.awt.Point(0, 0); }
    public int[][] getLayoutDimensions() { return new int[2][0]; }
    public double[][] getLayoutWeights() { return new double[2][0]; }
    public java.awt.Point location(int x, int y) { return new java.awt.Point(0, 0); }
}
"""

FILES["java/awt/FontMetrics.java"] = """package java.awt;
/** Minimal java.awt.FontMetrics (correct package -- the JDK class lives in
 *  java.awt, not java.awt.font). Stub metrics: 8px advance.
 *  Deliberately concrete (the JDK class is abstract) so stubs can
 *  instantiate it directly. */
public class FontMetrics implements java.io.Serializable {
    protected Font font;
    public FontMetrics(Font font) { this.font = font; }
    public Font getFont() { return font; }
    public int getHeight() { return 12; }
    public int getAscent() { return 10; }
    public int getDescent() { return 2; }
    public int getLeading() { return 0; }
    public int getMaxAscent() { return 10; }
    public int getMaxDescent() { return 2; }
    public int getMaxAdvance() { return 8; }
    public int charWidth(int ch) { return 8; }
    public int charWidth(char ch) { return 8; }
    public int stringWidth(String str) { return (str == null) ? 0 : str.length() * 8; }
    public int charsWidth(char[] data, int off, int len) { return len * 8; }
    public int bytesWidth(byte[] data, int off, int len) { return len * 8; }
    public int[] getWidths() { int[] w = new int[256]; java.util.Arrays.fill(w, 8); return w; }
    public boolean hasUniformLineMetrics() { return true; }
    public java.awt.geom.Rectangle2D getStringBounds(String str, java.awt.Graphics context) {
        return new java.awt.geom.Rectangle2D.Double(0, 0, stringWidth(str), getHeight());
    }
    public java.awt.geom.Rectangle2D getStringBounds(char[] chars, int beginIndex, int limit, java.awt.Graphics context) {
        return new java.awt.geom.Rectangle2D.Double(0, 0, (limit - beginIndex) * 8, getHeight());
    }
    public java.awt.geom.Rectangle2D getStringBounds(java.text.CharacterIterator ci, int beginIndex, int limit, java.awt.Graphics context) {
        return new java.awt.geom.Rectangle2D.Double(0, 0, (limit - beginIndex) * 8, getHeight());
    }
}
"""

FILES["java/awt/geom/RoundRectangle2D.java"] = """package java.awt.geom;
/** Minimal java.awt.geom.RoundRectangle2D. */
public abstract class RoundRectangle2D extends RectangularShape {
    public abstract double getArcWidth();
    public abstract double getArcHeight();
    public abstract void setRoundRect(double x, double y, double w, double h, double arcWidth, double arcHeight);
    public void setRoundRect(RoundRectangle2D rr) { setRoundRect(rr.getX(), rr.getY(), rr.getWidth(), rr.getHeight(), rr.getArcWidth(), rr.getArcHeight()); }
    public static class Double extends RoundRectangle2D {
        public double x, y, width, height, arcwidth, archeight;
        public Double() {}
        public Double(double x, double y, double w, double h, double arcWidth, double arcHeight) {
            this.x = x; this.y = y; width = w; height = h; arcwidth = arcWidth; archeight = arcHeight;
        }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public double getWidth() { return width; }
        @Override public double getHeight() { return height; }
        @Override public double getArcWidth() { return arcwidth; }
        @Override public double getArcHeight() { return archeight; }
        @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
        @Override public void setFrame(double x, double y, double w, double h) { this.x = x; this.y = y; width = w; height = h; }
        @Override public void setRoundRect(double x, double y, double w, double h, double arcWidth, double arcHeight) {
            this.x = x; this.y = y; width = w; height = h; arcwidth = arcWidth; archeight = arcHeight;
        }
        @Override public Rectangle2D getBounds2D() { return new Rectangle2D.Double(x, y, width, height); }
    }
    public static class Float extends RoundRectangle2D {
        public float x, y, width, height, arcwidth, archeight;
        public Float() {}
        public Float(float x, float y, float w, float h, float arcWidth, float arcHeight) {
            this.x = x; this.y = y; width = w; height = h; arcwidth = arcWidth; archeight = arcHeight;
        }
        @Override public double getX() { return x; }
        @Override public double getY() { return y; }
        @Override public double getWidth() { return width; }
        @Override public double getHeight() { return height; }
        @Override public double getArcWidth() { return arcwidth; }
        @Override public double getArcHeight() { return archeight; }
        @Override public boolean isEmpty() { return width <= 0 || height <= 0; }
        @Override public void setFrame(double x, double y, double w, double h) { this.x = (float) x; this.y = (float) y; width = (float) w; height = (float) h; }
        @Override public void setRoundRect(double x, double y, double w, double h, double arcWidth, double arcHeight) {
            this.x = (float) x; this.y = (float) y; width = (float) w; height = (float) h;
            arcwidth = (float) arcWidth; archeight = (float) arcHeight;
        }
        @Override public Rectangle2D getBounds2D() { return new Rectangle2D.Float(x, y, width, height); }
    }
}
"""

FILES["java/awt/SystemColor.java"] = """package java.awt;
/** Minimal java.awt.SystemColor. */
public class SystemColor extends Color {
    public static final int DESKTOP = 0;
    public static final int ACTIVE_CAPTION = 1;
    public static final int ACTIVE_CAPTION_TEXT = 2;
    public static final int ACTIVE_CAPTION_BORDER = 3;
    public static final int INACTIVE_CAPTION = 4;
    public static final int INACTIVE_CAPTION_TEXT = 5;
    public static final int INACTIVE_CAPTION_BORDER = 6;
    public static final int WINDOW = 7;
    public static final int WINDOW_BORDER = 8;
    public static final int WINDOW_TEXT = 9;
    public static final int MENU = 10;
    public static final int MENU_TEXT = 11;
    public static final int TEXT = 12;
    public static final int TEXT_TEXT = 13;
    public static final int TEXT_HIGHLIGHT = 14;
    public static final int TEXT_HIGHLIGHT_TEXT = 15;
    public static final int TEXT_INACTIVE_TEXT = 16;
    public static final int CONTROL = 17;
    public static final int CONTROL_TEXT = 18;
    public static final int CONTROL_LT_HIGHLIGHT = 19;
    public static final int CONTROL_HIGHLIGHT = 20;
    public static final int CONTROL_SHADOW = 21;
    public static final int CONTROL_DK_SHADOW = 22;
    public static final int SCROLLBAR = 23;
    public static final int INFO = 24;
    public static final int INFO_TEXT = 25;
    public static final SystemColor desktop = new SystemColor(DESKTOP);
    public static final SystemColor activeCaption = new SystemColor(ACTIVE_CAPTION);
    public static final SystemColor activeCaptionText = new SystemColor(ACTIVE_CAPTION_TEXT);
    public static final SystemColor activeCaptionBorder = new SystemColor(ACTIVE_CAPTION_BORDER);
    public static final SystemColor inactiveCaption = new SystemColor(INACTIVE_CAPTION);
    public static final SystemColor inactiveCaptionText = new SystemColor(INACTIVE_CAPTION_TEXT);
    public static final SystemColor inactiveCaptionBorder = new SystemColor(INACTIVE_CAPTION_BORDER);
    public static final SystemColor window = new SystemColor(WINDOW);
    public static final SystemColor windowBorder = new SystemColor(WINDOW_BORDER);
    public static final SystemColor windowText = new SystemColor(WINDOW_TEXT);
    public static final SystemColor menu = new SystemColor(MENU);
    public static final SystemColor menuText = new SystemColor(MENU_TEXT);
    public static final SystemColor text = new SystemColor(TEXT);
    public static final SystemColor textText = new SystemColor(TEXT_TEXT);
    public static final SystemColor textHighlight = new SystemColor(TEXT_HIGHLIGHT);
    public static final SystemColor textHighlightText = new SystemColor(TEXT_HIGHLIGHT_TEXT);
    public static final SystemColor textInactiveText = new SystemColor(TEXT_INACTIVE_TEXT);
    public static final SystemColor control = new SystemColor(CONTROL);
    public static final SystemColor controlText = new SystemColor(CONTROL_TEXT);
    public static final SystemColor controlLtHighlight = new SystemColor(CONTROL_LT_HIGHLIGHT);
    public static final SystemColor controlHighlight = new SystemColor(CONTROL_HIGHLIGHT);
    public static final SystemColor controlShadow = new SystemColor(CONTROL_SHADOW);
    public static final SystemColor controlDkShadow = new SystemColor(CONTROL_DK_SHADOW);
    public static final SystemColor scrollbar = new SystemColor(SCROLLBAR);
    public static final SystemColor info = new SystemColor(INFO);
    public static final SystemColor infoText = new SystemColor(INFO_TEXT);
    private final int index;
    private SystemColor(int index) { super(0, 0, 0); this.index = index; }
    public int getIndex() { return index; }
    public String toString() { return "SystemColor[" + index + "]"; }
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
