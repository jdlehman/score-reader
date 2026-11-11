package java.beans;
/** Minimal java.beans.IntrospectionException (thrown when an exception
 *  occurs during introspection).
 *  Added 2026-11-09: it was missing from TeaVM's classpath. Found by a
 *  full audit of catch types across all program jars (AuditCatchTypes);
 *  it is caught in org.jdesktop.application.ResourceMap (bsaf), which is
 *  compiled into TeavmMain, so it would have surfaced as the next
 *  br_on_cast failure after java.awt.HeadlessException (#32683). Same
 *  defect class as #18066 (TimeoutException), #19489 (FontFormatException)
 *  and #32683 (HeadlessException). */
public class IntrospectionException extends Exception {
    public IntrospectionException(String mess) { super(mess); }
}
