package javax.swing.text;
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
