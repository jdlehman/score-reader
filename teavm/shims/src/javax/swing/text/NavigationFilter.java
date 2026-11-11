package javax.swing.text;
/** Minimal javax.swing.text.NavigationFilter. */
public abstract class NavigationFilter {
    public void setDot(NavigationFilter.FilterBypass fb, int dot, Position.Bias bias) { fb.setDot(dot, bias); }
    public void moveDot(NavigationFilter.FilterBypass fb, int dot, Position.Bias bias) { fb.moveDot(dot, bias); }
    public int getNextVisualPositionFrom(JTextComponent text, int pos, Position.Bias bias, int direction, Position.Bias[] biasRet) throws BadLocationException { return pos; }
    public abstract static class FilterBypass {
        public abstract void setDot(int dot, Position.Bias bias);
        public abstract void moveDot(int dot, Position.Bias bias);
    }
}
