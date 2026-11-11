package java.awt;
/** Minimal java.awt.Dialog. */
public class Dialog extends Window {
    public static final int DEFAULT_MODALITY_TYPE = 0;
    protected String title;
    protected boolean modal;
    protected boolean resizable = true;
    public Dialog() {}
    public Dialog(Frame owner) {}
    public Dialog(Frame owner, String title) { this.title = title; }
    public Dialog(Frame owner, boolean modal) { this.modal = modal; }
    public Dialog(Frame owner, String title, boolean modal) { this.title = title; this.modal = modal; }
    public Dialog(Dialog owner) {}
    public Dialog(Dialog owner, String title) { this.title = title; }
    public Dialog(Window owner) {}
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public boolean isModal() { return modal; }
    public void setModal(boolean b) { modal = b; }
    public boolean isResizable() { return resizable; }
    public void setResizable(boolean b) { resizable = b; }
    public void setUndecorated(boolean b) {}
    public boolean isUndecorated() { return false; }
}
