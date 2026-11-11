package javax.swing.text;
/** Minimal javax.swing.text.Style. */
public interface Style extends MutableAttributeSet {
    String getName();
    void addChangeListener(javax.swing.event.ChangeListener l);
    void removeChangeListener(javax.swing.event.ChangeListener l);
}
