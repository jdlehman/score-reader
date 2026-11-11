package java.awt;
import java.awt.event.*;
/** Minimal java.awt.Button. */
public class Button extends Component {
    protected String label;
    protected String actionCommand;
    public Button() {}
    public Button(String label) { this.label = label; }
    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public String getActionCommand() { return actionCommand; }
    public void setActionCommand(String command) { actionCommand = command; }
    public void addActionListener(ActionListener l) {}
    public void removeActionListener(ActionListener l) {}
    public ActionListener[] getActionListeners() { return new ActionListener[0]; }
}
