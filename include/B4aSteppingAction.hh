//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4aSteppingAction.hh
/// \brief Definition of the B4aSteppingAction class
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// This stepping action collects the energy deposited inside the NaI(Tl)
/// scintillator crystal and passes the accumulated event-level quantities
/// to B4aEventAction.

#ifndef B4aSteppingAction_h
#define B4aSteppingAction_h 1

#include "G4UserSteppingAction.hh"

class B4DetectorConstruction;
class B4aEventAction;
class G4Step;

/// Stepping action class.
///
/// In UserSteppingAction(), the deposited energy and charged-particle
/// track length inside the NaI(Tl) crystal are collected step by step.
/// The quantities are accumulated at event level through B4aEventAction.

class B4aSteppingAction : public G4UserSteppingAction
{
  public:
    B4aSteppingAction(const B4DetectorConstruction* detectorConstruction,
                      B4aEventAction* eventAction);

    virtual ~B4aSteppingAction();

    virtual void UserSteppingAction(const G4Step* step);

  private:
    const B4DetectorConstruction* fDetConstruction;
    B4aEventAction* fEventAction;
};

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
