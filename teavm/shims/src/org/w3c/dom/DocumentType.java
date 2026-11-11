package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface DocumentType extends Node {
    String getName();
    NamedNodeMap getEntities();
    NamedNodeMap getNotations();
    String getPublicId();
    String getSystemId();
    String getInternalSubset();
}
