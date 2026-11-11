package java.awt;
/** Minimal java.awt.EventQueue. */
public class EventQueue {
    public static void invokeLater(Runnable r) { r.run(); }
    public static void invokeAndWait(Runnable r) throws InterruptedException, java.lang.reflect.InvocationTargetException { r.run(); }
    public static boolean isDispatchThread() { return false; }
    public static AWTEvent getCurrentEvent() { return null; }
    public static long getMostRecentEventTime() { return 0; }
    public void postEvent(AWTEvent e) {}
    public AWTEvent getNextEvent() throws InterruptedException { throw new InterruptedException(); }
    public AWTEvent peekEvent() { return null; }
    public void push(EventQueue q) {}
    protected void pop() {}
}
