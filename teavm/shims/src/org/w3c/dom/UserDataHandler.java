package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface UserDataHandler {
    short NODE_CLONED = 1;
    short NODE_IMPORTED = 2;
    short NODE_DELETED = 3;
    short NODE_RENAMED = 4;
    short NODE_ADOPTED = 5;
    void handle(short operation, String key, Object data, Node src, Node dst);
}
