package org.slf4j;
import java.util.Iterator;
public interface Marker {
    String getName();
    void add(Marker reference);
    boolean remove(Marker reference);
    boolean hasChildren();
    boolean hasReferences();
    Iterator<Marker> iterator();
    boolean contains(Marker other);
    boolean contains(String name);
}
