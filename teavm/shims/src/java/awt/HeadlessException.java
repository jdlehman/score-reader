package java.awt;
/** Minimal java.awt.HeadlessException (thrown when code that depends on a
 *  keyboard, display, or mouse is called in a headless environment).
 *  Added 2026-11-09: it was missing from TeaVM's classpath, which made TeaVM
 *  emit an empty root struct for it and Node reject the module at function
 *  #32683 (com.jgoodies.common.base.SystemUtils.isLowResolution catch
 *  dispatch, br_on_cast Throwable -> HeadlessException). Same defect class
 *  as #18066 (TimeoutException) and #19489 (FontFormatException). Found by
 *  a full audit of catch types across all program jars (AuditCatchTypes);
 *  java.beans.IntrospectionException was the only other missing catch type
 *  in a compiled class, and was shimmed at the same time. */
public class HeadlessException extends UnsupportedOperationException {
    public HeadlessException() { super(); }
    public HeadlessException(String msg) { super(msg); }
}
