package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface ProcessingInstruction extends Node {
    String getTarget();
    String getData();
    void setData(String data);
}
