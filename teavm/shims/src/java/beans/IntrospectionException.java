package java.beans;
/** Minimal java.beans.IntrospectionException (thrown when an exception
 *  occurs during introspection).
 *  The program catches it, and TeaVM has no class for it: without one, TeaVM emits an empty
 *  type for it and the module fails to load at that catch.
 *  (org.jdesktop.application.ResourceMap) */
public class IntrospectionException extends Exception {
    public IntrospectionException(String mess) { super(mess); }
}
