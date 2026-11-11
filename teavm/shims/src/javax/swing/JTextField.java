package javax.swing;
import java.awt.event.*;
/** Minimal javax.swing.JTextField. */
public class JTextField extends javax.swing.text.JTextComponent {
    protected int columns;
    protected int horizontalAlignment = javax.swing.SwingConstants.LEADING;
    protected String actionCommand;
    public JTextField() {}
    public JTextField(String text) { setText(text); }
    public JTextField(int columns) { this.columns = columns; }
    public JTextField(String text, int columns) { setText(text); this.columns = columns; }
    public JTextField(javax.swing.text.Document doc, String text, int columns) { setText(text); this.columns = columns; }
    public int getColumns() { return columns; }
    public void setColumns(int columns) { this.columns = columns; }
    public int getHorizontalAlignment() { return horizontalAlignment; }
    public void setHorizontalAlignment(int a) { horizontalAlignment = a; }
    public void addActionListener(ActionListener l) {}
    public void removeActionListener(ActionListener l) {}
    public ActionListener[] getActionListeners() { return new ActionListener[0]; }
    public String getActionCommand() { return actionCommand; }
    public void setActionCommand(String command) { actionCommand = command; }
    public void setAction(Action a) {}
    public Action getAction() { return null; }
    public void postActionEvent() {}
}
