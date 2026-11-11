package javax.swing.text.html;
import javax.swing.text.*;
/** Minimal javax.swing.text.html.HTMLEditorKit (referenced by ij.gui.HTMLDialog). */
public class HTMLEditorKit extends EditorKit {
    public static final String BOLD_ACTION = "font-bold";
    public static final String ITALIC_ACTION = "font-italic";
    public static final String PARA_INDENT_LEFT = "paragraph-indent-left";
    public static final String PARA_INDENT_RIGHT = "paragraph-indent-right";
    public String getContentType() { return "text/html"; }
    public ViewFactory getViewFactory() { return null; }
    public javax.swing.Action[] getActions() { return new javax.swing.Action[0]; }
    public Caret createCaret() { return null; }
    public Document createDefaultDocument() { return null; }
    public StyleSheet getStyleSheet() { return null; }
    public void setStyleSheet(StyleSheet s) {}
    public void read(java.io.InputStream in, Document doc, int pos) throws java.io.IOException, BadLocationException {}
    public void write(java.io.OutputStream out, Document doc, int pos, int len) throws java.io.IOException, BadLocationException {}
    public void read(java.io.Reader in, Document doc, int pos) throws java.io.IOException, BadLocationException {}
    public void write(java.io.Writer out, Document doc, int pos, int len) throws java.io.IOException, BadLocationException {}
    public void install(javax.swing.text.JTextComponent c) {}
    public void deinstall(javax.swing.text.JTextComponent c) {}
}
