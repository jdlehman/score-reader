package java.awt;
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
