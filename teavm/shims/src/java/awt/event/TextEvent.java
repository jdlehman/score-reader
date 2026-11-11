package java.awt.event;
/** Minimal java.awt.event.TextEvent. */
public class TextEvent extends java.awt.AWTEvent {
    public static final int TEXT_FIRST = 900;
    public static final int TEXT_LAST = 900;
    public static final int TEXT_VALUE_CHANGED = TEXT_FIRST;
    public TextEvent(Object source, int id) { super(source, id); }
}
