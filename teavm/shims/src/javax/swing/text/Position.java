package javax.swing.text;
/** Minimal javax.swing.text.Position. */
public interface Position {
    int getOffset();
    interface Bias {
        Bias Forward = new Bias() {};
        Bias Backward = new Bias() {};
    }
}
