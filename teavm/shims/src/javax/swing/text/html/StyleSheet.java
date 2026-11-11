package javax.swing.text.html;
import javax.swing.text.Style;
/** Minimal javax.swing.text.html.StyleSheet (referenced by ij.gui.HTMLDialog). */
public class StyleSheet {
    public StyleSheet() {}
    public Style addStyle(String nm, Style parent) { return null; }
    public void removeStyle(String nm) {}
    public Style getStyle(String nm) { return null; }
    public String[] getStyleNames() { return new String[0]; }
    public void addRule(String rule) {}
    public String getRule(String selector) { return null; }
    public void removeRule(String selector) {}
    public void importStyleSheet(java.net.URL url) {}
    public String getDeclaration(String decl) { return null; }
    public void loadRules(java.io.Reader in, java.net.URL ref) {}
    public javax.swing.text.AttributeSet getViewAttributes(javax.swing.text.View v) { return null; }
    public javax.swing.text.AttributeSet translateHTMLToCSS(javax.swing.text.AttributeSet htmlAttrSet) { return null; }
}
