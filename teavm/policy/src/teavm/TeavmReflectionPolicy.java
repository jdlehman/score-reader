package teavm;

import org.teavm.extension.spi.reflection.SimpleReflectionPolicy;

/**
 * Compile-time-only TeaVM reflection policy for the Audiveris headless entry point.
 *
 * TeaVM generates field-reflection metadata ONLY for members a ReflectionPolicy declares
 * accessible; with no policy, Class.getDeclaredFields() returns an empty array for every
 * class. Audiveris's ConstantSet.initMap() enumerates its Constant fields via
 * getDeclaredFields(), so with no policy it builds an empty map, the constants never get
 * qualified names, and Constant.checkInitialized() busy-spins forever calling
 * checkDirtySets() on an empty dirty set (the OmrExecutors static-init stall, 2026-11-09).
 *
 * Scope is deliberately narrow: fields of ConstantSet subclasses (the initMap path),
 * WellKnowns (logDeclaredData), and ShapeSet (shape enumeration). This is a build-time
 * tool class, discovered by TeaVM's DefaultReflectionSupplier via ServiceLoader on the
 * program classpath; it is NOT reachable from main and is NOT compiled into the wasm.
 *
 * §12 (2026-11-09): FilamentFactory looks up filamentClass.getConstructor(int.class)
 * reflectively; with no policy the constructor metadata is absent, getConstructor
 * throws NoSuchMethodException, the factory keeps a null constructor, and
 * createFilament traps on it (GRID step, first seen in full-out16). Constructors
 * are IntrospectMethods named "<init>" (IntrospectClassImpl.declaredMethods()
 * includes them), so reflectableMethods(named("<init>")) covers them.
 * StaffFilament is the first factory built (LinesRetriever, GRID);
 * StraightFilament follows in LeggedIntersBuilder (CURVES). CurvedFilament is
 * NOT a FilamentFactory target (its ctor takes two ints), so it is not listed.
 */
public class TeavmReflectionPolicy extends SimpleReflectionPolicy
{
    @Override
    protected void setup ()
    {
        selectClasses(extending("org.audiveris.omr.constant.ConstantSet"))
                .reflectableFields(f -> true);
        selectClass("org.audiveris.omr.WellKnowns").reflectableFields(f -> true);
        selectClass("org.audiveris.omr.glyph.ShapeSet").reflectableFields(f -> true);
        // §12: FilamentFactory.getConstructor(int.class) needs the (int)
        // constructors of the filament classes as reflection metadata.
        selectClass("org.audiveris.omr.sheet.grid.StaffFilament")
                .reflectableMethods(named("<init>"));
        selectClass("org.audiveris.omr.glyph.dynamic.StraightFilament")
                .reflectableMethods(named("<init>"));
        // §42: SIGraph.insertSupport does
        // supportClass.getDeclaredConstructor().newInstance(); with no
        // policy the constructor metadata is absent, getDeclaredConstructor
        // throws NoSuchMethodException, the support is silently missing
        // (DIAG48: all 149 failures on Hallelujah p01 are
        // HeadHeadRelation). Both Support subclasses instantiated through
        // insertSupport are listed: HeadHeadRelation (proven failing —
        // SigReducer.java:326, ChordsBuilder.java:484) and BeamBeamRelation
        // (BeamGroupInter.java:158 — same path, never observed failing,
        // same defect class). Constructors are IntrospectMethods named
        // "<init>", as in §12.
        selectClass("org.audiveris.omr.sig.relation.HeadHeadRelation")
                .reflectableMethods(named("<init>"));
        selectClass("org.audiveris.omr.sig.relation.BeamBeamRelation")
                .reflectableMethods(named("<init>"));
    }
}
