//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4RunAction.hh
/// \brief Definition of the B4RunAction class
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// This run action defines analysis objects for:
///   - deposited energy in the NaI(Tl) crystal
///   - charged-particle track length in the NaI(Tl) crystal
///
/// The ROOT output file is written as:
///   nai59.root
///
/// The event-level CSV file is reset at the beginning of each run:
///   nai59_edep_events.csv

#ifndef B4RunAction_h
#define B4RunAction_h 1

#include "G4UserRunAction.hh"
#include "globals.hh"

class G4Run;

/// Run action class for the NaI(Tl) 59.5 keV gamma simulation.

class B4RunAction : public G4UserRunAction
{
  public:
    B4RunAction();
    virtual ~B4RunAction();

    virtual void BeginOfRunAction(const G4Run*);
    virtual void EndOfRunAction(const G4Run*);
};

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
