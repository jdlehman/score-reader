package javax.swing;
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
