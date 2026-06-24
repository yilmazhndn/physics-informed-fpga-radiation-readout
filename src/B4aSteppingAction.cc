//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4aSteppingAction.cc
/// \brief Implementation of the B4aSteppingAction class
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// The original B4a example collected energy deposition separately in
/// absorber and gap volumes. In this version, the only scoring volume is
/// the NaI(Tl) crystal.

#include "B4aSteppingAction.hh"

#include "B4aEventAction.hh"
#include "B4DetectorConstruction.hh"

#include "G4Step.hh"
#include "G4Track.hh"
#include "G4VPhysicalVolume.hh"
#include "G4ParticleDefinition.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4aSteppingAction::B4aSteppingAction(
                      const B4DetectorConstruction* detectorConstruction,
                      B4aEventAction* eventAction)
  : G4UserSteppingAction(),
    fDetConstruction(detectorConstruction),
    fEventAction(eventAction)
{
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4aSteppingAction::~B4aSteppingAction()
{
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void B4aSteppingAction::UserSteppingAction(const G4Step* step)
{
  // --------------------------------------------------------------------------
  // Collect energy deposition inside the NaI(Tl) crystal step by step.
  // --------------------------------------------------------------------------

  // Get physical volume of the current step.
  auto volume = step->GetPreStepPoint()->GetTouchableHandle()->GetVolume();

  // Only score quantities inside the NaI(Tl) crystal.
  if (volume != fDetConstruction->GetCrystalPV()) {
    return;
  }

  // Total energy deposited in this step.
  auto edep = step->GetTotalEnergyDeposit();

  // Track length is accumulated only for charged secondary particles.
  // Primary gamma has zero charge and therefore does not contribute to
  // charged-particle path length.
  G4double stepLength = 0.0;

  if (step->GetTrack()->GetDefinition()->GetPDGCharge() != 0.0) {
    stepLength = step->GetStepLength();
  }

  // Add the step quantities to the event-level accumulator.
  fEventAction->AddCrystal(edep, stepLength);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
