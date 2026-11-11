package javax.swing.text;
/** Minimal javax.swing.text.Keymap. */
public interface Keymap {
    String getName();
    javax.swing.Action getDefaultAction();
    void setDefaultAction(javax.swing.Action a);
    javax.swing.Action getAction(javax.swing.KeyStroke key);
    javax.swing.KeyStroke[] getBoundKeyStrokes();
    javax.swing.Action[] getBoundActions();
    javax.swing.KeyStroke[] getKeyStrokesForAction(javax.swing.Action a);
    boolean isLocallyDefined(javax.swing.KeyStroke key);
    void addActionForKeyStroke(javax.swing.KeyStroke key, javax.swing.Action a);
    void removeKeyStrokeBinding(javax.swing.KeyStroke keys);
    void removeBindings();
    Keymap getResolveParent();
    void setResolveParent(Keymap parent);
}
