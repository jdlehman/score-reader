package javax.swing.text;
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
