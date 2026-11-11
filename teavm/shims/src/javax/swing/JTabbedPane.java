package javax.swing;
import java.awt.*;
import javax.swing.event.ChangeListener;
/** Minimal javax.swing.JTabbedPane. */
public class JTabbedPane extends JComponent {
    public static final int WRAP_TAB_LAYOUT = 0;
    public static final int SCROLL_TAB_LAYOUT = 1;
    public static final int TOP = 1;
    public static final int BOTTOM = 3;
    public static final int LEFT = 2;
    public static final int RIGHT = 4;
    protected int tabPlacement = TOP;
    protected int selectedIndex = -1;
    public JTabbedPane() {}
    public JTabbedPane(int tabPlacement) { this.tabPlacement = tabPlacement; }
    public JTabbedPane(int tabPlacement, int tabLayoutPolicy) { this.tabPlacement = tabPlacement; }
    public void addTab(String title, Component component) {}
    public void addTab(String title, Icon icon, Component component) {}
    public void addTab(String title, Icon icon, Component component, String tip) {}
    public void insertTab(String title, Icon icon, Component component, String tip, int index) {}
    public void removeTabAt(int index) {}
    public int getTabCount() { return 0; }
    public int getSelectedIndex() { return selectedIndex; }
    public void setSelectedIndex(int index) { selectedIndex = index; }
    public Component getSelectedComponent() { return null; }
    public void setSelectedComponent(Component c) {}
    public String getTitleAt(int index) { return null; }
    public void setTitleAt(int index, String title) {}
    public Icon getIconAt(int index) { return null; }
    public void setIconAt(int index, Icon icon) {}
    public String getToolTipTextAt(int index) { return null; }
    public void setToolTipTextAt(int index, String text) {}
    public Component getComponentAt(int index) { return null; }
    public void setComponentAt(int index, Component component) {}
    public int getTabPlacement() { return tabPlacement; }
    public void setTabPlacement(int tabPlacement) { this.tabPlacement = tabPlacement; }
    public void setEnabledAt(int index, boolean enabled) {}
    public boolean isEnabledAt(int index) { return false; }
    public int indexOfComponent(Component component) { return -1; }
    public int indexOfTab(String title) { return -1; }
    public void setMnemonicAt(int index, int mnemonic) {}
    public int getMnemonicAt(int index) { return 0; }
    public void addChangeListener(ChangeListener l) {}
    public void removeChangeListener(ChangeListener l) {}
    public ChangeListener[] getChangeListeners() { return new ChangeListener[0]; }
    public void setTabLayoutPolicy(int policy) {}
    public int getTabLayoutPolicy() { return WRAP_TAB_LAYOUT; }
}
