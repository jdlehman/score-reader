package java.util.concurrent;
/** Minimal java.util.concurrent.TimeoutException (thrown when a blocking
 *  operation times out). Added 2026-11-08: it was the only catch type in
 *  the program missing from TeaVM's classpath, which made TeaVM emit an
 *  empty root struct for it and Node reject the module at function #18066
 *  (SheetStub.doOneStep catch dispatch, br_on_cast Throwable -> TimeoutException). */
public class TimeoutException extends Exception {
    public TimeoutException() { super(); }
    public TimeoutException(String message) { super(message); }
}
