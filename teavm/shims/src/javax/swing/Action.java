package javax.swing;
import java.awt.event.ActionListener;
import java.beans.PropertyChangeListener;
/** Minimal javax.swing.Action. */
public interface Action extends ActionListener {
    String DEFAULT = "Default";
    String NAME = "Name";
    String SHORT_DESCRIPTION = "ShortDescription";
    String LONG_DESCRIPTION = "LongDescription";
    String SMALL_ICON = "SmallIcon";
    String ACTION_COMMAND_KEY = "ActionCommandKey";
    String ACCELERATOR_KEY = "AcceleratorKey";
    String MNEMONIC_KEY = "MnemonicKey";
    String SELECTED_KEY = "SwingSelectedKey";
    String DISPLAYED_MNEMONIC_INDEX_KEY = "SwingDisplayedMnemonicIndexKey";
    String LARGE_ICON_KEY = "SwingLargeIconKey";
    Object getValue(String key);
    void putValue(String key, Object value);
    void setEnabled(boolean b);
    boolean isEnabled();
    void addPropertyChangeListener(PropertyChangeListener listener);
    void removePropertyChangeListener(PropertyChangeListener listener);
}
