package javax.swing.text;
/** Minimal javax.swing.text.AttributeSet. */
public interface AttributeSet {
    int getAttributeCount();
    boolean isDefined(Object attrName);
    boolean isEqual(AttributeSet attr);
    AttributeSet copyAttributes();
    Object getAttribute(Object key);
    java.util.Enumeration<?> getAttributeNames();
    boolean containsAttribute(Object name, Object value);
    boolean containsAttributes(AttributeSet attributes);
    AttributeSet getResolveParent();
    interface CharacterAttribute {}
    interface ColorAttribute {}
    interface FontAttribute {}
    interface ParagraphAttribute {}
}
