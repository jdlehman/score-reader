package java.awt.event;
import java.awt.Component;
/** Minimal java.awt.event.FocusEvent. */
public class FocusEvent extends ComponentEvent {
    public static final int FOCUS_FIRST = 1004;
    public static final int FOCUS_LAST = 1005;
    public static final int FOCUS_GAINED = FOCUS_FIRST;
    public static final int FOCUS_LOST = 1 + FOCUS_FIRST;
    protected boolean temporary;
    protected Component opposite;
    public FocusEvent(Component source, int id) { this(source, id, false); }
    public FocusEvent(Component source, int id, boolean temporary) { super(source, id); this.temporary = temporary; }
    public FocusEvent(Component source, int id, boolean temporary, Component opposite) {
        super(source, id); this.temporary = temporary; this.opposite = opposite;
    }
    public boolean isTemporary() { return temporary; }
    public Component getOppositeComponent() { return opposite; }
}
