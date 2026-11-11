package java.awt.event;
import java.awt.Window;
/** Minimal java.awt.event.WindowEvent. */
public class WindowEvent extends ComponentEvent {
    public static final int WINDOW_FIRST = 200;
    public static final int WINDOW_LAST = 209;
    public static final int WINDOW_OPENED = WINDOW_FIRST;
    public static final int WINDOW_CLOSING = 1 + WINDOW_FIRST;
    public static final int WINDOW_CLOSED = 2 + WINDOW_FIRST;
    public static final int WINDOW_ICONIFIED = 3 + WINDOW_FIRST;
    public static final int WINDOW_DEICONIFIED = 4 + WINDOW_FIRST;
    public static final int WINDOW_ACTIVATED = 5 + WINDOW_FIRST;
    public static final int WINDOW_DEACTIVATED = 6 + WINDOW_FIRST;
    public static final int WINDOW_GAINED_FOCUS = 7 + WINDOW_FIRST;
    public static final int WINDOW_LOST_FOCUS = 8 + WINDOW_FIRST;
    public static final int WINDOW_STATE_CHANGED = 9 + WINDOW_FIRST;
    protected Window opposite;
    protected int oldState, newState;
    public WindowEvent(Window source, int id) { super(source, id); }
    public WindowEvent(Window source, int id, Window opposite) { super(source, id); this.opposite = opposite; }
    public WindowEvent(Window source, int id, int oldState, int newState) {
        super(source, id); this.oldState = oldState; this.newState = newState;
    }
    public Window getWindow() { return (Window) getSource(); }
    public Window getOppositeWindow() { return opposite; }
    public int getOldState() { return oldState; }
    public int getNewState() { return newState; }
}
