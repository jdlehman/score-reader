package java.awt.event;
/** Minimal java.awt.event.ActionEvent. */
public class ActionEvent extends java.awt.AWTEvent {
    public static final int SHIFT_MASK = 1;
    public static final int CTRL_MASK = 2;
    public static final int META_MASK = 4;
    public static final int ALT_MASK = 8;
    public static final int ACTION_FIRST = 1001;
    public static final int ACTION_LAST = 1001;
    public static final int ACTION_PERFORMED = ACTION_FIRST;
    protected String actionCommand;
    protected long when;
    protected int modifiers;
    public ActionEvent(Object source, int id, String command) { this(source, id, command, 0); }
    public ActionEvent(Object source, int id, String command, int modifiers) { this(source, id, command, 0, modifiers); }
    public ActionEvent(Object source, int id, String command, long when, int modifiers) {
        super(source, id); actionCommand = command; this.when = when; this.modifiers = modifiers;
    }
    public String getActionCommand() { return actionCommand; }
    public long getWhen() { return when; }
    public int getModifiers() { return modifiers; }
}
