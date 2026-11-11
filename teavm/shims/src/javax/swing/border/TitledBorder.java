package javax.swing.border;
import javax.swing.border.Border;
import java.awt.Color;
import java.awt.Font;
/** Minimal javax.swing.border.TitledBorder. */
public class TitledBorder implements Border, java.io.Serializable {
    public static final int DEFAULT_POSITION = 0;
    public static final int ABOVE_TOP = 1;
    public static final int TOP = 2;
    public static final int BELOW_TOP = 3;
    public static final int ABOVE_BOTTOM = 4;
    public static final int BOTTOM = 5;
    public static final int BELOW_BOTTOM = 6;
    public static final int DEFAULT_JUSTIFICATION = 0;
    public static final int LEFT = 1;
    public static final int CENTER = 2;
    public static final int RIGHT = 3;
    public static final int LEADING = 4;
    public static final int TRAILING = 5;
    private Border border;
    private String title;
    private int titleJustification = DEFAULT_JUSTIFICATION;
    private int titlePosition = DEFAULT_POSITION;
    private Font titleFont;
    private Color titleColor;
    public TitledBorder(String title) { this.title = title; }
    public TitledBorder(Border border) { this.border = border; }
    public TitledBorder(Border border, String title) { this.border = border; this.title = title; }
    public TitledBorder(Border border, String title, int titleJustification, int titlePosition) {
        this.border = border; this.title = title; this.titleJustification = titleJustification; this.titlePosition = titlePosition;
    }
    public TitledBorder(Border border, String title, int titleJustification, int titlePosition, Font titleFont) {
        this(border, title, titleJustification, titlePosition); this.titleFont = titleFont;
    }
    public TitledBorder(Border border, String title, int titleJustification, int titlePosition, Font titleFont, Color titleColor) {
        this(border, title, titleJustification, titlePosition, titleFont); this.titleColor = titleColor;
    }
    public void paintBorder(java.awt.Component c, java.awt.Graphics g, int x, int y, int width, int height) {}
    public java.awt.Insets getBorderInsets(java.awt.Component c) { return new java.awt.Insets(0, 0, 0, 0); }
    public boolean isBorderOpaque() { return false; }
    public Border getBorder() { return border; }
    public void setBorder(Border border) { this.border = border; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public int getTitleJustification() { return titleJustification; }
    public void setTitleJustification(int titleJustification) { this.titleJustification = titleJustification; }
    public int getTitlePosition() { return titlePosition; }
    public void setTitlePosition(int titlePosition) { this.titlePosition = titlePosition; }
    public Font getTitleFont() { return titleFont; }
    public void setTitleFont(Font titleFont) { this.titleFont = titleFont; }
    public Color getTitleColor() { return titleColor; }
    public void setTitleColor(Color titleColor) { this.titleColor = titleColor; }
    public java.awt.Dimension getMinimumSize(java.awt.Component c) { return new java.awt.Dimension(0, 0); }
}
