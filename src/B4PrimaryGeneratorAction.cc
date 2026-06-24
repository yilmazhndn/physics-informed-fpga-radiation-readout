//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders of  *
// * the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4PrimaryGeneratorAction.cc
/// \brief Implementation of the B4PrimaryGeneratorAction class
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// The source is a monoenergetic 59.5 keV gamma beam emitted toward the
/// cylindrical NaI(Tl) crystal along the +z axis.

#include "B4PrimaryGeneratorAction.hh"

#include "G4Event.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "Randomize.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4PrimaryGeneratorAction::B4PrimaryGeneratorAction()
 : G4VUserPrimaryGeneratorAction(),
   fParticleGun(nullptr)
{
  // --------------------------------------------------------------------------
  // One primary particle per event
  // --------------------------------------------------------------------------

  G4int nofParticles = 1;
  fParticleGun = new G4ParticleGun(nofParticles);

  // --------------------------------------------------------------------------
  // Default particle definition: 59.5 keV gamma
  // --------------------------------------------------------------------------
  //
  // This corresponds to the standard low-energy gamma line commonly associated
  // with Am-241 and is used here as the monoenergetic input for the NaI(Tl)
  // detector response simulation.
  // --------------------------------------------------------------------------

  auto particleDefinition =
    G4ParticleTable::GetParticleTable()->FindParticle("gamma");

  fParticleGun->SetParticleDefinition(particleDefinition);
  fParticleGun->SetParticleEnergy(59.5*keV);

  // Beam directed along +z, toward the detector placed at the origin.
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0., 0., 1.));

  // Source position: 5 cm in front of the NaI(Tl) crystal along -z.
  //
  // Crystal center is at z = 0.
  // Crystal length is 50.8 mm, so its front face is at z = -25.4 mm.
  // Source at z = -50 mm gives an air gap of approximately 24.6 mm
  // between source and crystal front face.
  fParticleGun->SetParticlePosition(G4ThreeVector(0., 0., -5.0*cm));
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4PrimaryGeneratorAction::~B4PrimaryGeneratorAction()
{
  delete fParticleGun;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void B4PrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent)
{
  // Generate one primary 59.5 keV gamma vertex.
  //
  // Particle properties are initialized in the constructor and may be modified
  // externally using /gun macro commands before /run/beamOn.

  fParticleGun->GeneratePrimaryVertex(anEvent);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
