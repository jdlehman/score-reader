package java.awt.event;
import java.awt.Component;
/** Minimal java.awt.event.InputEvent. */
public abstract class InputEvent extends java.awt.AWTEvent {
    public static final int SHIFT_MASK = 1;
    public static final int CTRL_MASK = 2;
    public static final int META_MASK = 4;
    public static final int ALT_MASK = 8;
    public static final int ALT_GRAPH_MASK = 32;
    public static final int BUTTON1_MASK = 16;
    public static final int BUTTON2_MASK = 8;
    public static final int BUTTON3_MASK = 4;
    public static final int SHIFT_DOWN_MASK = 64;
    public static final int CTRL_DOWN_MASK = 128;
    public static final int META_DOWN_MASK = 256;
    public static final int ALT_DOWN_MASK = 512;
    public static final int BUTTON1_DOWN_MASK = 1024;
    public static final int BUTTON2_DOWN_MASK = 2048;
    public static final int BUTTON3_DOWN_MASK = 4096;
    protected long when;
    protected int modifiers;
    public InputEvent(Component source, int id, long when, int modifiers) { super(source, id); this.when = when; this.modifiers = modifiers; }
    public boolean isShiftDown() { return (modifiers & SHIFT_DOWN_MASK) != 0; }
    public boolean isControlDown() { return (modifiers & CTRL_DOWN_MASK) != 0; }
    public boolean isMetaDown() { return (modifiers & META_DOWN_MASK) != 0; }
    public boolean isAltDown() { return (modifiers & ALT_DOWN_MASK) != 0; }
    public boolean isAltGraphDown() { return (modifiers & ALT_GRAPH_MASK) != 0; }
    public long getWhen() { return when; }
    public int getModifiers() { return modifiers; }
    public int getModifiersEx() { return modifiers; }
    public void consume() { consumed = true; }
    public boolean isConsumed() { return consumed; }
}
