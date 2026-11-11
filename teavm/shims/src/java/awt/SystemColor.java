package java.awt;
/** Minimal java.awt.SystemColor. */
public class SystemColor extends Color {
    public static final int DESKTOP = 0;
    public static final int ACTIVE_CAPTION = 1;
    public static final int ACTIVE_CAPTION_TEXT = 2;
    public static final int ACTIVE_CAPTION_BORDER = 3;
    public static final int INACTIVE_CAPTION = 4;
    public static final int INACTIVE_CAPTION_TEXT = 5;
    public static final int INACTIVE_CAPTION_BORDER = 6;
    public static final int WINDOW = 7;
    public static final int WINDOW_BORDER = 8;
    public static final int WINDOW_TEXT = 9;
    public static final int MENU = 10;
    public static final int MENU_TEXT = 11;
    public static final int TEXT = 12;
    public static final int TEXT_TEXT = 13;
    public static final int TEXT_HIGHLIGHT = 14;
    public static final int TEXT_HIGHLIGHT_TEXT = 15;
    public static final int TEXT_INACTIVE_TEXT = 16;
    public static final int CONTROL = 17;
    public static final int CONTROL_TEXT = 18;
    public static final int CONTROL_LT_HIGHLIGHT = 19;
    public static final int CONTROL_HIGHLIGHT = 20;
    public static final int CONTROL_SHADOW = 21;
    public static final int CONTROL_DK_SHADOW = 22;
    public static final int SCROLLBAR = 23;
    public static final int INFO = 24;
    public static final int INFO_TEXT = 25;
    public static final SystemColor desktop = new SystemColor(DESKTOP);
    public static final SystemColor activeCaption = new SystemColor(ACTIVE_CAPTION);
    public static final SystemColor activeCaptionText = new SystemColor(ACTIVE_CAPTION_TEXT);
    public static final SystemColor activeCaptionBorder = new SystemColor(ACTIVE_CAPTION_BORDER);
    public static final SystemColor inactiveCaption = new SystemColor(INACTIVE_CAPTION);
    public static final SystemColor inactiveCaptionText = new SystemColor(INACTIVE_CAPTION_TEXT);
    public static final SystemColor inactiveCaptionBorder = new SystemColor(INACTIVE_CAPTION_BORDER);
    public static final SystemColor window = new SystemColor(WINDOW);
    public static final SystemColor windowBorder = new SystemColor(WINDOW_BORDER);
    public static final SystemColor windowText = new SystemColor(WINDOW_TEXT);
    public static final SystemColor menu = new SystemColor(MENU);
    public static final SystemColor menuText = new SystemColor(MENU_TEXT);
    public static final SystemColor text = new SystemColor(TEXT);
    public static final SystemColor textText = new SystemColor(TEXT_TEXT);
    public static final SystemColor textHighlight = new SystemColor(TEXT_HIGHLIGHT);
    public static final SystemColor textHighlightText = new SystemColor(TEXT_HIGHLIGHT_TEXT);
    public static final SystemColor textInactiveText = new SystemColor(TEXT_INACTIVE_TEXT);
    public static final SystemColor control = new SystemColor(CONTROL);
    public static final SystemColor controlText = new SystemColor(CONTROL_TEXT);
    public static final SystemColor controlLtHighlight = new SystemColor(CONTROL_LT_HIGHLIGHT);
    public static final SystemColor controlHighlight = new SystemColor(CONTROL_HIGHLIGHT);
    public static final SystemColor controlShadow = new SystemColor(CONTROL_SHADOW);
    public static final SystemColor controlDkShadow = new SystemColor(CONTROL_DK_SHADOW);
    public static final SystemColor scrollbar = new SystemColor(SCROLLBAR);
    public static final SystemColor info = new SystemColor(INFO);
    public static final SystemColor infoText = new SystemColor(INFO_TEXT);
    private final int index;
    private SystemColor(int index) { super(0, 0, 0); this.index = index; }
    public int getIndex() { return index; }
    public String toString() { return "SystemColor[" + index + "]"; }
}
