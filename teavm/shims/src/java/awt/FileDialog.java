package java.awt;
import java.io.FilenameFilter;
/** Minimal java.awt.FileDialog. */
public class FileDialog extends Dialog {
    public static final int LOAD = 0;
    public static final int SAVE = 1;
    private int mode = LOAD;
    private String directory, file;
    private FilenameFilter filter;
    private boolean multipleMode;
    public FileDialog(Frame parent) { super(parent); }
    public FileDialog(Frame parent, String title) { super(parent, title); }
    public FileDialog(Frame parent, String title, int mode) { super(parent, title); this.mode = mode; }
    public FileDialog(Dialog parent) { super(parent); }
    public FileDialog(Dialog parent, String title) { super(parent, title); }
    public FileDialog(Dialog parent, String title, int mode) { super(parent, title); this.mode = mode; }
    public int getMode() { return mode; }
    public void setMode(int mode) { this.mode = mode; }
    public String getDirectory() { return directory; }
    public void setDirectory(String dir) { directory = dir; }
    public String getFile() { return file; }
    public void setFile(String file) { this.file = file; }
    public FilenameFilter getFilenameFilter() { return filter; }
    public void setFilenameFilter(FilenameFilter filter) { this.filter = filter; }
    public java.io.File[] getFiles() { return new java.io.File[0]; }
    public boolean isMultipleMode() { return multipleMode; }
    public void setMultipleMode(boolean b) { multipleMode = b; }
}
