package java.text;
import java.util.Map;
import java.util.Set;
/** Minimal java.text.AttributedCharacterIterator. */
public interface AttributedCharacterIterator extends CharacterIterator {
    class Attribute implements java.io.Serializable {
        private final String name;
        protected Attribute(String name) { this.name = name; }
        @Override public String toString() { return getClass().getName() + "(" + name + ")"; }
        @Override public boolean equals(Object o) { return o == this; }
        @Override public int hashCode() { return System.identityHashCode(this); }
        public static final Attribute LANGUAGE = new Attribute("language");
        public static final Attribute READING = new Attribute("reading");
        public static final Attribute INPUT_METHOD_SEGMENT = new Attribute("input_method_segment");
    }
    Set<Attribute> getAllAttributeKeys();
    Object getAttribute(Attribute attribute);
    Map<Attribute, Object> getAttributes();
    int getRunLimit();
    int getRunLimit(Attribute attribute);
    int getRunLimit(Set<? extends Attribute> attributes);
    int getRunStart();
    int getRunStart(Attribute attribute);
    int getRunStart(Set<? extends Attribute> attributes);
}
