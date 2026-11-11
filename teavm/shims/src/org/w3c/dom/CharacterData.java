package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface CharacterData extends Node {
    String getData();
    void setData(String data);
    int getLength();
    String substringData(int offset, int count);
    void appendData(String arg);
    void insertData(int offset, String arg);
    void deleteData(int offset, int count);
    void replaceData(int offset, int count, String arg);
}
