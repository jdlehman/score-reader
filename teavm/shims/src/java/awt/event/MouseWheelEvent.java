package java.awt.event;
import java.awt.Component;
/** Minimal java.awt.event.MouseWheelEvent. */
public class MouseWheelEvent extends MouseEvent {
    public static final int WHEEL_UNIT_SCROLL = 0;
    public static final int WHEEL_BLOCK_SCROLL = 1;
    protected int scrollType, scrollAmount, wheelRotation;
    protected double preciseWheelRotation;
    public MouseWheelEvent(Component source, int id, long when, int modifiers, int x, int y, int clickCount, boolean popupTrigger, int scrollType, int scrollAmount, int wheelRotation) {
        super(source, id, when, modifiers, x, y, clickCount, popupTrigger);
        this.scrollType = scrollType; this.scrollAmount = scrollAmount; this.wheelRotation = wheelRotation;
    }
    public MouseWheelEvent(Component source, int id, long when, int modifiers, int x, int y, int xAbs, int yAbs, int clickCount, boolean popupTrigger, int scrollType, int scrollAmount, int wheelRotation, double preciseWheelRotation) {
        this(source, id, when, modifiers, x, y, clickCount, popupTrigger, scrollType, scrollAmount, wheelRotation);
        this.preciseWheelRotation = preciseWheelRotation;
    }
    public int getScrollType() { return scrollType; }
    public int getScrollAmount() { return scrollAmount; }
    public int getWheelRotation() { return wheelRotation; }
    public double getPreciseWheelRotation() { return preciseWheelRotation; }
    public int getUnitsToScroll() { return scrollAmount * wheelRotation; }
}
