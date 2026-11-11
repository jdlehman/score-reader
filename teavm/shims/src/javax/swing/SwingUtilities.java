package javax.swing;
import java.lang.reflect.InvocationTargetException;
/** Minimal javax.swing.SwingUtilities: no EDT in TeaVM; run everything inline. */
public class SwingUtilities {
    private SwingUtilities() {}
    public static boolean isEventDispatchThread() { return false; }
    public static void invokeLater(Runnable doRun) { doRun.run(); }
    public static void invokeAndWait(Runnable doRun) throws InterruptedException, InvocationTargetException { doRun.run(); }
    public static <T> T invokeAndWait(java.util.concurrent.Callable<T> c) throws Exception { return c.call(); }
    public static boolean isDescendingFrom(java.awt.Component a, java.awt.Component b) { return false; }
    public static java.awt.Point convertPoint(java.awt.Component source, java.awt.Point aPoint, java.awt.Component destination) { return aPoint; }
    public static java.awt.Rectangle convertRectangle(java.awt.Component source, java.awt.Rectangle aRectangle, java.awt.Component destination) { return aRectangle; }
    public static java.awt.Component getRoot(java.awt.Component c) { return c; }
    public static java.awt.Component getAncestorOfClass(Class<?> c, java.awt.Component comp) { return null; }
}
