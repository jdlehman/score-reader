package javax.swing.text;
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
