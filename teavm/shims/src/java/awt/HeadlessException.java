package java.awt;
/** Minimal java.awt.HeadlessException (thrown when code that depends on a
 *  keyboard, display, or mouse is called in a headless environment).
 *  The program catches it, and TeaVM has no class for it: without one, TeaVM emits an empty
 *  type for it and the module fails to load at that catch.
 *  (com.jgoodies.common.base.SystemUtils.isLowResolution) */
public class HeadlessException extends UnsupportedOperationException {
    public HeadlessException() { super(); }
    public HeadlessException(String msg) { super(msg); }
}
