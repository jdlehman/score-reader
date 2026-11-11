package teavm;

import java.awt.Point;
import java.awt.Rectangle;
import java.awt.geom.CubicCurve2D;
import java.awt.geom.Line2D;
import java.awt.geom.Point2D;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.ListIterator;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

import org.audiveris.omr.WellKnowns;
import org.audiveris.omr.glyph.Shape;
import org.audiveris.omr.glyph.ShapeSet.HeadMotif;
import org.audiveris.omr.math.Rational;
import org.audiveris.omr.score.DrumSet;
import org.audiveris.omr.score.LogicalPart;
import org.audiveris.omr.score.MidiAbstractions;
import org.audiveris.omr.score.Page;
import org.audiveris.omr.score.Score;
import org.audiveris.omr.sheet.Book;
import org.audiveris.omr.sheet.Part;
import org.audiveris.omr.sheet.PartBarline;
import org.audiveris.omr.sheet.Scale;
import org.audiveris.omr.sheet.Sheet;
import org.audiveris.omr.sheet.SheetStub;
import org.audiveris.omr.sheet.Staff;
import org.audiveris.omr.sheet.SystemInfo;
import org.audiveris.omr.sheet.rhythm.Measure;
import org.audiveris.omr.sheet.rhythm.MeasureStack;
import org.audiveris.omr.sheet.rhythm.Slot;
import org.audiveris.omr.sheet.rhythm.SlotVoice;
import org.audiveris.omr.sheet.rhythm.Voice;
import org.audiveris.omr.sig.SIGraph;
import org.audiveris.omr.sig.inter.AbstractBeamInter;
import org.audiveris.omr.sig.inter.AbstractChordInter;
import org.audiveris.omr.sig.inter.AbstractNoteInter;
import org.audiveris.omr.sig.inter.AbstractPauseInter;
import org.audiveris.omr.sig.inter.AbstractTimeInter;
import org.audiveris.omr.sig.inter.AlterInter;
import org.audiveris.omr.sig.inter.ArpeggiatoInter;
import org.audiveris.omr.sig.inter.ArticulationInter;
import org.audiveris.omr.sig.inter.BeamGroupInter;
import org.audiveris.omr.sig.inter.BowInter;
import org.audiveris.omr.sig.inter.ChordNameInter;
import org.audiveris.omr.sig.inter.ClefInter;
import org.audiveris.omr.sig.inter.DynamicsInter;
import org.audiveris.omr.sig.inter.EndingInter;
import org.audiveris.omr.sig.inter.FermataInter;
import org.audiveris.omr.sig.inter.FingeringInter;
import org.audiveris.omr.sig.inter.HeadChordInter;
import org.audiveris.omr.sig.inter.HeadInter;
import org.audiveris.omr.sig.inter.Inter;
import org.audiveris.omr.sig.inter.KeyInter;
import org.audiveris.omr.sig.inter.LyricItemInter;
import org.audiveris.omr.sig.inter.MarkerInter;
import org.audiveris.omr.sig.inter.MeasureRepeatInter;
import org.audiveris.omr.sig.inter.MetronomeInter;
import org.audiveris.omr.sig.inter.MultipleRestInter;
import org.audiveris.omr.sig.inter.OctaveShiftInter;
import org.audiveris.omr.sig.inter.OrnamentInter;
import org.audiveris.omr.sig.inter.PedalInter;
import org.audiveris.omr.sig.inter.PlayingInter;
import org.audiveris.omr.sig.inter.PluckingInter;
import org.audiveris.omr.sig.inter.RehearsalInter;
import org.audiveris.omr.sig.inter.RestChordInter;
import org.audiveris.omr.sig.inter.SentenceInter;
import org.audiveris.omr.sig.inter.SlurInter;
import org.audiveris.omr.sig.inter.SmallChordInter;
import org.audiveris.omr.sig.inter.StaffBarlineInter;
import org.audiveris.omr.sig.inter.TremoloInter;
import org.audiveris.omr.sig.inter.TupletInter;
import org.audiveris.omr.sig.inter.WedgeInter;
import org.audiveris.omr.sig.relation.ChordArpeggiatoRelation;
import org.audiveris.omr.sig.relation.ChordArticulationRelation;
import org.audiveris.omr.sig.relation.ChordBowRelation;
import org.audiveris.omr.sig.relation.ChordDynamicsRelation;
import org.audiveris.omr.sig.relation.ChordNameRelation;
import org.audiveris.omr.sig.relation.ChordOrnamentRelation;
import org.audiveris.omr.sig.relation.ChordPauseRelation;
import org.audiveris.omr.sig.relation.ChordPedalRelation;
import org.audiveris.omr.sig.relation.ChordSentenceRelation;
import org.audiveris.omr.sig.relation.ChordSyllableRelation;
import org.audiveris.omr.sig.relation.FermataChordRelation;
import org.audiveris.omr.sig.relation.MarkerBarRelation;
import org.audiveris.omr.sig.relation.OctaveShiftChordRelation;
import org.audiveris.omr.sig.relation.Relation;
import org.audiveris.omr.sig.relation.SlurHeadRelation;
import org.audiveris.omr.text.FontInfo;
import org.audiveris.omr.text.TextRole;
import org.audiveris.omr.ui.symbol.TextFont;
import org.audiveris.omr.util.HorizontalSide;
import static org.audiveris.omr.util.HorizontalSide.LEFT;
import static org.audiveris.omr.util.HorizontalSide.RIGHT;
import static org.audiveris.omr.util.VerticalSide.BOTTOM;
import static org.audiveris.omr.util.VerticalSide.TOP;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Hand-rolled, non-JAXB MusicXML 4.0.3 partwise writer (Phase D, §22).
 *
 * <p>Walks the already-computed Audiveris {@link Score} model directly and
 * writes MusicXML text with {@link StringBuilder} only — no proxymusic
 * marshalling, no JAXB, no reflection. It mirrors
 * {@code PartwiseBuilder}'s traversal (processScore → processStub →
 * processLogicalPart → processSystem → processPart → processMeasure →
 * processChord → processNote) and the same per-method guards, so its
 * output should match Audiveris's own {@code ScoreExporter} element for
 * element on the same Score. Element order inside each container follows
 * the proxymusic JAXB {@code propOrder} (verified with javap on
 * proxymusic-4.0.3.jar), since JAXB reorders PartwiseBuilder's insertion
 * order into propOrder when marshalling.
 *
 * <p>TeaVM-safe by construction: only plain JDK classes already reachable
 * in the spike (StringBuilder, collections, Math, Locale, AWT geometry)
 * plus the Audiveris model classes the pipeline itself uses. No
 * {@code jakarta.xml.bind}, no {@code org.audiveris.proxymusic}, no
 * reflection, no {@code Class.forName}.
 */
public class MxlWriter
{
    private static final Logger logger = LoggerFactory.getLogger(MxlWriter.class);

    /** MusicXML version written (matches proxymusic 4.0.3 / Audiveris 5.11). */
    private static final String MUSICXML_VERSION = "4.0.3";

    /** Maximum level number for slurs / tuplets / octave shifts. */
    private static final int MAX_LEVEL_NUMBER = 16;

    /** Page margins in tenths (PartwiseBuilder.Constants). */
    private static final int PAGE_MARGIN = 80;

    /** Note type names, indexed as in MusicXML.getNoteTypeName. */
    private static final String[] NOTE_TYPE_NAMES = new String[] { "256th", "128th", "64th",
            "32nd", "16th", "eighth", "quarter", "half", "whole", "breve", "long" };

    //~ Instance fields ----------------------------------------------------------------------------

    private final Score score;

    /** Current context (mirrors PartwiseBuilder.Current). */
    private final Current current = new Current();

    /** Current flags (mirrors PartwiseBuilder.IsFirst). */
    private final IsFirst isFirst = new IsFirst();

    /** Map of OctaveShift numbers, reset for every (physical) Part. */
    private final Map<OctaveShiftInter, Integer> octaveShiftNumbers = new HashMap<>();

    /** Map of Slur numbers, reset for every LogicalPart. */
    private final Map<SlurInter, Integer> slurNumbers = new HashMap<>();

    /** Map of Tuplet numbers, reset for every Measure. */
    private final Map<TupletInter, Integer> tupletNumbers = new HashMap<>();

    /** Emitted clefs in the current logical part, for isNewClef. */
    private final List<ClefKey> emittedClefs = new ArrayList<>();

    /** Collected <credit> elements (sentences), emitted before part-list. */
    private final List<X> credits = new ArrayList<>();

    /** Movement number / title from sentences, if any. */
    private String movementNumber;

    private String movementTitle;

    /** Collected <creator>/<rights> identification children, if any. */
    private final List<X> idCreators = new ArrayList<>();

    private final List<X> idRights = new ArrayList<>();

    /** The <part-list> element, built first, emitted after identification. */
    private X partList;

    /** The <part> elements, one per logical part, in part-list order. */
    private final List<X> parts = new ArrayList<>();

    /** Source input path string (identification <source> + misc field). */
    private String sourcePath;

    //~ Constructors -------------------------------------------------------------------------------

    private MxlWriter (Score score)
    {
        this.score = score;
    }

    //~ Methods ------------------------------------------------------------------------------------

    /**
     * Build the MusicXML document for the provided score.
     *
     * @param score the Audiveris score (already read to PAGE or beyond)
     * @return the MusicXML document text
     */
    public static String build (Score score)
    {
        MxlWriter writer = new MxlWriter(score);
        return writer.processScore();
    }

    //------------//
    // processScore //
    //------------//
    private String processScore ()
    {
        try {
            Book book = score.getBook();
            Page firstPage = score.getFirstPage();

            try {
                sourcePath = book.getSomeInputPath().toAbsolutePath().toString();
            } catch (Exception ex) {
                sourcePath = null;
            }

            // Defaults (needs first page scale)
            X defaults = null;
            Scale scale = (firstPage != null) ? firstPage.getSheet().getScale() : null;
            current.scale = scale;
            if (scale != null) {
                defaults = new X("defaults");
                X scaling = new X("scaling");
                scaling.add(new X("millimeters").text(
                        String.format(Locale.US, "%.4f", (scale.getInterline() * 25.4 * 4) / 300)));
                scaling.add(new X("tenths").text("40"));
                defaults.add(scaling);

                X pageLayout = new X("page-layout");
                pageLayout.add(new X("page-height").text(
                        "" + (toTenths(firstPage.getSheet().getHeight()) + PAGE_MARGIN + PAGE_MARGIN)));
                pageLayout.add(new X("page-width").text(
                        "" + (toTenths(firstPage.getSheet().getWidth()) + PAGE_MARGIN + PAGE_MARGIN)));
                X pageMargins = new X("page-margins").attr("type", "both");
                pageMargins.add(new X("left-margin").text("" + PAGE_MARGIN));
                pageMargins.add(new X("right-margin").text("" + PAGE_MARGIN));
                pageMargins.add(new X("top-margin").text("" + PAGE_MARGIN));
                pageMargins.add(new X("bottom-margin").text("" + PAGE_MARGIN));
                pageLayout.add(pageMargins);
                defaults.add(pageLayout);

                java.awt.Font lyricFont = TextFont.TEXT_FONT_BASE;
                X lyricFontX = new X("lyric-font")
                        .attr("font-family", lyricFont.getName())
                        .attr("font-size", "" + lyricFont.getSize());
                if (lyricFont.isItalic()) {
                    lyricFontX.attr("font-style", "italic");
                }
                defaults.add(lyricFontX);
            }

            // PartList & sequence of parts (populates parts, credits, movement info)
            if (score.getLogicalParts() != null) {
                processPartList();
            }

            // Assemble the document in ScorePartwise propOrder:
            // work?, movement-number?, movement-title?, identification, defaults,
            // credit*, part-list, part*
            StringBuilder sb = new StringBuilder();
            sb.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
            sb.append("<!DOCTYPE score-partwise PUBLIC \"-//Recordare//DTD MusicXML 4.0.3 Partwise//EN\" \"http://www.musicxml.org/dtds/partwise.dtd\">\n");
            X root = new X("score-partwise").attr("version", MUSICXML_VERSION);
            if (movementNumber != null) {
                root.add(new X("movement-number").text(movementNumber));
            }
            if (movementTitle != null) {
                root.add(new X("movement-title").text(movementTitle));
            }
            root.add(buildIdentification());
            if (defaults != null) {
                root.add(defaults);
            }
            for (X credit : credits) {
                root.add(credit);
            }
            root.add(partList);
            for (X part : parts) {
                root.add(part);
            }
            root.render(sb, 0);
            return sb.toString();
        } catch (Exception ex) {
            logger.warn("Error visiting {}", score, ex);
            throw new RuntimeException(ex);
        }
    }

    //--------------------//
    // buildIdentification //
    //--------------------//
    private X buildIdentification ()
    {
        X identification = new X("identification");
        // Identification propOrder: creator*, rights*, encoding, source,
        // relation*, miscellaneous
        for (X creator : idCreators) {
            identification.add(creator);
        }
        for (X rights : idRights) {
            identification.add(rights);
        }
        X encoding = new X("encoding");
        encoding.add(new X("software").text(WellKnowns.TOOL_NAME + " " + WellKnowns.TOOL_REF));
        for (String attribute : new String[] { "new-system", "new-page" }) {
            encoding.add(new X("supports")
                    .attr("type", "yes").attr("element", "print")
                    .attr("attribute", attribute).attr("value", "yes"));
        }
        for (String element : new String[] { "accidental", "beam", "stem" }) {
            encoding.add(new X("supports").attr("type", "yes").attr("element", element));
        }
        identification.add(encoding);
        if (sourcePath != null) {
            identification.add(new X("source").text(sourcePath));
        }
        X misc = new X("miscellaneous");
        if (sourcePath != null) {
            misc.add(new X("miscellaneous-field").attr("name", "source-file").text(sourcePath));
        }
        // source-sheet-N fields were collected during processStub, in order
        for (X field : current.miscSheetFields) {
            misc.add(field);
        }
        if (!misc.kids.isEmpty()) {
            identification.add(misc);
        }
        return identification;
    }

    //-----------------//
    // processPartList //
    //-----------------//
    private void processPartList ()
    {
        partList = new X("part-list");
        Map<LogicalPart, X> partMap = new LinkedHashMap<>();

        for (LogicalPart p : score.getLogicalParts()) {
            X scorePartX = createScorePart(p);
            partList.add(scorePartX);
            partMap.put(p, current.partByLogical.get(p));
        }

        // Then, stub by stub, populate all parts in parallel
        for (SheetStub stub : score.getStubs()) {
            processStub(stub, partMap);
        }
    }

    //------------------//
    // createScorePart //
    //------------------//
    private X createScorePart (LogicalPart logicalPart)
    {
        X pmScorePart = new X("score-part").attr("id", logicalPart.getPid());
        pmScorePart.add(new X("part-name").text(
                (logicalPart.getName() != null) ? logicalPart.getName()
                        : logicalPart.getDefaultName()));
        String abbr = (logicalPart.getAbbreviation() != null) ? logicalPart.getAbbreviation()
                : ((logicalPart.getName() != null) ? logicalPart.getName()
                        : logicalPart.getDefaultName());
        pmScorePart.add(new X("part-abbreviation").text(abbr));

        // Is this a drum part?
        boolean isDrumLogicalPart = false;
        outermost:
        for (SheetStub stub : score.getStubs()) {
            Integer sheetPageId = score.getSheetPageId(stub.getNumber());
            Sheet sheet = stub.getSheet();
            Page page = sheet.getPages().get(sheetPageId - 1);
            for (SystemInfo system : page.getSystems()) {
                Part systemPart = system.getPartById(logicalPart.getId());
                if (systemPart != null) {
                    isDrumLogicalPart = systemPart.isDrumPart();
                    break outermost;
                }
            }
        }

        if (isDrumLogicalPart) {
            DrumSet drumSet = DrumSet.getInstance();
            for (DrumSet.DrumSound sound : DrumSet.DrumSound.values()) {
                String instId = pmScorePart.attrs.get("id") + "-I" + sound.getMidi();
                X scoreInstrument = new X("score-instrument").attr("id", instId);
                scoreInstrument.add(new X("instrument-name").text(sound.name()));
                pmScorePart.add(scoreInstrument);
                X midiInstrument = new X("midi-instrument").attr("id", instId);
                midiInstrument.add(new X("midi-channel").text("10"));
                midiInstrument.add(new X("midi-program").text("1"));
                midiInstrument.add(new X("midi-unpitched").text("" + sound.getMidi()));
                midiInstrument.add(new X("volume").text("" + score.getVolume()));
                pmScorePart.add(midiInstrument);
            }
        } else {
            Integer midiProgram = logicalPart.getMidiProgram();
            if (midiProgram == null) {
                midiProgram = logicalPart.getDefaultProgram();
            }
            X scoreInstrument = new X("score-instrument").attr("id", logicalPart.getPid() + "-I1");
            scoreInstrument.add(new X("instrument-name").text(
                    MidiAbstractions.getProgramName(midiProgram)));
            pmScorePart.add(scoreInstrument);
            X midiInstrument = new X("midi-instrument").attr("id", logicalPart.getPid() + "-I1");
            midiInstrument.add(new X("midi-channel").text(
                    "" + (1 + ((logicalPart.getId() - 1) % 16))));
            midiInstrument.add(new X("midi-program").text("" + midiProgram));
            midiInstrument.add(new X("volume").text("" + score.getVolume()));
            pmScorePart.add(midiInstrument);
        }

        // The <part> element itself is built during processStub
        X pmPart = new X("part").attr("id", logicalPart.getPid());
        parts.add(pmPart);
        current.partByLogical.put(logicalPart, pmPart);
        return pmScorePart;
    }

    //-------------//
    // processStub //
    //-------------//
    private void processStub (SheetStub stub,
                              Map<LogicalPart, X> partMap)
    {
        Integer sheetPageId = score.getSheetPageId(stub.getNumber());
        if (sheetPageId == null) {
            return;
        }

        Sheet sheet = stub.getSheet();
        Page page = sheet.getPages().get(sheetPageId - 1);

        // Source.encodePage equivalent: one misc field per sheet
        StringBuilder systems = new StringBuilder();
        for (SystemInfo system : page.getSystems()) {
            if (systems.length() > 0) {
                systems.append(' ');
            }
            systems.append(system.getId());
        }
        current.miscSheetFields.add(new X("miscellaneous-field")
                .attr("name", "source-sheet-" + stub.getNumber()).text(systems.toString()));

        current.page = page;
        current.pageMeasureIdOffset = score.getMeasureIdOffset(page);
        current.scale = page.getSheet().getScale();
        page.resetDurationDivisor();

        isFirst.page = score.isFirst(page);
        isFirst.system = true;
        isFirst.measure = true;
        isFirst.part = true;

        for (Map.Entry<LogicalPart, X> entry : partMap.entrySet()) {
            processLogicalPart(entry.getKey(), entry.getValue());
            isFirst.part = false;
        }
    }

    //--------------------//
    // processLogicalPart //
    //--------------------//
    private void processLogicalPart (LogicalPart logicalPart,
                                     X pmPart)
    {
        current.logicalPart = logicalPart;
        current.pmPart = pmPart;
        current.keys.clear();
        emittedClefs.clear();

        isFirst.system = true;
        slurNumbers.clear();

        for (SystemInfo system : current.page.getSystems()) {
            processSystem(system);
        }
    }

    //---------------//
    // processSystem //
    //---------------//
    private void processSystem (SystemInfo system)
    {
        try {
            current.system = system;
            current.multipleRests = system.getSig().inters(MultipleRestInter.class);
            isFirst.measure = true;

            Part systemPart = system.getPartById(current.logicalPart.getId());
            if (systemPart != null) {
                current.isDrumPart = systemPart.isDrumPart();
                processPart(systemPart);
            } else {
                Part dummyPart = system.getFirstStandardPart().createDummyPart(
                        current.logicalPart.getId());
                current.isDrumPart = dummyPart.isDrumPart();
                processPart(dummyPart);
            }

            // Sentences in system
            if (isFirst.part) {
                for (Inter inter : system.getSig().inters(SentenceInter.class)) {
                    processSentence((SentenceInter) inter);
                }
            }

            if (!isFirst.measure) {
                isFirst.system = false;
            }
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", system, current.page, ex);
        }
    }

    //-------------//
    // processPart //
    //-------------//
    private void processPart (Part part)
    {
        try {
            octaveShiftNumbers.clear();

            for (Measure measure : part.getMeasures()) {
                if (!measure.getStack().isCautionary()) {
                    processMeasure(measure);
                }
            }
        } catch (Exception ex) {
            logger.warn("Error visiting {}", part, ex);
        }
    }

    //----------------//
    // processMeasure //
    //----------------//
    private void processMeasure (Measure measure)
    {
        try {
            boolean isPageFirstMeasure = isFirst.system && isFirst.measure;
            boolean isScoreFirstMeasure = isFirst.page && isPageFirstMeasure;
            MeasureStack stack = measure.getStack();

            current.measure = measure;
            tupletNumbers.clear();

            Set<MeasureRepeatInter> repeats = measure.getMeasureRepeats();

            if (!current.repeatCopying) {
                // Allocate a new measure shell
                current.pmMeasure = new X("measure").attr("number", stack.getScoreId(current.pageMeasureIdOffset));
                current.pmPart.add(current.pmMeasure);
                current.items = new ArrayList<>();
                current.attrs = new Attrs();

                if (current.repeatStarted && repeats.isEmpty()) {
                    X measureStyle = new X("measure-style");
                    measureStyle.add(new X("measure-repeat").attr("type", "stop"));
                    addMeasureStyle(measureStyle);
                    current.repeatStarted = false;
                }

                if (!measure.isDummy()) {
                    current.pmMeasure.attr("width", "" + toTenths(measure.getWidth()));
                }

                if (stack.isImplicit()) {
                    current.pmMeasure.attr("implicit", "yes");
                }

                // Print?
                new MeasurePrint(measure).process();

                // Left/mid barline?
                PartBarline mid = measure.getMidPartBarline();
                if (mid != null) {
                    processBarline(mid, "middle");
                } else {
                    processBarline(getBarlineOnLeft(measure), "left");
                }

                // Divisions?
                if (isPageFirstMeasure) {
                    try {
                        setDivisions(current.page.simpleDurationOf(Rational.QUARTER));
                    } catch (Exception ex) {
                        if (current.page.getDurationDivisor() == null) {
                            logger.warn("Not able to infer division value for part {} in {}",
                                    current.logicalPart.getPid(), current.page);
                        } else {
                            logger.warn("Error on divisions in {}", current.page, ex);
                        }
                    }
                }

                // Number of staves, if > 1
                if (isScoreFirstMeasure && current.logicalPart.isMultiStaff()) {
                    setStaves(current.logicalPart.getStaffCount());
                }

                // Insert KeySignature(s), if any
                processKeys();

                // Insert TimeSignature, if any
                if (measure.getTimeSignature() != null) {
                    processTime(measure.getTimeSignature());
                }
            }

            // Clefs may be inserted further down the measure
            ClefIterators clefIters = new ClefIterators(measure);

            // Wedges are collected and sorted for the whole measure
            WedgeIterators wedgeIters = new WedgeIterators(measure);

            // Insert clefs that occur before the first time slot
            List<Slot> slots = stack.getSlots();
            if (slots.isEmpty()) {
                clefIters.push(null, null);
                wedgeIters.push(Rational.ZERO);
            } else {
                clefIters.push(slots.get(0).getXOffset(), null);
                wedgeIters.push(Rational.ZERO);
            }

            // Rehearsal mark?
            for (RehearsalInter rehearsal : measure.getRehearsals()) {
                processRehearsal(rehearsal);
            }

            // Now voice per voice
            Rational timeCounter = Rational.ZERO;

            for (Voice voice : measure.getVoices()) {
                current.voice = voice;

                // Need a backup?
                if (!timeCounter.equals(Rational.ZERO)) {
                    insertBackup(timeCounter);
                    timeCounter = Rational.ZERO;
                }

                if (voice.isMeasureRest()) {
                    AbstractChordInter chord = voice.getWholeChord();
                    clefIters.push(measure.getWidth(), chord.getTopStaff());
                    wedgeIters.push(chord.getTimeOffset());
                    processChord(chord);
                    if (stack.getActualDuration() != null) {
                        timeCounter = stack.getActualDuration();
                    }
                } else {
                    for (Slot slot : stack.getSlots()) {
                        SlotVoice info = voice.getSlotInfo(slot);
                        if ((info != null) && (info.status == SlotVoice.ChordStatus.BEGIN)) {
                            AbstractChordInter chord = info.chord;
                            clefIters.push(slot.getXOffset(), chord.getTopStaff());

                            Rational timeOffset = chord.getTimeOffset();
                            // §34: null timeOffset (un-timed chord, see sort
                            // above) — no forward to insert; wedgeIters.push
                            // already flushes on null.
                            if ((timeOffset != null) && (timeCounter.compareTo(timeOffset) < 0)) {
                                insertForward(timeOffset.minus(timeCounter), chord);
                                timeCounter = timeOffset;
                            }

                            wedgeIters.push(timeOffset);

                            if (chord instanceof HeadChordInter headChord) {
                                SmallChordInter small = headChord.getGraceChord();
                                if (small != null) {
                                    BeamGroupInter group = small.getBeamGroup();
                                    if (group != null) {
                                        for (AbstractChordInter ch : group.getChords()) {
                                            processChord(ch);
                                        }
                                    } else {
                                        processChord(small);
                                    }
                                }
                            }

                            processChord(chord);
                            // §34: getDuration() is null only for measure
                            // rests (never in this branch), but guard it the
                            // same way — a null here used to NPE and drop the
                            // measure on desktop / trap the run under TeaVM.
                            Rational chordDur = chord.getDuration();
                            if (chordDur != null) {
                                timeCounter = timeCounter.plus(chordDur);
                            }
                        }
                    }
                }

                current.endVoice();
            }

            // Clefs that occur after time slots, if any
            clefIters.push(null, null);

            // Wedges that occur after time slots, if any
            wedgeIters.push(null);

            // Right Barline
            if (!measure.isDummy()) {
                processBarline(measure.getRightPartBarline(), "right");
            }

            // Multiple rest?
            if (stack.isMultiRest()) {
                insertMultipleRest(stack);
            }

            if (!repeats.isEmpty()) {
                MeasureRepeatInter repeatSign = repeats.iterator().next();
                int slashes = repeatSign.getShape().getSlashCount();

                if (!current.repeatStarted) {
                    X measureStyle = new X("measure-style");
                    X repeat = new X("measure-repeat").attr("type", "start")
                            .attr("slashes", "" + slashes);
                    measureStyle.add(repeat);
                    addMeasureStyle(measureStyle);
                    current.repeatStarted = true;
                }

                List<Measure> toCopy = new ArrayList<>();
                Measure precMeasure = measure.getPrecedingInScore();
                int countLeft = slashes;
                while (countLeft > 0 && precMeasure != null) {
                    if (precMeasure.getMeasureRepeats().isEmpty()) {
                        toCopy.add(0, precMeasure);
                        if (--countLeft == 0) {
                            break;
                        }
                    } else if (!toCopy.isEmpty()) {
                        logger.warn("Abnormal measure sequence before repeat sign {}", measure);
                        break;
                    }
                    precMeasure = precMeasure.getPrecedingInScore();
                }

                for (int i = 0, iMax = toCopy.size() - 1; i <= iMax; i++) {
                    Measure sourceMeasure = toCopy.get(i);
                    current.repeatCopying = true;
                    processMeasure(sourceMeasure);
                    if (i < iMax) {
                        renderMeasure();
                        // Allocate a new Measure shell
                        current.pmMeasure = new X("measure").attr("number",
                                stack.getScoreId(current.pageMeasureIdOffset) + "+" + (i + 1));
                        current.pmPart.add(current.pmMeasure);
                        current.items = new ArrayList<>();
                        current.attrs = new Attrs();
                    }
                    current.repeatCopying = false;
                }
            }
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", measure, current.page, ex);
            if (current.pmMeasure != null) {
                current.pmPart.kids.remove(current.pmMeasure);
            }
        }

        if (!current.repeatCopying) {
            renderMeasure();
        }

        current.endMeasure();
        tupletNumbers.clear();
        isFirst.measure = false;
    }

    //--------------//
    // insertBackup //
    //--------------//
    private void insertBackup (Rational delta)
    {
        try {
            X backup = new X("backup");
            backup.add(new X("duration").text("" + current.page.simpleDurationOf(delta)));
            current.items.add(backup);
        } catch (Exception ex) {
            if (current.page.getDurationDivisor() != null) {
                logger.warn("Not able to insert backup {} at {} in {}", delta, current.measure,
                        current.page, ex);
            }
        }
    }

    //---------------//
    // insertForward //
    //---------------//
    private void insertForward (Rational delta,
                                AbstractChordInter chord)
    {
        try {
            X forward = new X("forward");
            forward.add(new X("duration").text("" + current.page.simpleDurationOf(delta)));
            forward.add(new X("voice").text("" + current.voice.getId()));
            insertStaffId(forward, chord.getTopStaff());
            current.items.add(forward);
        } catch (Exception ex) {
            if (current.page.getDurationDivisor() != null) {
                logger.warn("Not able to insert forward {} for {} at {} in {}", delta, chord,
                        current.measure, current.page, ex);
            }
        }
    }

    //--------------------//
    // insertMultipleRest //
    //--------------------//
    private void insertMultipleRest (MeasureStack stack)
    {
        Integer count = stack.getMultipleMeasureCount(current.multipleRests);
        if (count != null) {
            if (count == 0) {
                count = 1;
                logger.warn("{} Multirest with no measure count, using default value {}",
                        current.measure, count);
            }
            AbstractTimeInter timeSig = stack.getCurrentTimeSignature();
            int dur = current.page.simpleDurationOf(
                    timeSig != null ? timeSig.getTimeRational().getValue() : Rational.ONE);
            for (int num = 0; num < count; num++) {
                if (num == 0) {
                    X measureStyle = new X("measure-style");
                    measureStyle.add(new X("multiple-rest").text("" + count));
                    addMeasureStyle(measureStyle);
                }
                X note = new X("note").attr("print-object", "no");
                X rest = new X("rest").attr("measure", "yes");
                note.add(rest);
                note.add(new X("duration").text("" + dur));
                current.items.add(note);
                if (num != count - 1) {
                    renderMeasure();
                    current.pmMeasure = new X("measure").attr("number",
                            stack.getScoreId(current.pageMeasureIdOffset + num + 1));
                    current.pmPart.add(current.pmMeasure);
                    current.items = new ArrayList<>();
                    current.attrs = new Attrs();
                }
            }
        }
    }

    //---------------//
    // insertStaffId //
    //---------------//
    /** Add a <staff> child if the current logical part has more than one staff. */
    private void insertStaffId (X parent,
                                Staff staff)
    {
        if (current.logicalPart.isMultiStaff()) {
            parent.add(new X("staff").text("" + (1 + staff.getIndexInPart())));
        }
    }

    //------------------//
    // getBarlineOnLeft //
    //------------------//
    private PartBarline getBarlineOnLeft (Measure measure)
    {
        if (measure.getLeftPartBarline() != null) {
            return measure.getLeftPartBarline();
        } else if (isFirst.measure) {
            return measure.getPart().getLeftPartBarline();
        } else {
            Measure prevMeasure = measure.getPrecedingInSystem();
            if (prevMeasure != null) {
                if (!prevMeasure.isDummy()) {
                    return prevMeasure.getRightPartBarline();
                }
            }
        }
        return null;
    }

    //----------------//
    // processBarline //
    //----------------//
    private void processBarline (PartBarline partBarline,
                                 String location)
    {
        try {
            if (partBarline == null) {
                return;
            }
            MeasureStack stack = current.measure.getStack();
            PartBarline.Style style = partBarline.getStyle();
            List<FermataInter> fermatas = partBarline.getFermatas();
            EndingInter ending = partBarline.getEnding(
                    location.equals("right") ? RIGHT : LEFT);
            String endingValue = (ending != null) ? ending.getValue() : null;
            String endingNumber = (ending != null) ? ending.getExportedNumber() : null;

            if (endingNumber == null && ending != null) {
                boolean isFirstNumber = true;
                Measure prevMeasure = current.measure.getPrecedingInPage();
                if (prevMeasure != null) {
                    PartBarline prevBar = prevMeasure.getRightPartBarline();
                    if (prevBar != null && prevBar.getEnding(RIGHT) != null) {
                        isFirstNumber = false;
                    }
                }
                ending.setNumber(endingNumber = isFirstNumber ? "1" : "2");
            }

            boolean needed = false;
            needed |= (partBarline == current.measure.getLeftPartBarline());
            needed |= (location.equals("left") && (stack.isRepeat(LEFT) || (ending != null)));
            needed |= location.equals("middle");
            needed |= (location.equals("right")
                    && (stack.isRepeat(RIGHT) || (ending != null) || !fermatas.isEmpty()
                            || (style != null && style != PartBarline.Style.REGULAR)));

            if (needed) {
                try {
                    X pmBarline = new X("barline")
                            .attr("location", location.equals("right") ? "right" : "left");
                    if (style != null) {
                        X barStyle = new X("bar-style");
                        barStyle.text(barStyleOf(style, location));
                        pmBarline.add(barStyle);
                    }
                    if (location.equals("left") || location.equals("middle")) {
                        if (stack.isRepeat(LEFT)) {
                            pmBarline.add(new X("repeat").attr("direction", "forward"));
                        }
                        if (ending != null) {
                            pmBarline.add(buildEnding(ending, endingNumber, endingValue, true));
                        }
                    } else { // right
                        if (stack.isRepeat(RIGHT)) {
                            pmBarline.add(new X("repeat").attr("direction", "backward"));
                        }
                        if (!fermatas.isEmpty()) {
                            for (FermataInter f : fermatas) {
                                if (f.getShape() == Shape.FERMATA) {
                                    pmBarline.add(buildFermata(f, true));
                                }
                                break;
                            }
                            for (ListIterator<FermataInter> it = fermatas.listIterator(
                                    fermatas.size()); it.hasPrevious();) {
                                FermataInter f = it.previous();
                                if (f.getShape() == Shape.FERMATA_BELOW) {
                                    pmBarline.add(buildFermata(f, true));
                                }
                                break;
                            }
                        }
                        if (ending != null) {
                            pmBarline.add(buildEnding(ending, endingNumber, endingValue, false));
                        }
                    }
                    current.items.add(pmBarline);
                } catch (Exception ex) {
                    logger.warn("Cannot process barline {} in {}", partBarline, current.page, ex);
                }
            }

            // Markers (Coda, Segno)?
            if (!location.equals("right")) {
                Part part = current.measure.getPart();
                Measure topMeasure = current.measure.getStack().getFirstMeasure();
                PartBarline topPartBarline = getBarlineOnLeft(topMeasure);
                if (topPartBarline != null) {
                    StaffBarlineInter topBarline = topPartBarline.getStaffBarline(
                            part, part.getFirstStaff());
                    for (Inter marker : topBarline.getRelatedInters(MarkerBarRelation.class)) {
                        processMarker((MarkerInter) marker);
                    }
                }
            }
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {} {} location:{}", partBarline, current.page,
                    current.measure, location, ex);
        }
    }

    /** Build an <ending> element; left=true for the start side, false for the stop side. */
    private X buildEnding (EndingInter ending,
                           String endingNumber,
                           String endingValue,
                           boolean left)
    {
        X pmEnding = new X("ending");
        Staff staff = current.measure.getPart().getFirstStaff();
        if (left) {
            Point2D pt = ending.getLine().getP1();
            pmEnding.attr("default-y", "" + yOf(pt, staff));
            Line2D leg = ending.getLeftLeg();
            if (leg != null) {
                pmEnding.attr("end-length", "" + toTenths(leg.getY2() - pt.getY()));
            }
            pmEnding.attr("type", "start");
            pmEnding.attr("number", endingNumber);
            if (endingValue != null) {
                pmEnding.text(endingValue);
            }
        } else {
            Point2D pt = ending.getLine().getP2();
            pmEnding.attr("default-y", "" + yOf(pt, staff));
            Line2D leg = ending.getRightLeg();
            if (leg != null) {
                pmEnding.attr("end-length", "" + toTenths(leg.getY2() - pt.getY()));
                pmEnding.attr("type", "stop");
            } else {
                pmEnding.attr("type", "discontinue");
            }
            pmEnding.attr("number", endingNumber);
        }
        return pmEnding;
    }

    //-------------//
    // processKeys //
    //-------------//
    private void processKeys ()
    {
        if (current.measure.hasKeys()) {
            if (current.measure.hasSameKeys()) {
                processKey(current.measure.getKey(0), true);
            } else {
                int staffCount = current.measure.getPart().getStaves().size();
                for (int index = 0; index < staffCount; index++) {
                    KeyInter key = current.measure.getKey(index);
                    processKey(key, false);
                }
            }
        } else {
            if (isFirst.measure) {
                processKeyVoid();
            }
        }
    }

    //------------//
    // processKey //
    //------------//
    private void processKey (KeyInter keySignature,
                             boolean global)
    {
        try {
            if (keySignature == null) {
                return;
            }

            // §44.1: a KEY_CANCEL key can carry a null fifths (KeyInter.getFifths()
            // returns the field as-is for cancels; the javadoc promises 0, but a
            // cancel built by KeyInter.createAdded keeps fifths null). Stock
            // PartwiseBuilder does new BigInteger("" + getFifths()) on it, throws
            // NumberFormatException("null"), and skips the key via its catch.
            // Our writer must skip BEFORE the unboxing: under TeaVM WasmGC a null
            // unbox is an uncatchable trap, not a catchable NPE (same family as
            // the §34 null timeOffset). Skipping emits no <key> element for the
            // cancel, exactly like stock's observable output.
            Integer fifthsObj = keySignature.getFifths();

            if (fifthsObj == null) {
                logger.warn("Skipping {} with null fifths in {}", keySignature, current.page);

                return;
            }

            int fifths = fifthsObj.intValue();
            if (global) {
                int staffCount = current.measure.getPart().getStaves().size();
                boolean isNew = false;
                for (int index = 0; index < staffCount; index++) {
                    Integer cur = current.keys.get(index);
                    if ((cur == null) || (cur.intValue() != fifths)) {
                        isNew = true;
                        break;
                    }
                }
                if (isNew) {
                    addKey(new X("key")
                            .add(new X("fifths").text("" + fifths)));
                    for (int index = 0; index < staffCount; index++) {
                        current.keys.put(index, fifths);
                    }
                }
            } else {
                int staffIndex = keySignature.getStaff().getIndexInPart();
                Integer cur = current.keys.get(staffIndex);
                if ((cur == null) || (cur.intValue() != fifths)) {
                    X key = new X("key");
                    key.add(new X("fifths").text("" + fifths));
                    key.attr("number", "" + (1 + staffIndex));
                    // Key propOrder: cancel?, fifths, mode?, ..., number is an
                    // attribute, so it stays on the element.
                    addKey(key);
                    current.keys.put(staffIndex, fifths);
                }
            }
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", keySignature, current.page, ex);
        }
    }

    //----------------//
    // processKeyVoid //
    //----------------//
    private void processKeyVoid ()
    {
        try {
            int staffCount = current.measure.getPart().getStaves().size();
            boolean isNew = false;
            for (int index = 0; index < staffCount; index++) {
                Integer cur = current.keys.get(index);
                if ((cur != null) && (cur.intValue() != 0)) {
                    isNew = true;
                    break;
                }
            }
            if (isNew) {
                addKey(new X("key").add(new X("fifths").text("0")));
                for (int index = 0; index < staffCount; index++) {
                    current.keys.put(index, 0);
                }
            }
        } catch (Exception ex) {
            logger.warn("Error in processKeyVoid in {}", current.page, ex);
        }
    }

    //-------------//
    // processTime //
    //-------------//
    private void processTime (AbstractTimeInter timeSig)
    {
        processTime(timeSig.getNumerator(), timeSig.getDenominator(), timeSig.getShape());
    }

    private void processTime (int num,
                              int den,
                              Shape shape)
    {
        X time = new X("time");
        time.add(new X("beats").text("" + num));
        time.add(new X("beat-type").text("" + den));
        if (shape != null) {
            switch (shape) {
                case COMMON_TIME -> time.attr("symbol", "common");
                case CUT_TIME -> time.attr("symbol", "cut");
                default -> {
                }
            }
        }
        addTime(time);
    }

    //-------------//
    // processClef //
    //-------------//
    private void processClef (ClefInter clef)
    {
        try {
            X pmClef = buildClef(clef);
            if (isNewClef(pmClef)) {
                addClef(pmClef);
            }
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", clef, current.page, ex);
        }
    }

    private X buildClef (ClefInter clef)
    {
        X pmClef = new X("clef");
        if (current.logicalPart.isMultiStaff()) {
            pmClef.attr("number", "" + (1 + clef.getStaff().getIndexInPart()));
        }
        Shape shape = clef.getShape();
        if (shape != Shape.PERCUSSION_CLEF) {
            pmClef.add(new X("line").text("" + (3 - (int) Math.rint(clef.getPitch() / 2.0))));
        }
        // Clef propOrder: sign, line, clef-octave-change
        String sign;
        Integer octaveChange = null;
        switch (shape) {
            case G_CLEF, G_CLEF_SMALL -> sign = "G";
            case G_CLEF_8VA -> {
                sign = "G";
                octaveChange = 1;
            }
            case G_CLEF_8VB -> {
                sign = "G";
                octaveChange = -1;
            }
            case C_CLEF -> sign = "C";
            case F_CLEF, F_CLEF_SMALL -> sign = "F";
            case F_CLEF_8VA -> {
                sign = "F";
                octaveChange = 1;
            }
            case F_CLEF_8VB -> {
                sign = "F";
                octaveChange = -1;
            }
            case PERCUSSION_CLEF -> sign = "percussion";
            default -> {
                logger.error("Clef shape not exported {}", shape);
                sign = "G";
            }
        }
        // Rebuild in propOrder: sign first, then line, then octave-change.
        X ordered = new X("clef");
        if (pmClef.attrs.containsKey("number")) {
            ordered.attr("number", pmClef.attrs.get("number"));
        }
        ordered.add(new X("sign").text(sign));
        for (X kid : pmClef.kids) {
            ordered.add(kid);
        }
        if (octaveChange != null) {
            ordered.add(new X("clef-octave-change").text("" + octaveChange));
        }
        return ordered;
    }

    private boolean isNewClef (X newClef)
    {
        String num = newClef.attrs.get("number");
        String sign = textOf(newClef, "sign");
        String line = textOf(newClef, "line");
        String oct = textOf(newClef, "clef-octave-change");
        for (int i = emittedClefs.size() - 1; i >= 0; i--) {
            ClefKey prev = emittedClefs.get(i);
            if (java.util.Objects.equals(prev.number, num)) {
                return !(java.util.Objects.equals(prev.sign, sign)
                        && java.util.Objects.equals(prev.line, line)
                        && java.util.Objects.equals(prev.octaveChange, oct));
            }
        }
        emittedClefs.add(new ClefKey(num, sign, line, oct));
        return true;
    }

    //--------------//
    // processChord //
    //--------------//
    private void processChord (AbstractChordInter chord)
    {
        checkOctaveShift(chord, LEFT);
        for (Inter inter : chord.getNotes()) {
            processNote((AbstractNoteInter) inter);
        }
        checkOctaveShift(chord, RIGHT);
    }

    //-------------//
    // processNote //
    //-------------//
    // Note children are collected into slots and assembled at the end in
    // proxymusic Note propOrder (grace, chord, pitch/unpitched/rest,
    // duration, tie, instrument, voice, type, dot, accidental,
    // time-modification, stem, notehead, staff, beam, notations, lyric),
    // because PartwiseBuilder's call order differs from JAXB's marshal order.
    private void processNote (AbstractNoteInter note)
    {
        try {
            SIGraph sig = note.getSig();
            Staff staff = note.getStaff();
            AbstractChordInter chord = note.getChord();
            boolean isFirstInChord = chord.getNotes().indexOf(note) == 0;

            current.note = note;
            current.notations = null;
            current.pendingTies.clear();
            current.pendingLyrics.clear();

            // For first note in chord: chord events (directions etc.),
            // emitted as measure items BEFORE the note itself.
            if (isFirstInChord) {
                if (!current.measure.isDummy() && !current.repeatCopying) {
                    for (Relation rel : sig.edgesOf(chord)) {
                        Inter other = sig.getOppositeInter(chord, rel);
                        if (rel instanceof ChordSentenceRelation) {
                            processDirection((SentenceInter) other);
                        } else if (rel instanceof ChordBowRelation) {
                            processBow((BowInter) other);
                        } else if (rel instanceof ChordPedalRelation) {
                            processPedal((PedalInter) other);
                        } else if (rel instanceof ChordDynamicsRelation) {
                            processDynamics((DynamicsInter) other);
                        } else if (rel instanceof ChordArticulationRelation) {
                            processArticulation((ArticulationInter) other);
                        } else if (rel instanceof ChordPauseRelation) {
                            processPause((AbstractPauseInter) other);
                        } else if (rel instanceof ChordOrnamentRelation) {
                            processOrnament((OrnamentInter) other);
                        } else if (rel instanceof ChordArpeggiatoRelation) {
                            processArpeggiato((ArpeggiatoInter) other);
                        } else if (rel instanceof FermataChordRelation) {
                            processFermata((FermataInter) other, null);
                        } else if (rel instanceof ChordNameRelation) {
                            processChordName((ChordNameInter) other);
                        }
                    }
                }
            }

            X pmNote = new X("note");
            if (!current.measure.isDummy() && !current.repeatCopying) {
                int noteLeft = note.getCenterLeft().x;
                pmNote.attr("default-x",
                        "" + toTenths(noteLeft - current.measure.getAbscissa(LEFT, staff)));
            }
            current.pmNote = pmNote;

            boolean isMeasureRest = false;
            X graceX = null;
            X contentX = null;
            X motifNotehead = null;
            X timeModX = null;
            X durationX = null;
            X instrumentX = null;
            X voiceX = null;
            X typeX = null;
            X accidentalX = null;
            X stemX = null;
            X staffX = null;
            List<X> beams = new ArrayList<>();
            int dots = 0;

            // Rest?
            if (note.getShape().isRest()) {
                RestChordInter restChord = (RestChordInter) chord;
                X rest = new X("rest");
                if (current.measure.isDummy() || current.measure.isMeasureRest(restChord)) {
                    rest.attr("measure", "yes");
                    isMeasureRest = true;
                }
                if (!current.measure.isDummy() && !staff.isOneLineStaff()) {
                    rest.add(new X("display-step").text(stepOf(note.getStep())));
                    rest.add(new X("display-octave").text("" + (note.getOctave() + getOctaveShift(note))));
                }
                contentX = rest;
            } else {
                HeadChordInter headChord = (HeadChordInter) chord;
                if (!current.measure.isDummy()) {
                    if (isFirstInChord && note.getShape().isSmallHead()) {
                        graceX = new X("grace");
                        if (headChord.hasSlash()) {
                            graceX.attr("slash", "yes");
                        }
                    }
                }

                if (staff.isOneLineStaff()) {
                    X unpitched = new X("unpitched");
                    unpitched.add(new X("display-step").text("E"));
                    unpitched.add(new X("display-octave").text("4"));
                    contentX = unpitched;
                } else if (current.isDrumPart) {
                    X unpitched = new X("unpitched");
                    unpitched.add(new X("display-step").text(stepOf(note.getStep())));
                    unpitched.add(new X("display-octave").text("" + note.getOctave()));
                    contentX = unpitched;
                } else {
                    X pitch = new X("pitch");
                    pitch.add(new X("step").text(stepOf(note.getStep())));
                    HeadInter head = (HeadInter) note;
                    Integer fifths = current.keys.get(staff.getIndexInPart());
                    int alter = head.getAlteration(fifths);
                    if (alter != 0) {
                        pitch.add(new X("alter").text("" + alter));
                    }
                    pitch.add(new X("octave").text("" + (note.getOctave() + getOctaveShift(note))));
                    contentX = pitch;
                }

                HeadMotif motif = note.getShape().getHeadMotif();
                if (motif != HeadMotif.oval && motif != HeadMotif.small) {
                    motifNotehead = new X("notehead");
                    switch (motif) {
                        case cross -> motifNotehead.text("x");
                        case diamond -> motifNotehead.text("diamond");
                        case triangle -> motifNotehead.text("inverted triangle");
                        case circle -> motifNotehead.text("circle-x");
                        default -> {
                        }
                    }
                }
            }

            // Tuplet factor?
            if (chord.getTupletFactor() != null) {
                timeModX = new X("time-modification");
                timeModX.add(new X("actual-notes").text("" + chord.getTupletFactor().actualDen));
                timeModX.add(new X("normal-notes").text("" + chord.getTupletFactor().actualNum));
                TupletInter tuplet = chord.getTuplet();
                Rational chordDur = chord.getDurationSansDotOrTuplet();
                if (!chordDur.equals(tuplet.getBaseDuration())) {
                    timeModX.add(new X("normal-type").text(getNoteTypeName(tuplet.getBaseDuration())));
                }
                if (isFirstInChord) {
                    List<AbstractChordInter> embraced = tuplet.getChords();
                    if ((embraced.get(0) == chord) || (embraced.get(embraced.size() - 1) == chord)) {
                        processTuplet(tuplet);
                    }
                }
            }

            // Duration (not for grace note)
            if (graceX == null) {
                try {
                    Rational dur;
                    if (chord.isMeasureRest()) {
                        Rational measureDur = current.measure.getStack().getActualDuration();
                        dur = (measureDur != null) ? measureDur : Rational.ONE;
                    } else {
                        dur = chord.getDuration();
                    }
                    durationX = new X("duration").text("" + current.page.simpleDurationOf(dur));
                } catch (Exception ex) {
                    if (current.page.getDurationDivisor() != null) {
                        logger.warn("Not able to get duration of {} in {}", note, current.page, ex);
                    }
                }
            }

            // Instrument (for unpitched percussion)
            if (!note.getShape().isRest() && current.isDrumPart) {
                HeadMotif motif = note.getShape().getHeadMotif();
                int notePitch = note.getIntegerPitch();
                if (motif == HeadMotif.circle) {
                    motif = HeadMotif.cross;
                    if (notePitch == -5 || notePitch == 5) {
                        notePitch = -3;
                    }
                } else if (motif == HeadMotif.small) {
                    motif = HeadMotif.oval;
                }
                HeadInter head = (HeadInter) note;
                PlayingInter playing = head.getPlayingSign();
                Shape sign = (playing != null) ? playing.getShape() : null;
                DrumSet.MotifSign ms = new DrumSet.MotifSign(motif, sign);
                DrumSet drumSet = DrumSet.getInstance();
                int lineCount = staff.getLineCount();
                Map<Integer, Map<DrumSet.MotifSign, DrumSet.DrumInstrument>> staffSet =
                        drumSet.getStaffSet(lineCount);
                if (staffSet == null) {
                    logger.warn("No drum set defined for staff size {}", lineCount);
                } else {
                    Map<DrumSet.MotifSign, DrumSet.DrumInstrument> map = staffSet.get(notePitch);
                    DrumSet.DrumInstrument drum = (map != null) ? map.get(ms) : null;
                    if (drum != null) {
                        instrumentX = new X("instrument")
                                .attr("id", current.logicalPart.getPid() + "-I" + drum.sound.getMidi());
                    } else {
                        logger.warn("No instrument for note {} {}", note, ms);
                    }
                }
            }

            // Voice
            Voice voice = chord.getVoice();
            if (voice != null) {
                voiceX = new X("voice").text("" + voice.getId());
            } else {
                logger.warn("No voice for {}", chord);
            }

            // Type
            if (!current.measure.isDummy()) {
                if (!isMeasureRest) {
                    typeX = new X("type").text(getNoteTypeName(note));
                }
            }

            // Dots
            dots = chord.getDotsNumber();

            // For specific mirrored note
            if (note.getMirror() != null) {
                int fbn = note.getChord().getBeamsOrFlagsNumber();
                if ((fbn > 0) && (note.getShape() == Shape.NOTEHEAD_VOID)) {
                    motifNotehead = new X("notehead").attr("filled", "no").text("normal");
                }
            }

            // Stem?
            if (chord.getStem() != null) {
                stemX = new X("stem");
                Point tail = chord.getTailLocation();
                if (!staff.isOneLineStaff() && !current.repeatCopying) {
                    stemX.attr("default-y", "" + yOf(tail, staff));
                }
                stemX.text((tail.y < note.getCenter().y) ? "up" : "down");
            }

            // Staff?
            if (current.logicalPart.isMultiStaff()) {
                staffX = new X("staff").text("" + (1 + staff.getIndexInPart()));
            }

            if (!note.getShape().isRest()) {
                // Accidental?
                HeadInter head = (HeadInter) note;
                AlterInter alter = head.getAccidental();
                if (alter != null) {
                    accidentalX = new X("accidental").text(accidentalValueOf(alter.getShape()));
                }

                // Beams?
                int beamCounter = 0;
                for (AbstractBeamInter beam : chord.getBeams()) {
                    X pmBeam = new X("beam").attr("number", "" + (1 + beamCounter++));
                    if (beam.isHook()) {
                        if (beam.getCenter().x > chord.getStem().getCenter().x) {
                            pmBeam.text("forward hook");
                        } else {
                            pmBeam.text("backward hook");
                        }
                    } else {
                        List<AbstractChordInter> chords = beam.getChords();
                        if (chords.get(0) == chord) {
                            pmBeam.text("begin");
                        } else if (chords.get(chords.size() - 1) == chord) {
                            pmBeam.text("end");
                        } else {
                            pmBeam.text("continue");
                        }
                    }
                    beams.add(pmBeam);
                }

                // Fingering?
                FingeringInter fingering = head.getFingering();
                if (fingering != null) {
                    X pmFingering = new X("fingering")
                            .attr("placement", (fingering.getCenter().y < head.getCenter().y) ? "above" : "below")
                            .attr("default-y", "" + yOf(fingering.getCenter(), staff))
                            .text(fingering.getSymbolString());
                    getTechnical().add(pmFingering);
                }

                // Plucking?
                PluckingInter plucking = head.getPlucking();
                if (plucking != null) {
                    X placement = new X("pluck")
                            .attr("placement", (plucking.getCenter().y < head.getCenter().y) ? "above" : "below")
                            .attr("default-y", "" + yOf(plucking.getCenter(), staff))
                            .text(plucking.getSymbolString());
                    getTechnical().add(placement);
                }
            }

            if (!current.measure.isDummy()) {
                // Ties / Slurs
                for (Relation rel : sig.getRelations(note, SlurHeadRelation.class)) {
                    processSlur((SlurInter) sig.getOppositeInter(note, rel));
                }

                // Lyrics?
                if (isFirstInChord) {
                    for (Relation rel : sig.getRelations(chord, ChordSyllableRelation.class)) {
                        processSyllable((LyricItemInter) sig.getOppositeInter(chord, rel));
                    }
                }
            }

            // Assemble in Note propOrder
            if (graceX != null) {
                pmNote.add(graceX);
            }
            if (!isFirstInChord) {
                pmNote.add(new X("chord"));
            }
            if (contentX != null) {
                pmNote.add(contentX);
            }
            if (durationX != null) {
                pmNote.add(durationX);
            }
            for (X tie : current.pendingTies) {
                pmNote.add(tie);
            }
            current.pendingTies.clear();
            if (instrumentX != null) {
                pmNote.add(instrumentX);
            }
            if (voiceX != null) {
                pmNote.add(voiceX);
            }
            if (typeX != null) {
                pmNote.add(typeX);
            }
            for (int i = 0; i < dots; i++) {
                pmNote.add(new X("dot"));
            }
            if (accidentalX != null) {
                pmNote.add(accidentalX);
            }
            if (timeModX != null) {
                pmNote.add(timeModX);
            }
            if (stemX != null) {
                pmNote.add(stemX);
            }
            if (motifNotehead != null) {
                pmNote.add(motifNotehead);
            }
            if (staffX != null) {
                pmNote.add(staffX);
            }
            for (X beam : beams) {
                pmNote.add(beam);
            }
            if (current.notations != null) {
                pmNote.add(current.notations);
            }
            for (X lyric : current.pendingLyrics) {
                pmNote.add(lyric);
            }
            current.pendingLyrics.clear();

            current.items.add(pmNote);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", note, current.page, ex);
        }
        current.endNote();
    }

    //------------------//
    // checkOctaveShift //
    //------------------//
    private void checkOctaveShift (AbstractChordInter chord,
                                   HorizontalSide side)
    {
        try {
            if (chord.getId() == 0) {
                return;
            }
            SIGraph sig = current.system.getSig();
            Set<Relation> rels = sig.getRelations(chord, OctaveShiftChordRelation.class);
            for (Relation rel : rels) {
                OctaveShiftChordRelation oscRel = (OctaveShiftChordRelation) rel;
                if (oscRel.getSide() != side) {
                    continue;
                }
                OctaveShiftInter os = (OctaveShiftInter) sig.getOppositeInter(chord, rel);
                X octaveShift = null;
                if (side == RIGHT) {
                    if (os.getExtension(RIGHT) == null) {
                        octaveShift = new X("octave-shift").attr("type", "stop");
                    }
                } else {
                    if (os.getExtension(LEFT) == null) {
                        octaveShift = new X("octave-shift")
                                .attr("type", (os.getKind() == OctaveShiftInter.Kind.ALTA) ? "down" : "up");
                    }
                }
                if (octaveShift != null) {
                    octaveShift.attr("number", "" + getOctaveShiftNumber(os));
                    octaveShift.attr("size", "" + os.getValue());
                    octaveShift.attr("default-y", "" + yOf(
                            side == LEFT ? os.getLine().getP1() : os.getLine().getP2(), os.getStaff()));
                    X directionType = new X("direction-type");
                    directionType.add(octaveShift);
                    X direction = new X("direction")
                            .attr("placement", (os.getKind() == OctaveShiftInter.Kind.ALTA) ? "above" : "below");
                    direction.add(directionType);
                    insertStaffId(direction, os.getStaff());
                    current.items.add(direction);
                }
            }
        } catch (Exception ex) {
            logger.warn("Error checking octave-shift {} side on {}", side, chord, ex);
        }
    }

    private int getOctaveShift (AbstractNoteInter note)
    {
        Staff staff = note.getStaff();
        Point center = note.getChord().getCenter();
        for (OctaveShiftInter os : octaveShiftNumbers.keySet()) {
            if (os.getStaff() == staff) {
                AbstractChordInter first = os.getChord(LEFT);
                if (first == null) {
                    continue;
                }
                AbstractChordInter last = os.getChord(RIGHT);
                if (last == null) {
                    continue;
                }
                if (center.x >= first.getCenter().x && center.x <= last.getCenter().x) {
                    return os.getShift();
                }
            }
        }
        return 0;
    }

    private Integer getOctaveShiftNumber (OctaveShiftInter os)
    {
        Integer num = octaveShiftNumbers.get(os);
        if (num != null) {
            octaveShiftNumbers.remove(os);
            return num;
        }
        for (int i = 1; i <= MAX_LEVEL_NUMBER; i++) {
            if (!octaveShiftNumbers.containsValue(i)) {
                octaveShiftNumbers.put(os, i);
                return i;
            }
        }
        logger.warn("No number for {}", os);
        return null;
    }

    //----------------//
    // getOctaveShift // (number helper above; kept separate for clarity)
    //----------------//

    //-------------//
    // processSlur //
    //-------------//
    private void processSlur (SlurInter slur)
    {
        try {
            boolean isStart = slur.getHead(LEFT) == current.note;
            if (slur.isTie()) {
                X tie = new X("tie").attr("type", isStart ? "start" : "stop");
                // Tie belongs before <voice> in Note propOrder; it is
                // collected here and inserted by processNote — instead we
                // record it on the current note for ordered insertion.
                current.pendingTies.add(tie);
                X tied = new X("tied").attr("type", isStart ? "start" : "stop");
                if (isStart) {
                    tied.attr("orientation", slur.isAbove() ? "over" : "under");
                }
                getNotations().add(tied);
            } else {
                Integer num = getSlurNumber(slur);
                if (isStart) {
                    addSlur(slur, num, LEFT, false);
                    if (slur.getHead(RIGHT) == null) {
                        addSlur(slur, num, RIGHT, true);
                    }
                } else {
                    if (slur.getHead(LEFT) == null) {
                        addSlur(slur, num, LEFT, true);
                    }
                    addSlur(slur, num, RIGHT, false);
                }
            }
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", slur, current.page, ex);
        }
    }

    private void addSlur (SlurInter slur,
                          Integer num,
                          HorizontalSide side,
                          boolean continuation)
    {
        Staff staff = current.note.getStaff();
        CubicCurve2D curve = slur.getCurve();
        X pmSlur = new X("slur");
        if (num != null) {
            pmSlur.attr("number", "" + num);
        }
        pmSlur.attr("type", continuation ? "continue"
                : ((side == LEFT) ? "start" : "stop"));
        if (side == LEFT) {
            pmSlur.attr("placement", slur.isAbove() ? "above" : "below");
        }
        Point2D end = (side == LEFT) ? curve.getP1() : curve.getP2();
        pmSlur.attr("default-x", "" + toTenths(end.getX() - current.note.getCenterLeft().x));
        pmSlur.attr("default-y", "" + yOf(end, staff));
        Point2D ctrl = (side == LEFT) ? curve.getCtrlP1() : curve.getCtrlP2();
        if ((side == LEFT) && continuation) {
            pmSlur.attr("bezier-x2", "" + toTenths(ctrl.getX() - end.getX()));
            pmSlur.attr("bezier-y2", "" + toTenths(end.getY() - ctrl.getY()));
        } else {
            pmSlur.attr("bezier-x", "" + toTenths(ctrl.getX() - end.getX()));
            pmSlur.attr("bezier-y", "" + toTenths(end.getY() - ctrl.getY()));
        }
        getNotations().add(pmSlur);
    }

    private Integer getSlurNumber (SlurInter slur)
    {
        Integer num = slurNumbers.get(slur);
        if (num != null) {
            slurNumbers.remove(slur);
            return num;
        }
        for (int i = 1; i <= MAX_LEVEL_NUMBER; i++) {
            if (!slurNumbers.containsValue(i)) {
                if (slur.getExtension(RIGHT) != null) {
                    slurNumbers.put(slur.getExtension(RIGHT), i);
                } else {
                    slurNumbers.put(slur, i);
                }
                return i;
            }
        }
        logger.warn("No number for {}", slur);
        return null;
    }

    //---------------//
    // processTuplet //
    //---------------//
    private void processTuplet (TupletInter tuplet)
    {
        try {
            X pmTuplet = new X("tuplet");
            if (tuplet.getChords().get(0) == current.note.getChord()) {
                pmTuplet.attr("placement",
                        (tuplet.getCenter().y <= current.note.getCenter().y) ? "above" : "below");
            }
            pmTuplet.attr("type",
                    (tuplet.getChords().get(0) == current.note.getChord()) ? "start" : "stop");
            Integer num = tupletNumbers.get(tuplet);
            if (num != null) {
                pmTuplet.attr("number", "" + num);
                tupletNumbers.remove(tuplet);
            } else {
                for (num = 1; num <= MAX_LEVEL_NUMBER; num++) {
                    if (!tupletNumbers.containsValue(num)) {
                        tupletNumbers.put(tuplet, num);
                        pmTuplet.attr("number", "" + num);
                        break;
                    }
                }
            }
            getNotations().add(pmTuplet);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", tuplet, current.page, ex);
        }
    }

    //-----------------//
    // processSyllable //
    //-----------------//
    private void processSyllable (LyricItemInter syllable)
    {
        if (syllable.getValue() != null) {
            X pmLyric = new X("lyric");
            int defaultY = yOf(syllable.getLocation(), syllable.getStaff());
            pmLyric.attr("default-y", "" + defaultY);
            pmLyric.attr("placement", (defaultY >= 0) ? "above" : "below");
            pmLyric.attr("number", "" + syllable.getLyricLine().getNumber());
            pmLyric.add(new X("syllabic").text(syllable.getSyllabicType().toString().toLowerCase(Locale.US)));
            pmLyric.add(new X("text").text(syllable.getValue()));
            current.pendingLyrics.add(pmLyric);
        }
    }

    //--------------//
    // getNotations //
    //--------------//
    private X getNotations ()
    {
        if (current.notations == null) {
            current.notations = new X("notations");
        }
        return current.notations;
    }

    private X getArticulations ()
    {
        X notations = getNotations();
        X articulations = findChild(notations, "articulations");
        if (articulations == null) {
            articulations = new X("articulations");
            notations.add(articulations);
        }
        return articulations;
    }

    private X getOrnaments ()
    {
        X notations = getNotations();
        X ornaments = findChild(notations, "ornaments");
        if (ornaments == null) {
            ornaments = new X("ornaments");
            notations.add(ornaments);
        }
        return ornaments;
    }

    private X getTechnical ()
    {
        X notations = getNotations();
        X technical = findChild(notations, "technical");
        if (technical == null) {
            technical = new X("technical");
            notations.add(technical);
        }
        return technical;
    }

    //---------------------//
    // processArticulation //
    //---------------------//
    private void processArticulation (ArticulationInter articulation)
    {
        try {
            Shape shape = articulation.getShape();
            Staff staff = current.note.getStaff();
            String placement = (articulation.getCenter().y < current.note.getCenter().y) ? "above" : "below";
            int defaultY = yOf(articulation.getCenter(), staff);
            X element = articulationElement(shape, placement, defaultY);
            if (element != null) {
                getArticulations().add(element);
            }
        } catch (Exception ex) {
            logger.warn("Error visiting " + articulation, ex);
        }
    }

    //----------------//
    // processOrnament //
    //----------------//
    private void processOrnament (OrnamentInter ornament)
    {
        try {
            int defaultY = yOf(ornament.getCenter2D(), ornament.getStaff());
            X element = ornamentElement(ornament, defaultY);
            if (element != null) {
                getOrnaments().add(element);
            }
        } catch (Exception ex) {
            logger.warn("Error visiting " + ornament, ex);
        }
    }

    //--------------//
    // processPause //
    //--------------//
    private void processPause (AbstractPauseInter pause)
    {
        try {
            Point center = pause.getCenter();
            Staff staff = current.note.getStaff();
            String placement = (center.y < current.note.getCenter().y) ? "above" : "below";
            int defaultX = toTenths(center.x - current.measure.getAbscissa(LEFT, staff));
            int defaultY = yOf(center, staff);
            X element = pauseElement(pause.getShape(), placement, defaultX, defaultY);
            if (element != null) {
                getArticulations().add(element);
            }
        } catch (Exception ex) {
            logger.warn("Error visiting " + pause, ex);
        }
    }

    //------------//
    // processBow //
    //------------//
    private void processBow (BowInter bow)
    {
        X placement = new X((bow.getShape() == Shape.BOW_DOWN) ? "down-bow" : "up-bow")
                .attr("placement", "above");
        getTechnical().add(placement);
    }

    //---------------------//
    // processArpeggiato //
    //---------------------//
    private void processArpeggiato (ArpeggiatoInter arpeggiate)
    {
        if (arpeggiate == null) {
            return;
        }
        try {
            X pmArpeggiate = new X("arpeggiate")
                    .attr("relative-x", "" + toTenths(
                            arpeggiate.getCenter().x - current.note.getCenterLeft().x));
            getNotations().add(pmArpeggiate);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", arpeggiate, current.page, ex);
        }
    }

    //----------------//
    // processFermata //
    //----------------//
    /** Build a <fermata> element; if barline=true it is for a barline, else for notations. */
    private X buildFermata (FermataInter fermata,
                            boolean forBarline)
    {
        X pmFermata = new X("fermata");
        Rectangle box = fermata.getBounds();
        Point dot;
        if (fermata.getShape() == Shape.FERMATA_BELOW) {
            dot = new Point(box.x + (box.width / 2), box.y);
        } else {
            dot = new Point(box.x + (box.width / 2), box.y + box.height);
        }
        if (current.note != null) {
            pmFermata.attr("default-y", "" + yOf(dot, current.note.getStaff()));
        }
        pmFermata.attr("type",
                (fermata.getShape() == Shape.FERMATA) ? "upright" : "inverted");
        return pmFermata;
    }

    private void processFermata (FermataInter fermata,
                                 X pmBarline)
    {
        try {
            X pmFermata = buildFermata(fermata, pmBarline != null);
            if (pmBarline != null) {
                pmBarline.add(pmFermata);
            } else {
                getNotations().add(pmFermata);
            }
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", fermata, current.page, ex);
        }
    }

    //------------------//
    // processChordName //
    //------------------//
    private void processChordName (ChordNameInter chordName)
    {
        if (chordName == null) {
            return;
        }
        try {
            Point2D location = chordName.getLocation();
            Staff staff = current.note.getStaff();
            X harmony = new X("harmony")
                    .attr("default-y", "" + yOf(location, staff))
                    .attr("font-size", "" + (chordName.getFontInfo().pointSize * TextFont.TO_POINT))
                    .attr("relative-x", "" + toTenths(location.getX() - current.note.getCenterLeft().x))
                    .attr("placement", (location.getY() < current.note.getCenter().y) ? "above" : "below");
            insertStaffId(harmony, staff);

            X root = new X("root");
            root.add(new X("root-step").text(chordName.getRoot().step.toString()));
            if (chordName.getRoot().alter != 0) {
                root.add(new X("root-alter").text("" + chordName.getRoot().alter));
            }
            harmony.add(root);

            X kind = new X("kind").text(chordName.getKind().type.toString().toLowerCase(Locale.US));
            if (chordName.getKind().text != null) {
                kind.attr("text", chordName.getKind().text);
            }
            if (chordName.getKind().parentheses) {
                kind.attr("parentheses-degrees", "yes");
            }
            if (chordName.getKind().symbol) {
                kind.attr("use-symbols", "yes");
            }
            harmony.add(kind);

            if (chordName.getBass() != null) {
                X bass = new X("bass");
                bass.add(new X("bass-step").text(chordName.getBass().step.toString()));
                if (chordName.getBass().alter != 0) {
                    bass.add(new X("bass-alter").text("" + chordName.getBass().alter));
                }
                harmony.add(bass);
            }

            if (chordName.getDegrees() != null) {
                for (ChordNameInter.ChordDegree deg : chordName.getDegrees()) {
                    X degree = new X("degree");
                    degree.add(new X("degree-value").text("" + deg.value));
                    degree.add(new X("degree-alter").text("" + deg.alter));
                    degree.add(new X("degree-type").text(deg.type.toString().toLowerCase(Locale.US)));
                    harmony.add(degree);
                }
            }
            current.items.add(harmony);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", chordName, current.page, ex);
        }
    }

    //------------------//
    // processDirection //
    //------------------//
    private void processDirection (SentenceInter sentence)
    {
        try {
            String content = sentence.getValue();
            Point2D location = sentence.getLocation();
            Staff staff = current.note.getStaff();
            X direction = new X("direction")
                    .attr("placement", (location.getY() < current.note.getCenter().y) ? "above" : "below");
            X directionType = new X("direction-type");
            direction.add(directionType);
            insertStaffId(direction, staff);

            if (sentence instanceof MetronomeInter metro && metro.isParsed()) {
                String tempoText = metro.getTempoText();
                if (tempoText != null && !tempoText.isBlank()) {
                    X words = new X("words")
                            .attr("default-y", "" + yOf(location, staff))
                            .attr("relative-x", "" + toTenths(location.getX() - current.note.getCenterLeft().x));
                    setFontInfo(words, sentence);
                    words.text(tempoText);
                    directionType.add(words);
                    directionType = new X("direction-type");
                    direction.add(directionType);
                }
                X metronome = new X("metronome");
                if (tempoText == null || tempoText.isBlank()) {
                    metronome.attr("default-y", "" + yOf(location, staff));
                    metronome.attr("relative-x", "" + toTenths(location.getX() - current.note.getCenterLeft().x));
                }
                org.audiveris.omr.sig.inter.BeatUnitInter.Note beatNote = metro.getNote();
                metronome.add(new X("beat-unit").text(beatNote.toMusicXml()));
                if (beatNote.hasDot()) {
                    metronome.add(new X("beat-unit-dot"));
                }
                metronome.add(new X("per-minute").text(metro.getBpmText()));
                if (metro.hasParentheses()) {
                    metronome.attr("parentheses", "yes");
                }
                directionType.add(metronome);
                direction.add(new X("sound").attr("tempo", "" + metro.getQuartersPerMinute()));
            } else {
                X words = new X("words")
                        .attr("default-y", "" + yOf(location, staff))
                        .attr("relative-x", "" + toTenths(location.getX() - current.note.getCenterLeft().x));
                setFontInfo(words, sentence);
                words.text(content);
                directionType.add(words);
            }
            current.items.add(direction);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", sentence, current.page, ex);
        }
    }

    //------------------//
    // processDynamics //
    //------------------//
    private void processDynamics (DynamicsInter dynamics)
    {
        try {
            if (dynamics.getShape() == null) {
                return;
            }
            String dynTag = dynamicsTag(dynamics.getShape());
            if (dynTag == null) {
                return;
            }
            Staff staff = current.note.getStaff();
            Point location = dynamics.getCenterLeft();
            X pmDynamics = new X("dynamics")
                    .attr("default-y", "" + yOf(location, staff))
                    .attr("relative-x", "" + toTenths(location.x - current.note.getCenterLeft().x));
            pmDynamics.add(new X(dynTag));
            X directionType = new X("direction-type");
            directionType.add(pmDynamics);
            X direction = new X("direction")
                    .attr("placement", (location.y < current.note.getCenter().y) ? "above" : "below");
            direction.add(directionType);
            insertStaffId(direction, staff);
            Integer soundLevel = dynamics.getSoundLevel();
            if (soundLevel != null) {
                direction.add(new X("sound").attr("dynamics", "" + soundLevel));
            }
            current.items.add(direction);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", dynamics, current.page, ex);
        }
    }

    //--------------//
    // processPedal //
    //--------------//
    private void processPedal (PedalInter pedal)
    {
        try {
            Staff staff = current.note.getStaff();
            Rectangle bounds = pedal.getBounds();
            Point refPoint = new Point(bounds.x, bounds.y + bounds.height);
            boolean isStart = pedal.getShape() == Shape.PEDAL_MARK;
            X pmPedal = new X("pedal")
                    .attr("type", isStart ? "start" : "stop")
                    .attr("line", "no")
                    .attr("halign", "left")
                    .attr("default-x", "" + toTenths(refPoint.x - current.measure.getAbscissa(LEFT, staff)))
                    .attr("default-y", "" + yOf(refPoint, staff));
            X directionType = new X("direction-type");
            directionType.add(pmPedal);
            X direction = new X("direction")
                    .attr("placement", (refPoint.y < current.note.getCenter().y) ? "above" : "below");
            direction.add(directionType);
            insertStaffId(direction, staff);
            direction.add(new X("sound").attr("damper-pedal", isStart ? "yes" : "no"));
            current.items.add(direction);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", pedal, current.page, ex);
        }
    }

    //------------------//
    // processRehearsal //
    //------------------//
    private void processRehearsal (RehearsalInter rehearsal)
    {
        try {
            Staff staff = rehearsal.getStaff();
            String content = rehearsal.getValue();
            Point2D location = rehearsal.getLocation();
            X fti = new X("rehearsal");
            if (rehearsal.getEnclosure() != null) {
                fti.attr("enclosure", "rectangle");
            }
            fti.attr("default-y", "" + yOf(location, staff));
            fti.attr("relative-x", "" + toTenths(location.getX() - current.measure.getAbscissa(LEFT, staff)));
            setFontInfo(fti, rehearsal);
            fti.attr("font-weight", "bold");
            fti.text(content);
            X directionType = new X("direction-type");
            directionType.add(fti);
            X direction = new X("direction").attr("placement", "above");
            direction.add(directionType);
            current.items.add(direction);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", rehearsal, current.page, ex);
        }
    }

    //---------------//
    // processMarker //
    //---------------//
    private void processMarker (MarkerInter marker)
    {
        if (marker == null) {
            return;
        }
        try {
            String measureId = current.measure.getStack().getScoreId(current.pageMeasureIdOffset);
            X directionType = new X("direction-type");
            X direction = new X("direction");
            direction.add(directionType);
            insertStaffId(direction, current.measure.getPart().getFirstStaff());
            X sound = new X("sound").attr("divisions", "" + current.page.simpleDurationOf(Rational.QUARTER));
            direction.add(sound);
            switch (marker.getShape()) {
                case CODA -> {
                    sound.attr("coda", measureId);
                    directionType.add(new X("coda"));
                }
                case SEGNO -> {
                    sound.attr("segno", measureId);
                    directionType.add(new X("segno"));
                }
                case DA_CAPO -> {
                    directionType.add(new X("words").text("D.C."));
                    sound.attr("dacapo", "yes");
                }
                case DAL_SEGNO -> {
                    directionType.add(new X("words").text("D.S."));
                }
                default -> {
                    logger.warn("Unknown marker shape: {}", marker.getShape());
                    return;
                }
            }
            current.items.add(direction);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", marker, current.page, ex);
        }
    }

    //-----------------//
    // processSentence //
    //-----------------//
    private void processSentence (SentenceInter sentence)
    {
        try {
            TextRole role = sentence.getRole();
            switch (role) {
                case Title -> movementTitle = sentence.getValue();
                case Number -> movementNumber = sentence.getValue();
                case Rights -> idRights.add(new X("rights").text(sentence.getValue()));
                case CreatorArranger, CreatorComposer, CreatorLyricist, Creator -> {
                    X creator = new X("creator").text(sentence.getValue());
                    switch (role) {
                        case CreatorArranger -> creator.attr("type", "arranger");
                        case CreatorComposer -> creator.attr("type", "composer");
                        case CreatorLyricist -> creator.attr("type", "lyricist");
                        default -> {
                        }
                    }
                    idCreators.add(creator);
                }
                case UnknownRole -> {
                }
                default -> {
                    return;
                }
            }
            // Credits
            X credit = new X("credit").attr("page", "" + (1 + score.getPageIndex(current.page)));
            X creditWords = new X("credit-words");
            setFontInfo(creditWords, sentence);
            Point2D pt = sentence.getLocation();
            creditWords.attr("default-x", "" + (toTenths(pt.getX()) + PAGE_MARGIN));
            creditWords.attr("default-y",
                    "" + (toTenths(current.page.getSheet().getHeight() - pt.getY()) + PAGE_MARGIN));
            creditWords.text(sentence.getValue());
            credit.add(creditWords);
            credits.add(credit);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", sentence, current.page, ex);
        }
    }

    //--------------//
    // processWedge //
    //--------------//
    private void processWedge (WedgeInter wedge,
                               HorizontalSide side,
                               AbstractNoteInter referenceNote)
    {
        try {
            Staff staff = referenceNote.getStaff();
            X pmWedge = new X("wedge").attr("spread", "" + toTenths(wedge.getSpread(side)));
            Point2D refPoint;
            X direction = new X("direction");
            if (side == LEFT) {
                Point2D top = wedge.getLine1().getP1();
                Point2D bot = wedge.getLine2().getP1();
                refPoint = new Point2D.Double((top.getX() + bot.getX()) / 2.0,
                        (top.getY() + bot.getY()) / 2.0);
                pmWedge.attr("type",
                        (wedge.getShape() == Shape.CRESCENDO) ? "crescendo" : "diminuendo");
                direction.attr("placement",
                        (refPoint.getY() < referenceNote.getCenter().y) ? "above" : "below");
                pmWedge.attr("default-y", "" + yOf(refPoint, staff));
            } else {
                pmWedge.attr("type", "stop");
                Point2D top = wedge.getLine1().getP2();
                Point2D bot = wedge.getLine2().getP2();
                refPoint = new Point2D.Double((top.getX() + bot.getX()) / 2.0,
                        (top.getY() + bot.getY()) / 2.0);
            }
            pmWedge.attr("default-x",
                    "" + toTenths(refPoint.getX() - referenceNote.getCenterLeft().x));
            X directionType = new X("direction-type");
            directionType.add(pmWedge);
            direction.add(directionType);
            insertStaffId(direction, staff);
            current.items.add(direction);
        } catch (Exception ex) {
            logger.warn("Error visiting {} in {}", wedge, current.page, ex);
        }
    }

    //-------------//
    // setFontInfo //
    //-------------//
    private void setFontInfo (X target,
                              SentenceInter sentence)
    {
        FontInfo fontInfo = sentence.getMeanFont();
        target.attr("font-size", "" + sentence.getExportedFontSize());
        if (fontInfo.isSerif) {
            target.attr("font-family", "serif");
        } else if (fontInfo.isMonospaced) {
            target.attr("font-family", "monospace");
        } else {
            target.attr("font-family", "sans-serif");
        }
        if (fontInfo.isItalic) {
            target.attr("font-style", "italic");
        }
        if (fontInfo.isBold) {
            target.attr("font-weight", "bold");
        }
    }

    //--------------//
    // MeasurePrint //
    //--------------//
    private class MeasurePrint
    {
        private final Measure measure;

        private final X pmPrint;

        private boolean used = false;

        MeasurePrint (Measure measure)
        {
            this.measure = measure;
            pmPrint = new X("print");
            current.items.add(pmPrint);
        }

        private X getPrint ()
        {
            used = true;
            return pmPrint;
        }

        private void populatePrint ()
        {
            if (isFirst.measure && !isFirst.system) {
                getPrint().attr("new-system", "yes");
            }
            if (!isFirst.page && isFirst.system && isFirst.measure) {
                getPrint().attr("new-page", "yes");
            }
            if (isFirst.measure && !measure.isDummy()) {
                X systemLayout = new X("system-layout");
                X systemMargins = new X("system-margins");
                systemMargins.add(new X("left-margin").text("" + toTenths(current.system.getLeft())));
                systemMargins.add(new X("right-margin").text(
                        "" + toTenths(current.page.getSheet().getWidth() - current.system.getLeft()
                                - current.system.getWidth())));
                systemLayout.add(systemMargins);
                if (isFirst.system) {
                    systemLayout.add(new X("top-system-distance")
                            .text("" + toTenths(current.system.getTop())));
                } else {
                    SystemInfo prevSystem = current.system.getPrecedingInPage();
                    systemLayout.add(new X("system-distance").text(
                            "" + toTenths(current.system.getTop() - prevSystem.getBottom())));
                }
                getPrint().add(systemLayout);
            }
            if (isFirst.measure && !measure.isDummy()) {
                SystemInfo system = measure.getStack().getSystem();
                for (Staff staff : measure.getPart().getStaves()) {
                    if (!isFirst.part || (staff.getIndexInPart() > 0)) {
                        try {
                            X staffLayout = new X("staff-layout")
                                    .attr("number", "" + (1 + staff.getIndexInPart()));
                            int staffIndexInSystem = system.getStaves().indexOf(staff);
                            if (staffIndexInSystem > 0) {
                                Staff staffAbove = system.getStaves().get(staffIndexInSystem - 1);
                                staffLayout.add(new X("staff-distance").text(
                                        "" + toTenths(staff.getLeftY(TOP) - staffAbove.getLeftY(BOTTOM))));
                                getPrint().add(staffLayout);
                            }
                        } catch (Exception ex) {
                            logger.warn("Error exporting staff layout system#"
                                    + current.system.getId() + " part#"
                                    + current.logicalPart.getId() + " staff#" + staff.getId()
                                    + " in " + current.page, ex);
                        }
                    }
                }
            }
            if (isFirst.measure) {
                X staffDetails = new X("staff-details")
                        .attr("print-object", measure.isDummy() ? "no" : "yes");
                if (measure.getPart().getStaves().size() == 1) {
                    Staff staff = measure.getPart().getStaves().get(0);
                    if (staff.isOneLineStaff()) {
                        staffDetails.add(new X("staff-lines").text("1"));
                    }
                }
                addStaffDetails(staffDetails);
            }
            if (isFirst.system && isFirst.measure) {
                X numbering = new X("measure-numbering")
                        .text(isFirst.part ? "system" : "none");
                getPrint().add(numbering);
            }
        }

        public void process ()
        {
            populatePrint();
            if (!used) {
                current.items.remove(pmPrint);
            }
        }
    }

    //---------------//
    // ClefIterators //
    //---------------//
    private class ClefIterators
    {
        private final Measure measure;

        private final List<Staff> staves;

        private final Map<Staff, ListIterator<ClefInter>> iters;

        ClefIterators (Measure measure)
        {
            this.measure = measure;
            staves = measure.getPart().getStaves();
            Map<Staff, List<ClefInter>> map = new HashMap<>();
            for (ClefInter clef : measure.getClefs()) {
                Staff staff = clef.getStaff();
                List<ClefInter> list = map.get(staff);
                if (list == null) {
                    map.put(staff, list = new ArrayList<>());
                }
                list.add(clef);
            }
            iters = new LinkedHashMap<>();
            for (Map.Entry<Staff, List<ClefInter>> entry : map.entrySet()) {
                iters.put(entry.getKey(), entry.getValue().listIterator());
            }
        }

        public void push (Integer xOffset,
                          Staff specificStaff)
        {
            if (xOffset != null) {
                MeasureStack stack = measure.getStack();
                for (Staff staff : staves) {
                    List<Staff> theStaff = Collections.singletonList(staff);
                    if ((specificStaff == null) || (staff == specificStaff)) {
                        ListIterator<ClefInter> it = iters.get(staff);
                        if ((it != null) && it.hasNext()) {
                            ClefInter clef = it.next();
                            if (measure.isDummy()
                                    || (stack.getXOffset(clef.getCenter(), theStaff) <= xOffset)) {
                                processClef(clef);
                            } else {
                                it.previous();
                            }
                        }
                    }
                }
            } else {
                for (ListIterator<ClefInter> it : iters.values()) {
                    while (it.hasNext()) {
                        processClef(it.next());
                    }
                }
            }
        }
    }

    //----------------//
    // WedgeIterators //
    //----------------//
    private static class TimedWedge
    {
        final WedgeInter wedge;

        final HorizontalSide side;

        final AbstractNoteInter referenceNote;

        final Rational timeOffset;

        TimedWedge (WedgeInter wedge,
                    HorizontalSide side,
                    AbstractNoteInter referenceNote,
                    Rational timeOffset)
        {
            this.wedge = wedge;
            this.side = side;
            this.referenceNote = referenceNote;
            this.timeOffset = timeOffset;
        }
    }

    private class WedgeIterators
    {
        private final List<TimedWedge> events = new ArrayList<>();

        private ListIterator<TimedWedge> it;

        WedgeIterators (Measure measure)
        {
            SIGraph sig = measure.getStack().getSystem().getSig();
            for (Inter inter : sig.inters(WedgeInter.class)) {
                WedgeInter wedge = (WedgeInter) inter;
                for (HorizontalSide side : HorizontalSide.values()) {
                    AbstractChordInter chord = wedge.getChord(side);
                    if ((chord != null) && (chord.getMeasure() == measure)) {
                        AbstractNoteInter refNote = (AbstractNoteInter) chord.getNotes().get(0);
                        events.add(new TimedWedge(wedge, side, refNote, chord.getTimeOffset()));
                    }
                }
            }
            for (Inter inter : sig.inters(WedgeInter.class)) {
                WedgeInter wedge = (WedgeInter) inter;
            }
            for (Voice voice : measure.getVoices()) {
            }
            Collections.sort(events, (w1, w2) -> {
                // §34: null timeOffset sorts last. Un-timed chords (RHYTHMS
                // "no correct rhythm" stacks leave trailing chords with no
                // timeOffset — identical on desktop and Wasm, DIAG40) must
                // not kill the export: on desktop the NPE is caught and the
                // whole measure is dropped; under TeaVM it is an uncatchable
                // Wasm trap that kills the run. push(null) already flushes
                // remaining events, so nulls-last degrades to "wedge at end
                // of measure" instead of losing the measure.
                if (w1.timeOffset == null) {
                    return (w2.timeOffset == null) ? 0 : 1;
                }
                if (w2.timeOffset == null) {
                    return -1;
                }
                int cmp = w1.timeOffset.compareTo(w2.timeOffset);
                if (cmp != 0) {
                    return cmp;
                }
                if (w1.side == w2.side) {
                    return 0;
                }
                return (w1.side == LEFT) ? -1 : 1;
            });
            it = events.listIterator();
        }

        public void push (Rational timeOffset)
        {
            if (timeOffset != null) {
                while (it.hasNext()) {
                    TimedWedge event = it.next();
                    // §34: a null event timeOffset (un-timed chord) never
                    // fires on a timed push — it waits for the final
                    // push(null) flush. Without this, the first timed push
                    // after the last timed event NPEs on the null event.
                    if ((event.timeOffset == null) || (event.timeOffset.compareTo(timeOffset) > 0)) {
                        it.previous();
                        break;
                    }
                    processWedge(event.wedge, event.side, event.referenceNote);
                }
            } else {
                while (it.hasNext()) {
                    TimedWedge event = it.next();
                    processWedge(event.wedge, event.side, event.referenceNote);
                }
            }
        }
    }

    //---------//
    // Helpers //
    //---------//

    /** Convert a distance in pixels to tenths of interline (integer). */
    private int toTenths (double dist)
    {
        return (int) Math.rint((10.0 * dist) / current.scale.getInterline());
    }

    /** Staff-based Y value of a point, upward from the staff top line, in tenths. */
    private int yOf (Point2D point,
                     Staff staff)
    {
        double staffTopY = staff.getFirstLine().yAt(point.getX());
        return toTenths(staffTopY - point.getY());
    }

    private static String stepOf (HeadInter.NoteStep step)
    {
        return step.toString();
    }

    private static String getNoteTypeName (AbstractNoteInter note)
    {
        return getNoteTypeName(note.getChord().getDurationSansDotOrTuplet());
    }

    private static String getNoteTypeName (Rational duration)
    {
        double dur = 64 * duration.divides(Rational.QUARTER).doubleValue();
        int index = (int) Math.rint(Math.log(dur) / Math.log(2));
        return NOTE_TYPE_NAMES[index];
    }

    private static String accidentalValueOf (Shape shape)
    {
        if (shape == Shape.DOUBLE_FLAT) {
            return "flat-flat";
        }
        return shape.toString().toLowerCase(Locale.US).replace('_', '-');
    }

    private static String barStyleOf (PartBarline.Style style,
                                      String location)
    {
        if (style == PartBarline.Style.LIGHT_HEAVY_LIGHT) {
            return switch (location) {
                case "left" -> "heavy-light";
                case "middle" -> "light-light";
                default -> "light-heavy";
            };
        }
        return style.name().toLowerCase(Locale.US).replace('_', '-');
    }

    private static String dynamicsTag (Shape shape)
    {
        return switch (shape) {
            case DYNAMICS_F -> "f";
            case DYNAMICS_FF -> "ff";
            case DYNAMICS_FFF -> "fff";
            case DYNAMICS_FP -> "fp";
            case DYNAMICS_FZ -> "fz";
            case DYNAMICS_MF -> "mf";
            case DYNAMICS_MP -> "mp";
            case DYNAMICS_P -> "p";
            case DYNAMICS_PP -> "pp";
            case DYNAMICS_PPP -> "ppp";
            case DYNAMICS_SF -> "sf";
            case DYNAMICS_SFZ -> "sfz";
            default -> null;
        };
    }

    private static X articulationElement (Shape shape,
                                          String placement,
                                          int defaultY)
    {
        X element;
        switch (shape) {
            case DOT_set, STACCATO -> element = new X("staccato");
            case ACCENT -> element = new X("accent");
            case MARCATO -> element = new X("strong-accent").attr("type", "up");
            case MARCATO_BELOW -> element = new X("strong-accent").attr("type", "down");
            case TENUTO -> element = new X("tenuto");
            case STACCATISSIMO -> element = new X("staccatissimo");
            case STACCATISSIMO_BELOW -> {
                element = new X("staccatissimo");
                placement = "below";
            }
            case BREATH_MARK -> {
                return new X("breath-mark").attr("placement", placement)
                        .attr("default-y", "" + defaultY).text("comma");
            }
            case CAESURA -> {
                return new X("caesura").attr("placement", placement)
                        .attr("default-y", "" + defaultY);
            }
            default -> {
                logger.error("Unsupported articulation shape:{}", shape);
                return null;
            }
        }
        return element.attr("placement", placement).attr("default-y", "" + defaultY);
    }

    private X ornamentElement (OrnamentInter ornament,
                               int defaultY)
    {
        Shape shape = ornament.getShape();
        X element;
        switch (shape) {
            case MORDENT -> element = new X("inverted-mordent");
            case MORDENT_INVERTED -> element = new X("mordent");
            case TR -> element = new X("trill-mark");
            case TURN -> element = new X("turn");
            case TURN_INVERTED -> element = new X("inverted-turn");
            case TURN_SLASH -> element = new X("inverted-turn").attr("slash", "yes");
            case TURN_UP -> element = new X("vertical-turn");
            case TREMOLO_1, TREMOLO_2, TREMOLO_3 -> {
                element = new X("tremolo").attr("type", "single")
                        .attr("default-y", "" + defaultY)
                        .text("" + TremoloInter.getTremoloValue(shape));
                return element;
            }
            default -> {
                logger.error("Unsupported ornament shape: {}", shape);
                return null;
            }
        }
        String placement = (ornament.getCenter().y < current.note.getCenter().y) ? "above" : "below";
        return element.attr("placement", placement);
    }

    private static X pauseElement (Shape shape,
                                   String placement,
                                   int defaultX,
                                   int defaultY)
    {
        return switch (shape) {
            case BREATH_MARK -> new X("breath-mark").attr("placement", placement)
                    .attr("default-x", "" + defaultX).attr("default-y", "" + defaultY).text("comma");
            case CAESURA -> new X("caesura").attr("placement", placement)
                    .attr("default-x", "" + defaultX).attr("default-y", "" + defaultY);
            default -> {
                logger.error("Unsupported pause shape:{}", shape);
                yield null;
            }
        };
    }

    private static X findChild (X parent,
                                String tag)
    {
        for (X kid : parent.kids) {
            if (kid.tag.equals(tag)) {
                return kid;
            }
        }
        return null;
    }

    private static String textOf (X parent,
                                  String tag)
    {
        X kid = findChild(parent, tag);
        return (kid == null) ? null : kid.text;
    }

    //-----------------------//
    // Attributes management //
    //-----------------------//

    private static final Object ATTR_MARKER = new Object();

    private void setDivisions (int divisions)
    {
        current.attrs.touch();
        current.attrs.divisions = divisions;
    }

    private void setStaves (int staves)
    {
        current.attrs.touch();
        current.attrs.staves = staves;
    }

    private void addKey (X key)
    {
        current.attrs.touch();
        current.attrs.keys.add(key);
    }

    private void addTime (X time)
    {
        current.attrs.touch();
        current.attrs.times.add(time);
    }

    private void addClef (X clef)
    {
        current.attrs.touch();
        current.attrs.clefs.add(clef);
    }

    private void addStaffDetails (X staffDetails)
    {
        current.attrs.touch();
        current.attrs.staffDetails.add(staffDetails);
    }

    private void addMeasureStyle (X measureStyle)
    {
        current.attrs.touch();
        current.attrs.measureStyles.add(measureStyle);
    }

    /** Render the current measure shell: items + attributes (at the marker). */
    private void renderMeasure ()
    {
        if (current.items == null || current.pmMeasure == null) {
            return;
        }
        for (Object o : current.items) {
            if (o == ATTR_MARKER) {
                X attrs = buildAttributes();
                if (attrs != null) {
                    current.pmMeasure.add(attrs);
                }
            } else {
                current.pmMeasure.add((X) o);
            }
        }
        current.items = null;
        current.attrs = null;
    }

    /** Build the <attributes> element from the collected slots, in propOrder. */
    private X buildAttributes ()
    {
        Attrs a = current.attrs;
        if (a == null) {
            return null;
        }
        if (a.divisions == null && a.keys.isEmpty() && a.times.isEmpty() && a.staves == null
                && a.clefs.isEmpty() && a.staffDetails.isEmpty() && a.measureStyles.isEmpty()) {
            return null;
        }
        X attrs = new X("attributes");
        if (a.divisions != null) {
            attrs.add(new X("divisions").text("" + a.divisions));
        }
        for (X key : a.keys) {
            attrs.add(key);
        }
        for (X time : a.times) {
            attrs.add(time);
        }
        if (a.staves != null) {
            attrs.add(new X("staves").text("" + a.staves));
        }
        for (X clef : a.clefs) {
            attrs.add(clef);
        }
        for (X sd : a.staffDetails) {
            attrs.add(sd);
        }
        for (X ms : a.measureStyles) {
            attrs.add(ms);
        }
        return attrs;
    }

    //~ Inner Classes ------------------------------------------------------------------------------

    /** The <attributes> slots; touch() records the element's position in the measure. */
    private class Attrs
    {
        Integer divisions;

        Integer staves;

        final List<X> keys = new ArrayList<>();

        final List<X> times = new ArrayList<>();

        final List<X> clefs = new ArrayList<>();

        final List<X> staffDetails = new ArrayList<>();

        final List<X> measureStyles = new ArrayList<>();

        boolean placed;

        void touch ()
        {
            if (!placed && current.items != null) {
                placed = true;
                current.items.add(ATTR_MARKER);
            }
        }
    }

    /** Current context (mirrors PartwiseBuilder.Current). */
    private static class Current
    {
        LogicalPart logicalPart;

        Boolean isDrumPart;

        X pmPart;

        Map<LogicalPart, X> partByLogical = new HashMap<>();

        List<X> miscSheetFields = new ArrayList<>();

        Page page;

        int pageMeasureIdOffset;

        Scale scale;

        SystemInfo system;

        List<Inter> multipleRests;

        Measure measure;

        boolean repeatStarted;

        boolean repeatCopying;

        X pmMeasure;

        List<Object> items;

        Attrs attrs;

        final TreeMap<Integer, Integer> keys = new TreeMap<>();

        Voice voice;

        AbstractNoteInter note;

        X pmNote;

        X notations;

        List<X> pendingTies = new ArrayList<>();

        List<X> pendingLyrics = new ArrayList<>();

        void endMeasure ()
        {
            measure = null;
            voice = null;
            endVoice();
        }

        void endNote ()
        {
            note = null;
            pmNote = null;
            notations = null;
        }

        void endVoice ()
        {
            voice = null;
            endNote();
        }
    }

    /** Composite first-flags (mirrors PartwiseBuilder.IsFirst). */
    private static class IsFirst
    {
        boolean part;

        boolean page;

        boolean system;

        boolean measure;
    }

    /** An emitted clef, for isNewClef comparison. */
    private static class ClefKey
    {
        final String number;

        final String sign;

        final String line;

        final String octaveChange;

        ClefKey (String number,
                 String sign,
                 String line,
                 String octaveChange)
        {
            this.number = number;
            this.sign = sign;
            this.line = line;
            this.octaveChange = octaveChange;
        }
    }

    /** Minimal XML element: tag, attributes (insertion order), children, optional text. */
    private static class X
    {
        final String tag;

        final LinkedHashMap<String, String> attrs = new LinkedHashMap<>();

        final List<X> kids = new ArrayList<>();

        String text;

        X (String tag)
        {
            this.tag = tag;
        }

        X attr (String name,
                String value)
        {
            if (value != null) {
                attrs.put(name, value);
            }
            return this;
        }

        X add (X kid)
        {
            kids.add(kid);
            return this;
        }

        X text (String text)
        {
            this.text = text;
            return this;
        }

        void render (StringBuilder sb,
                     int ind)
        {
            String pad = indent(ind);
            sb.append(pad).append('<').append(tag);
            for (Map.Entry<String, String> e : attrs.entrySet()) {
                sb.append(' ').append(e.getKey()).append("=\"").append(esc(e.getValue())).append('"');
            }
            if (kids.isEmpty() && text == null) {
                sb.append(" />\n");
                return;
            }
            sb.append('>');
            if (kids.isEmpty()) {
                sb.append(esc(text)).append("</").append(tag).append(">\n");
                return;
            }
            sb.append('\n');
            for (X kid : kids) {
                kid.render(sb, ind + 1);
            }
            sb.append(pad).append("</").append(tag).append(">\n");
        }

        private static String indent (int n)
        {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < n; i++) {
                sb.append("  ");
            }
            return sb.toString();
        }

        private static String esc (String s)
        {
            if (s == null) {
                return "";
            }
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < s.length(); i++) {
                char c = s.charAt(i);
                switch (c) {
                    case '&' -> sb.append("&amp;");
                    case '<' -> sb.append("&lt;");
                    case '>' -> sb.append("&gt;");
                    case '"' -> sb.append("&quot;");
                    default -> sb.append(c);
                }
            }
            return sb.toString();
        }
    }
}
