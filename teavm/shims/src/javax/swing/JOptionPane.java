package javax.swing;
/** Minimal javax.swing.JOptionPane. */
public class JOptionPane extends JComponent {
    public static final int DEFAULT_OPTION = -1;
    public static final int YES_NO_OPTION = 0;
    public static final int YES_NO_CANCEL_OPTION = 1;
    public static final int OK_CANCEL_OPTION = 2;
    public static final int YES_OPTION = 0;
    public static final int NO_OPTION = 1;
    public static final int CANCEL_OPTION = 2;
    public static final int OK_OPTION = 0;
    public static final int CLOSED_OPTION = -1;
    public static final int ERROR_MESSAGE = 0;
    public static final int INFORMATION_MESSAGE = 1;
    public static final int WARNING_MESSAGE = 2;
    public static final int QUESTION_MESSAGE = 3;
    public static final int PLAIN_MESSAGE = -1;
    public static final Object UNINITIALIZED_VALUE = "uninitializedValue";
    private Object message, messageType = QUESTION_MESSAGE, optionType = YES_NO_OPTION, value = UNINITIALIZED_VALUE;
    private Object[] options;
    private Object initialValue;
    public JOptionPane() {}
    public JOptionPane(Object message) { this.message = message; }
    public JOptionPane(Object message, int messageType) { this.message = message; this.messageType = messageType; }
    public JOptionPane(Object message, int messageType, int optionType) { this.message = message; this.messageType = messageType; this.optionType = optionType; }
    public JOptionPane(Object message, int messageType, int optionType, Icon icon) { this.message = message; this.messageType = messageType; this.optionType = optionType; }
    public JOptionPane(Object message, int messageType, int optionType, Icon icon, Object[] options) { this.message = message; this.messageType = messageType; this.optionType = optionType; this.options = options; }
    public JOptionPane(Object message, int messageType, int optionType, Icon icon, Object[] options, Object initialValue) { this.message = message; this.messageType = messageType; this.optionType = optionType; this.options = options; this.initialValue = initialValue; }
    public Object getMessage() { return message; }
    public void setMessage(Object newMessage) { message = newMessage; }
    public Object[] getOptions() { return options; }
    public void setOptions(Object[] newOptions) { options = newOptions; }
    public Object getInitialValue() { return initialValue; }
    public void setInitialValue(Object newInitialValue) { initialValue = newInitialValue; }
    public Object getValue() { return value; }
    public void setValue(Object newValue) { value = newValue; }
    public static String showInputDialog(Object message) { return null; }
    public static String showInputDialog(java.awt.Component parentComponent, Object message) { return null; }
    public static String showInputDialog(java.awt.Component parentComponent, Object message, String title, int messageType) { return null; }
    public static Object showInputDialog(java.awt.Component parentComponent, Object message, String title, int messageType, Icon icon, Object[] selectionValues, Object initialSelectionValue) { return null; }
    public static void showMessageDialog(java.awt.Component parentComponent, Object message) {}
    public static void showMessageDialog(java.awt.Component parentComponent, Object message, String title, int messageType) {}
    public static void showMessageDialog(java.awt.Component parentComponent, Object message, String title, int messageType, Icon icon) {}
    public static int showConfirmDialog(java.awt.Component parentComponent, Object message) { return CLOSED_OPTION; }
    public static int showConfirmDialog(java.awt.Component parentComponent, Object message, String title, int optionType) { return CLOSED_OPTION; }
    public static int showConfirmDialog(java.awt.Component parentComponent, Object message, String title, int optionType, int messageType) { return CLOSED_OPTION; }
    public static int showConfirmDialog(java.awt.Component parentComponent, Object message, String title, int optionType, int messageType, Icon icon) { return CLOSED_OPTION; }
    public static int showOptionDialog(java.awt.Component parentComponent, Object message, String title, int optionType, int messageType, Icon icon, Object[] options, Object initialValue) { return CLOSED_OPTION; }
    public static javax.swing.JDialog createDialog(java.awt.Component parentComponent, String title) { return null; }
}
