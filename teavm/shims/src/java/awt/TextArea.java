package java.awt;
/** Minimal java.awt.TextArea. */
public class TextArea extends TextComponent {
    public static final int SCROLLBARS_BOTH = 0;
    public static final int SCROLLBARS_VERTICAL_ONLY = 1;
    public static final int SCROLLBARS_HORIZONTAL_ONLY = 2;
    public static final int SCROLLBARS_NONE = 3;
    private int rows, columns;
    public TextArea() {}
    public TextArea(String text) { setText(text); }
    public TextArea(int rows, int columns) { this.rows = rows; this.columns = columns; }
    public TextArea(String text, int rows, int columns) { setText(text); this.rows = rows; this.columns = columns; }
    public TextArea(String text, int rows, int columns, int scrollbars) { setText(text); this.rows = rows; this.columns = columns; }
    public int getRows() { return rows; }
    public void setRows(int rows) { this.rows = rows; }
    public int getColumns() { return columns; }
    public void setColumns(int columns) { this.columns = columns; }
    public int getScrollbarVisibility() { return SCROLLBARS_BOTH; }
    public void append(String str) { setText(getText() + str); }
    public void appendText(String str) { append(str); }
    public void insert(String str, int pos) {}
    public void insertText(String str, int pos) {}
    public void replaceRange(String str, int start, int end) {}
    public void replaceText(String str, int start, int end) {}
}
