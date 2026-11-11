package javax.swing.text;
/** Minimal javax.swing.text.MutableAttributeSet. */
public interface MutableAttributeSet extends AttributeSet {
    void addAttribute(Object name, Object value);
    void addAttributes(AttributeSet attributes);
    void removeAttribute(Object name);
    void removeAttributes(AttributeSet attributes);
    void removeAttributes(java.util.Enumeration<?> names);
    void setResolveParent(AttributeSet parent);
}
