package java.util.concurrent;
/** Minimal java.util.concurrent.TimeoutException (thrown when a blocking
 *  operation times out).
 *  The program catches it, and TeaVM has no class for it: without one, TeaVM emits an empty
 *  type for it and the module fails to load at that catch. (SheetStub.doOneStep) */
public class TimeoutException extends Exception {
    public TimeoutException() { super(); }
    public TimeoutException(String message) { super(message); }
}
