package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface Attr extends Node {
    String getName();
    boolean getSpecified();
    String getValue();
    void setValue(String value);
    Element getOwnerElement();
    TypeInfo getSchemaTypeInfo();
    boolean isId();
}
