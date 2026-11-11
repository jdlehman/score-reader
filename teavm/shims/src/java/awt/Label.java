package java.awt;
/** Minimal java.awt.Label. */
public class Label extends Component {
    public static final int LEFT = 0;
    public static final int CENTER = 1;
    public static final int RIGHT = 2;
    protected String text;
    protected int alignment = LEFT;
    public Label() {}
    public Label(String text) { this.text = text; }
    public Label(String text, int alignment) { this.text = text; this.alignment = alignment; }
    public String getText() { return text; }
    public void setText(String text) { this.text = text; }
    public int getAlignment() { return alignment; }
    public void setAlignment(int alignment) { this.alignment = alignment; }
}
