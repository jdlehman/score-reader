package javax.swing;
/** Minimal javax.swing.LookAndFeel. */
public abstract class LookAndFeel {
    public abstract String getName();
    public abstract String getID();
    public abstract String getDescription();
    public abstract boolean isNativeLookAndFeel();
    public abstract boolean isSupportedLookAndFeel();
    public UIDefaults getDefaults() { return null; }
    public void initialize() {}
    public void uninitialize() {}
    public void provideErrorFeedback(java.awt.Component component) {}
    public String toString() { return getDescription(); }
}
