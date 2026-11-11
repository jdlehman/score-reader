package javax.swing.text;
/** Minimal javax.swing.text.Segment. */
public class Segment implements java.text.CharacterIterator, Cloneable {
    public char[] array;
    public int offset;
    public int count;
    public boolean partialReturn;
    public Segment() {}
    public Segment(char[] array, int offset, int count) { this.array = array; this.offset = offset; this.count = count; }
    public char first() { return count == 0 ? DONE : array[offset]; }
    public char last() { return count == 0 ? DONE : array[offset + count - 1]; }
    public char current() { return DONE; }
    public char next() { return DONE; }
    public char previous() { return DONE; }
    public char setIndex(int position) { return DONE; }
    public int getBeginIndex() { return offset; }
    public int getEndIndex() { return offset + count; }
    public int getIndex() { return offset; }
    public Object clone() { return this; }
}
