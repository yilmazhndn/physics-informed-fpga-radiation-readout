//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4aEventAction.hh
/// \brief Definition of the B4aEventAction class
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// This event action stores event-level quantities collected inside the
/// NaI(Tl) scintillator crystal:
///   - total deposited energy in the crystal
///   - charged-particle track length in the crystal
///
/// These quantities are filled into Geant4 analysis histograms/ntuples and
/// also exported to a CSV file for subsequent waveform generation.

#ifndef B4aEventAction_h
#define B4aEventAction_h 1

#include "G4UserEventAction.hh"
#include "globals.hh"

class G4Event;

/// Event action class for the NaI(Tl) 59.5 keV gamma simulation.

class B4aEventAction : public G4UserEventAction
{
  public:
    B4aEventAction();
    virtual ~B4aEventAction();

    virtual void BeginOfEventAction(const G4Event* event);
    virtual void EndOfEventAction(const G4Event* event);

    // Add energy deposition and charged-particle track length in NaI(Tl)
    void AddCrystal(G4double de, G4double dl);

  private:
    G4double fEnergyCrystal;   // total deposited energy in NaI(Tl)
    G4double fTrackLCrystal;   // charged-particle track length in NaI(Tl)
};

// Inline function

inline void B4aEventAction::AddCrystal(G4double de, G4double dl)
{
  fEnergyCrystal += de;
  fTrackLCrystal += dl;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
