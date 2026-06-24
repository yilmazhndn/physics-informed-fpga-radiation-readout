//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .        *
// ********************************************************************
//
//
/// \file exampleB4a.cc
/// \brief Main program of the B4a example
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// Physics configuration:
///   FTFP_BERT reference physics list
///   + G4EmLivermorePhysics for low-energy electromagnetic interactions

#include "B4DetectorConstruction.hh"
#include "B4aActionInitialization.hh"

#include "G4RunManagerFactory.hh"

#include "G4UImanager.hh"
#include "G4UIcommand.hh"

#include "FTFP_BERT.hh"
#include "G4EmLivermorePhysics.hh"

#include "Randomize.hh"

#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

namespace {
  void PrintUsage() {
    G4cerr << " Usage: " << G4endl;
    G4cerr << " exampleB4a [-m macro ] [-u UIsession] [-t nThreads]" << G4endl;
    G4cerr << "   note: -t option is available only for multi-threaded mode."
           << G4endl;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

int main(int argc,char** argv)
{
  // Evaluate arguments
  if ( argc > 7 ) {
    PrintUsage();
    return 1;
  }

  G4String macro;
  G4String session;

#ifdef G4MULTITHREADED
  G4int nThreads = 0;
#endif

  for ( G4int i = 1; i < argc; i = i + 2 ) {
    if      ( G4String(argv[i]) == "-m" ) macro = argv[i+1];
    else if ( G4String(argv[i]) == "-u" ) session = argv[i+1];

#ifdef G4MULTITHREADED
    else if ( G4String(argv[i]) == "-t" ) {
      nThreads = G4UIcommand::ConvertToInt(argv[i+1]);
    }
#endif

    else {
      PrintUsage();
      return 1;
    }
  }

  // Detect interactive mode if no macro is provided
  G4UIExecutive* ui = nullptr;

  if ( ! macro.size() ) {
    ui = new G4UIExecutive(argc, argv, session);
  }

  // Optional: choose a different random engine
  // G4Random::setTheEngine(new CLHEP::MTwistEngine);

  // Construct the default run manager
  auto* runManager =
    G4RunManagerFactory::CreateRunManager(G4RunManagerType::Default);

#ifdef G4MULTITHREADED
  if ( nThreads > 0 ) {
    runManager->SetNumberOfThreads(nThreads);
  }
#endif

  // --------------------------------------------------------------------------
  // Mandatory initialization classes
  // --------------------------------------------------------------------------

  auto detConstruction = new B4DetectorConstruction();
  runManager->SetUserInitialization(detConstruction);

  // --------------------------------------------------------------------------
  // Physics list
  // --------------------------------------------------------------------------
  //
  // FTFP_BERT is kept as the reference modular physics list.
  // Its default electromagnetic component is replaced by Livermore EM models,
  // which are more appropriate for low-energy photon/electron interactions
  // in the tens-of-keV range relevant to the 59.5 keV gamma simulation.
  // --------------------------------------------------------------------------

  auto physicsList = new FTFP_BERT;
  physicsList->ReplacePhysics(new G4EmLivermorePhysics());

  runManager->SetUserInitialization(physicsList);

  auto actionInitialization = new B4aActionInitialization(detConstruction);
  runManager->SetUserInitialization(actionInitialization);

  // Initialize visualization
  auto visManager = new G4VisExecutive;
  visManager->Initialize();

  // Get the pointer to the User Interface manager
  auto UImanager = G4UImanager::GetUIpointer();

  // Process macro or start UI session
  if ( macro.size() ) {
    // batch mode
    G4String command = "/control/execute ";
    UImanager->ApplyCommand(command + macro);
  }
  else {
    // interactive mode
    UImanager->ApplyCommand("/control/execute init_vis.mac");

    if (ui->IsGUI()) {
      UImanager->ApplyCommand("/control/execute gui.mac");
    }

    ui->SessionStart();
    delete ui;
  }

  // Job termination
  delete visManager;
  delete runManager;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo.....
