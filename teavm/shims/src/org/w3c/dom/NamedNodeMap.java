package org.w3c.dom;
/** Minimal org.w3c.dom.NamedNodeMap. */
public interface NamedNodeMap {
    Node getNamedItem(String name);
    Node setNamedItem(Node arg);
    Node removeNamedItem(String name);
    Node item(int index);
    int getLength();
    Node getNamedItemNS(String namespaceURI, String localName);
    Node setNamedItemNS(Node arg);
    Node removeNamedItemNS(String namespaceURI, String localName);
}
