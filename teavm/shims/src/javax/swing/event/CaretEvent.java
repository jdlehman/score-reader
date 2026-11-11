package javax.swing.event;
/** Minimal javax.swing.event.CaretEvent. */
public abstract class CaretEvent extends java.util.EventObject {
    public CaretEvent(Object source) { super(source); }
    public abstract int getDot();
    public abstract int getMark();
}
