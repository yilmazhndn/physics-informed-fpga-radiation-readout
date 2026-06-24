//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// *  The Geant4 software is copyright of the Copyright Holders of    *
// *  the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4DetectorConstruction.hh
/// \brief Definition of the B4DetectorConstruction class
///
/// Modified geometry for NaI(Tl) 59.5 keV gamma energy-deposition study.
/// Original B4a sampling calorimeter geometry is replaced by a single
/// cylindrical NaI(Tl) scintillator crystal.

#ifndef B4DetectorConstruction_h
#define B4DetectorConstruction_h 1

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

class G4VPhysicalVolume;
class G4GlobalMagFieldMessenger;

/// Detector construction class.
///
/// Geometry used in this study:
///
///   World volume
///      └── NaI(Tl) cylindrical scintillator crystal
///
/// The NaI(Tl) detector is represented using the NIST sodium iodide material
/// definition. Thallium doping is neglected at this stage because it is present
/// only at trace concentration and does not significantly affect gamma
/// interaction probabilities for the present energy-deposition simulation.

class B4DetectorConstruction : public G4VUserDetectorConstruction
{
  public:
    B4DetectorConstruction();
    virtual ~B4DetectorConstruction();

  public:
    virtual G4VPhysicalVolume* Construct();
    virtual void ConstructSDandField();

    // Get method for scoring volume
    const G4VPhysicalVolume* GetCrystalPV() const;

  private:
    // Methods
    void DefineMaterials();
    G4VPhysicalVolume* DefineVolumes();

    // Data members
    static G4ThreadLocal G4GlobalMagFieldMessenger* fMagFieldMessenger;

    G4VPhysicalVolume* fCrystalPV;   // NaI(Tl) crystal physical volume

    G4bool fCheckOverlaps;           // option to activate overlap checking
};

// Inline function

inline const G4VPhysicalVolume* B4DetectorConstruction::GetCrystalPV() const
{
  return fCrystalPV;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
