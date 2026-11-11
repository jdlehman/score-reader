package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface Element extends Node {
    String getTagName();
    String getAttribute(String name);
    void setAttribute(String name, String value);
    void removeAttribute(String name);
    Attr getAttributeNode(String name);
    Attr setAttributeNode(Attr newAttr);
    Attr removeAttributeNode(Attr oldAttr);
    NodeList getElementsByTagName(String name);
    String getAttributeNS(String namespaceURI, String localName);
    void setAttributeNS(String namespaceURI, String qualifiedName, String value);
    void removeAttributeNS(String namespaceURI, String localName);
    Attr getAttributeNodeNS(String namespaceURI, String localName);
    Attr setAttributeNodeNS(Attr newAttr);
    NodeList getElementsByTagNameNS(String namespaceURI, String localName);
    boolean hasAttribute(String name);
    boolean hasAttributeNS(String namespaceURI, String localName);
    TypeInfo getSchemaTypeInfo();
    void setIdAttribute(String name, boolean isId);
    void setIdAttributeNS(String namespaceURI, String localName, boolean isId);
    void setIdAttributeNode(Attr idAttr, boolean isId);
}
