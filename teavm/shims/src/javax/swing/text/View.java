package javax.swing.text;
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
