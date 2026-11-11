package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface Text extends CharacterData {
    Text splitText(int offset);
    boolean isElementContentWhitespace();
    String getWholeText();
    Text replaceWholeText(String content);
}
