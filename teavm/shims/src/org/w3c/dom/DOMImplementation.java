package org.w3c.dom;
/** Minimal org.w3c.dom stubs for types referenced by Document/Node signatures. */
public interface DOMImplementation {
    boolean hasFeature(String feature, String version);
    DocumentType createDocumentType(String qualifiedName, String publicId, String systemId);
    Document createDocument(String namespaceURI, String qualifiedName, DocumentType doctype);
    Object getFeature(String feature, String version);
}
