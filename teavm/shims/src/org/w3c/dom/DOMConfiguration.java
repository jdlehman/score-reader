package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface DOMConfiguration {
    void setParameter(String name, Object value);
    Object getParameter(String name);
    boolean canSetParameter(String name, Object value);
    DOMStringList getParameterNames();
}
