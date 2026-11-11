package java.awt.font;
import java.text.AttributedCharacterIterator;
/** Minimal java.awt.font.TextAttribute. */
public class TextAttribute extends AttributedCharacterIterator.Attribute {
    protected TextAttribute(String name) { super(name); }
    public static final TextAttribute FONT = new TextAttribute("font");
    public static final TextAttribute FAMILY = new TextAttribute("family");
    public static final TextAttribute SIZE = new TextAttribute("size");
    public static final TextAttribute WEIGHT = new TextAttribute("weight");
    public static final TextAttribute POSTURE = new TextAttribute("posture");
    public static final TextAttribute FOREGROUND = new TextAttribute("foreground");
    public static final TextAttribute BACKGROUND = new TextAttribute("background");
    public static final Float WEIGHT_REGULAR = 1.0f;
    public static final Float WEIGHT_BOLD = 2.0f;
    public static final Float POSTURE_REGULAR = 0.0f;
    public static final Float POSTURE_OBLIQUE = 0.2f;
}
