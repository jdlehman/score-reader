package javax.swing;
/** Minimal javax.swing.JFileChooser. */
public class JFileChooser extends JComponent {
    public static final int OPEN_DIALOG = 0;
    public static final int SAVE_DIALOG = 1;
    public static final int CUSTOM_DIALOG = 2;
    public static final int APPROVE_OPTION = 0;
    public static final int CANCEL_OPTION = 1;
    public static final int ERROR_OPTION = -1;
    public static final int FILES_ONLY = 0;
    public static final int DIRECTORIES_ONLY = 1;
    public static final int FILES_AND_DIRECTORIES = 2;
    private java.io.File selectedFile;
    private java.io.File[] selectedFiles = new java.io.File[0];
    private java.io.File currentDirectory;
    private int dialogType = OPEN_DIALOG;
    private int fileSelectionMode = FILES_ONLY;
    private boolean multiSelectionEnabled;
    private javax.swing.filechooser.FileFilter fileFilter;
    private String dialogTitle;
    public JFileChooser() {}
    public JFileChooser(String currentDirectoryPath) { currentDirectory = new java.io.File(currentDirectoryPath); }
    public JFileChooser(java.io.File currentDirectory) { this.currentDirectory = currentDirectory; }
    public int showOpenDialog(java.awt.Component parent) { return CANCEL_OPTION; }
    public int showSaveDialog(java.awt.Component parent) { return CANCEL_OPTION; }
    public int showDialog(java.awt.Component parent, String approveButtonText) { return CANCEL_OPTION; }
    public java.io.File getSelectedFile() { return selectedFile; }
    public void setSelectedFile(java.io.File file) { selectedFile = file; }
    public String getName(java.io.File f) { return (f == null) ? null : f.getName(); }
    public String getDescription(java.io.File f) { return getName(f); }
    public String getTypeDescription(java.io.File f) { return null; }
    public java.io.File[] getSelectedFiles() { return selectedFiles; }
    public void setSelectedFiles(java.io.File[] selectedFiles) { this.selectedFiles = selectedFiles; }
    public java.io.File getCurrentDirectory() { return currentDirectory; }
    public void setCurrentDirectory(java.io.File dir) { currentDirectory = dir; }
    public int getDialogType() { return dialogType; }
    public void setDialogType(int dialogType) { this.dialogType = dialogType; }
    public int getFileSelectionMode() { return fileSelectionMode; }
    public void setFileSelectionMode(int mode) { fileSelectionMode = mode; }
    public boolean isMultiSelectionEnabled() { return multiSelectionEnabled; }
    public void setMultiSelectionEnabled(boolean b) { multiSelectionEnabled = b; }
    public javax.swing.filechooser.FileFilter getFileFilter() { return fileFilter; }
    public void setFileFilter(javax.swing.filechooser.FileFilter filter) { fileFilter = filter; }
    public void addChoosableFileFilter(javax.swing.filechooser.FileFilter filter) {}
    public boolean removeChoosableFileFilter(javax.swing.filechooser.FileFilter f) { return false; }
    public javax.swing.filechooser.FileFilter[] getChoosableFileFilters() { return new javax.swing.filechooser.FileFilter[0]; }
    public void setAcceptAllFileFilterUsed(boolean b) {}
    public boolean isAcceptAllFileFilterUsed() { return true; }
    public String getDialogTitle() { return dialogTitle; }
    public void setDialogTitle(String dialogTitle) { this.dialogTitle = dialogTitle; }
    public void setApproveButtonText(String approveButtonText) {}
    public String getApproveButtonText() { return null; }
    public void rescanCurrentDirectory() {}
    public void setFileHidingEnabled(boolean b) {}
    public boolean isFileHidingEnabled() { return true; }
    public void setControlButtonsAreShown(boolean b) {}
    public boolean getControlButtonsAreShown() { return true; }
}
