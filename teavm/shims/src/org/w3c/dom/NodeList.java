package org.w3c.dom;
/** Minimal org.w3c.dom.NodeList. */
public interface NodeList {
    Node item(int index);
    int getLength();
}
