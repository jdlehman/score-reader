package javax.swing;
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
