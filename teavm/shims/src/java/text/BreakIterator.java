package java.text;
/** Minimal java.text.BreakIterator (analysis stub; no real iteration). */
public abstract class BreakIterator implements Cloneable {
    public static final int DONE = -1;
    protected BreakIterator() {}
    public static BreakIterator getCharacterInstance() { return null; }
    public static BreakIterator getCharacterInstance(java.util.Locale locale) { return null; }
    public static BreakIterator getWordInstance() { return null; }
    public static BreakIterator getWordInstance(java.util.Locale locale) { return null; }
    public static BreakIterator getLineInstance() { return null; }
    public static BreakIterator getLineInstance(java.util.Locale locale) { return null; }
    public static BreakIterator getSentenceInstance() { return null; }
    public static BreakIterator getSentenceInstance(java.util.Locale locale) { return null; }
    public abstract int first();
    public abstract int last();
    public abstract int next(int n);
    public abstract int next();
    public abstract int previous();
    public abstract int following(int offset);
    public abstract int preceding(int offset);
    public abstract int current();
    public abstract CharacterIterator getText();
    public abstract void setText(String newText);
    public abstract void setText(CharacterIterator newText);
    @Override public Object clone() {
        try { return super.clone(); } catch (CloneNotSupportedException e) { throw new InternalError(e); }
    }
}
