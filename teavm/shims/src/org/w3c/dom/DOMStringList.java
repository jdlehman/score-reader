package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface DOMStringList {
    String item(int index);
    int getLength();
    boolean contains(String str);
}
