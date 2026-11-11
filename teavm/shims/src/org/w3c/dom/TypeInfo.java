package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface TypeInfo {
    String getTypeName();
    String getTypeNamespace();
    boolean isDerivedFrom(String typeNamespaceArg, String typeNameArg, int derivationMethod);
}
