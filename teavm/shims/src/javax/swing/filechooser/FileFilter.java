package javax.swing.filechooser;
/** Minimal javax.swing.filechooser.FileFilter. */
public abstract class FileFilter {
    public abstract boolean accept(java.io.File f);
    public abstract String getDescription();
}
