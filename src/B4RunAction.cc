//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders of  *
// * the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4RunAction.cc
/// \brief Implementation of the B4RunAction class
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// This file defines the analysis output for the simulation:
///   - ROOT histograms and ntuple
///   - CSV reset at the beginning of the run
///
/// Event-level filling is performed in B4aEventAction.cc.

#include "B4RunAction.hh"
#include "B4Analysis.hh"

#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4UnitsTable.hh"
#include "G4SystemOfUnits.hh"

#include <fstream>

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4RunAction::B4RunAction()
 : G4UserRunAction()
{
  // Print progress every 1000 events.
  // This can also be overwritten from macro using:
  // /run/printProgress 1000
  G4RunManager::GetRunManager()->SetPrintProgress(1000);

  // --------------------------------------------------------------------------
  // Create analysis manager
  // --------------------------------------------------------------------------

  auto analysisManager = G4AnalysisManager::Instance();

  G4cout << "Using " << analysisManager->GetType()
         << " analysis manager for NaI(Tl) 59.5 keV simulation."
         << G4endl;

  analysisManager->SetVerboseLevel(1);
  analysisManager->SetNtupleMerging(true);

  // --------------------------------------------------------------------------
  // Histograms
  // --------------------------------------------------------------------------
  //
  // IMPORTANT:
  // In B4aEventAction.cc, we fill histograms using:
  //
  //   fEnergyCrystal / keV
  //   fTrackLCrystal / mm
  //
  // Therefore the histogram axes below are plain numerical values in:
  //
  //   Edep  -> keV
  //   Track -> mm
  //
  // For 59.5 keV gamma rays, 0--80 keV is sufficient to include the
  // full-energy peak and partial-deposition events.
  // --------------------------------------------------------------------------

  analysisManager->CreateH1(
    "Edep_NaI",
    "Deposited energy in NaI(Tl);E_{dep} [keV];Counts",
    200,
    0.0,
    80.0
  );

  analysisManager->CreateH1(
    "TrackL_NaI",
    "Charged-particle track length in NaI(Tl);Track length [mm];Counts",
    200,
    0.0,
    100.0
  );

  // --------------------------------------------------------------------------
  // Ntuple
  // --------------------------------------------------------------------------
  //
  // Ntuple columns:
  //   0 -> Edep_NaI_keV
  //   1 -> TrackL_NaI_mm
  // --------------------------------------------------------------------------

  analysisManager->CreateNtuple(
    "NaI59",
    "Event-level energy deposition in NaI(Tl)"
  );

  analysisManager->CreateNtupleDColumn("Edep_NaI_keV");
  analysisManager->CreateNtupleDColumn("TrackL_NaI_mm");

  analysisManager->FinishNtuple();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4RunAction::~B4RunAction()
{
  delete G4AnalysisManager::Instance();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void B4RunAction::BeginOfRunAction(const G4Run* /*run*/)
{
  // --------------------------------------------------------------------------
  // Open ROOT output file
  // --------------------------------------------------------------------------

  auto analysisManager = G4AnalysisManager::Instance();

  G4String fileName = "nai59";
  analysisManager->OpenFile(fileName);

  G4cout
    << G4endl
    << "------------------------------------------------------------" << G4endl
    << " Starting NaI(Tl) 59.5 keV gamma energy-deposition run" << G4endl
    << " ROOT output file : nai59.root" << G4endl
    << " CSV output file  : nai59_edep_events.csv" << G4endl
    << "------------------------------------------------------------" << G4endl
    << G4endl;

  // --------------------------------------------------------------------------
  // Reset CSV file at the beginning of each run
  // --------------------------------------------------------------------------
  //
  // B4aEventAction.cc appends one line per event.
  // To avoid mixing old and new runs, we clear the CSV file here.
  // The header line is written by B4aEventAction.cc at eventID == 0.
  // --------------------------------------------------------------------------

  std::ofstream csvFile("nai59_edep_events.csv", std::ios::trunc);
  csvFile.close();

  // Optional:
  // G4RunManager::GetRunManager()->SetRandomNumberStore(true);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void B4RunAction::EndOfRunAction(const G4Run* /*run*/)
{
  auto analysisManager = G4AnalysisManager::Instance();

  // --------------------------------------------------------------------------
  // Print histogram statistics
  // --------------------------------------------------------------------------

  if (analysisManager->GetH1(0)) {
    G4cout << G4endl
           << " ----> NaI(Tl) 59.5 keV run statistics ";

    if (isMaster) {
      G4cout << "for the entire run" << G4endl << G4endl;
    }
    else {
      G4cout << "for the local thread" << G4endl << G4endl;
    }

    G4cout
      << " Edep_NaI : mean = "
      << analysisManager->GetH1(0)->mean()
      << " keV"
      << "   rms = "
      << analysisManager->GetH1(0)->rms()
      << " keV"
      << G4endl;

    G4cout
      << " TrackL_NaI : mean = "
      << analysisManager->GetH1(1)->mean()
      << " mm"
      << "   rms = "
      << analysisManager->GetH1(1)->rms()
      << " mm"
      << G4endl;
  }

  // --------------------------------------------------------------------------
  // Save histograms and ntuple
  // --------------------------------------------------------------------------

  analysisManager->Write();
  analysisManager->CloseFile();

  G4cout
    << G4endl
    << "------------------------------------------------------------" << G4endl
    << " NaI(Tl) run completed." << G4endl
    << " Saved ROOT output : nai59.root" << G4endl
    << " Saved CSV output  : nai59_edep_events.csv" << G4endl
    << "------------------------------------------------------------" << G4endl
    << G4endl;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
