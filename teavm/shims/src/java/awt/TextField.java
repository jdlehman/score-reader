package java.awt;
/** Minimal java.awt.TextField. */
public class TextField extends TextComponent {
    private int columns;
    private char echoChar;
    public TextField() {}
    public TextField(String text) { setText(text); }
    public TextField(int columns) { this.columns = columns; }
    public TextField(String text, int columns) { setText(text); this.columns = columns; }
    public int getColumns() { return columns; }
    public void setColumns(int columns) { this.columns = columns; }
    public char getEchoChar() { return echoChar; }
    public void setEchoChar(char c) { echoChar = c; }
    public void setEchoCharacter(char c) { echoChar = c; }
    public boolean echoCharIsSet() { return echoChar != 0; }
    public void addActionListener(java.awt.event.ActionListener l) {}
    public void removeActionListener(java.awt.event.ActionListener l) {}
    public java.awt.event.ActionListener[] getActionListeners() { return new java.awt.event.ActionListener[0]; }
    public java.awt.Dimension getPreferredSize(int columns) { return new java.awt.Dimension(0, 0); }
}
