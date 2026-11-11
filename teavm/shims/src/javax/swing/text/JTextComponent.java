package javax.swing.text;
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
