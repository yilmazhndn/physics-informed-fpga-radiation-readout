//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders of  *
// * the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4aEventAction.cc
/// \brief Implementation of the B4aEventAction class
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// For each primary event, the total energy deposited in the NaI(Tl)
/// scintillator crystal is accumulated and exported as a truth-level input
/// for the synthetic waveform generation stage.

#include "B4aEventAction.hh"
#include "B4Analysis.hh"

#include "G4RunManager.hh"
#include "G4Event.hh"
#include "G4UnitsTable.hh"
#include "G4SystemOfUnits.hh"

#include <iomanip>
#include <fstream>

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4aEventAction::B4aEventAction()
 : G4UserEventAction(),
   fEnergyCrystal(0.),
   fTrackLCrystal(0.)
{
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4aEventAction::~B4aEventAction()
{
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void B4aEventAction::BeginOfEventAction(const G4Event* /*event*/)
{
  // Reset event-level accumulators
  fEnergyCrystal = 0.;
  fTrackLCrystal = 0.;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void B4aEventAction::EndOfEventAction(const G4Event* event)
{
  // Get analysis manager
  auto analysisManager = G4AnalysisManager::Instance();

  // --------------------------------------------------------------------------
  // Fill Geant4 analysis objects
  // --------------------------------------------------------------------------
  //
  // Histogram and ntuple IDs must match the definitions in B4RunAction.cc.
  // We will define:
  //   H1(0): deposited energy in NaI(Tl)
  //   H1(1): charged-particle track length in NaI(Tl)
  //   Ntuple columns:
  //       0: Edep_NaI_keV
  //       1: TrackL_NaI_mm
  //
  // Internally, fEnergyCrystal and fTrackLCrystal are stored in Geant4 units.
  // We convert them to keV and mm for direct analysis convenience.
  // --------------------------------------------------------------------------

  analysisManager->FillH1(0, fEnergyCrystal / keV);
  analysisManager->FillH1(1, fTrackLCrystal / mm);

  analysisManager->FillNtupleDColumn(0, fEnergyCrystal / keV);
  analysisManager->FillNtupleDColumn(1, fTrackLCrystal / mm);
  analysisManager->AddNtupleRow();

  // Get event ID
  auto eventID = event->GetEventID();

  // --------------------------------------------------------------------------
  // CSV export for waveform-generation pipeline
  // --------------------------------------------------------------------------
  //
  // Units:
  //   deposited energy -> keV
  //   track length     -> mm
  //
  // Output file:
  //   nai59_edep_events.csv
  //
  // This file will later be used as the truth-level input to generate
  // scintillation pulses, electronics response, ADC waveforms, and HDL vectors.
  // --------------------------------------------------------------------------

  std::ofstream csvFile("nai59_edep_events.csv", std::ios::app);

  if (eventID == 0) {
    csvFile << "event_id,edep_nai_keV,track_nai_mm\n";
  }

  csvFile
    << eventID << ","
    << fEnergyCrystal / keV << ","
    << fTrackLCrystal / mm << "\n";

  csvFile.close();

  // --------------------------------------------------------------------------
  // Print progress
  // --------------------------------------------------------------------------

  auto printModulo = G4RunManager::GetRunManager()->GetPrintProgress();

  if ((printModulo > 0) && (eventID % printModulo == 0)) {
    G4cout << "---> End of event: " << eventID << G4endl;

    G4cout
      << "   NaI(Tl): total deposited energy = " << std::setw(7)
      << G4BestUnit(fEnergyCrystal, "Energy")
      << "      charged-particle track length = " << std::setw(7)
      << G4BestUnit(fTrackLCrystal, "Length")
      << G4endl;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
