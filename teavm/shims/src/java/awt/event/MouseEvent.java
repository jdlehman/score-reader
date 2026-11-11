package java.awt.event;
import java.awt.Component;
import java.awt.Point;
/** Minimal java.awt.event.MouseEvent. */
public class MouseEvent extends InputEvent {
    public static final int MOUSE_FIRST = 500;
    public static final int MOUSE_LAST = 507;
    public static final int MOUSE_CLICKED = MOUSE_FIRST;
    public static final int MOUSE_PRESSED = 1 + MOUSE_FIRST;
    public static final int MOUSE_RELEASED = 2 + MOUSE_FIRST;
    public static final int MOUSE_MOVED = 3 + MOUSE_FIRST;
    public static final int MOUSE_ENTERED = 4 + MOUSE_FIRST;
    public static final int MOUSE_EXITED = 5 + MOUSE_FIRST;
    public static final int MOUSE_DRAGGED = 6 + MOUSE_FIRST;
    public static final int MOUSE_WHEEL = 7 + MOUSE_FIRST;
    public static final int NOBUTTON = 0;
    public static final int BUTTON1 = 1;
    public static final int BUTTON2 = 2;
    public static final int BUTTON3 = 3;
    protected int x, y, clickCount, button;
    protected boolean popupTrigger;
    public MouseEvent(Component source, int id, long when, int modifiers, int x, int y, int clickCount, boolean popupTrigger) {
        this(source, id, when, modifiers, x, y, clickCount, popupTrigger, NOBUTTON);
    }
    public MouseEvent(Component source, int id, long when, int modifiers, int x, int y, int clickCount, boolean popupTrigger, int button) {
        super(source, id, when, modifiers);
        this.x = x; this.y = y; this.clickCount = clickCount; this.popupTrigger = popupTrigger; this.button = button;
    }
    public int getX() { return x; }
    public int getY() { return y; }
    public Point getPoint() { return new Point(x, y); }
    public int getClickCount() { return clickCount; }
    public int getButton() { return button; }
    public boolean isPopupTrigger() { return popupTrigger; }
    public void translatePoint(int x, int y) { this.x += x; this.y += y; }
    public static String getMouseModifiersText(int modifiers) { return ""; }
}
