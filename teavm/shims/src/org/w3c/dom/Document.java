package org.w3c.dom;
/** Minimal org.w3c.dom.Document. */
public interface Document extends Node {
    DocumentType getDoctype();
    DOMImplementation getImplementation();
    Element getDocumentElement();
    Element createElement(String tagName);
    DocumentFragment createDocumentFragment();
    Text createTextNode(String data);
    Comment createComment(String data);
    CDATASection createCDATASection(String data);
    ProcessingInstruction createProcessingInstruction(String target, String data);
    Attr createAttribute(String name);
    EntityReference createEntityReference(String name);
    NodeList getElementsByTagName(String tagname);
    Node importNode(Node importedNode, boolean deep);
    Element createElementNS(String namespaceURI, String qualifiedName);
    Attr createAttributeNS(String namespaceURI, String qualifiedName);
    NodeList getElementsByTagNameNS(String namespaceURI, String localName);
    Element getElementById(String elementId);
    String getInputEncoding();
    String getXmlEncoding();
    boolean getXmlStandalone();
    void setXmlStandalone(boolean xmlStandalone);
    String getXmlVersion();
    void setXmlVersion(String xmlVersion);
    boolean getStrictErrorChecking();
    void setStrictErrorChecking(boolean strictErrorChecking);
    String getDocumentURI();
    void setDocumentURI(String documentURI);
    Node adoptNode(Node source);
    DOMConfiguration getDomConfig();
    void normalizeDocument();
    Node renameNode(Node n, String namespaceURI, String qualifiedName);
}
