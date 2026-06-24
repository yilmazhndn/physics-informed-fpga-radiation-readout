//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4PrimaryGeneratorAction.hh
/// \brief Definition of the B4PrimaryGeneratorAction class
///
/// Modified for NaI(Tl) 59.5 keV gamma energy-deposition study.
///
/// This primary generator emits monoenergetic 59.5 keV gamma rays toward
/// the NaI(Tl) crystal along the +z direction.

#ifndef B4PrimaryGeneratorAction_h
#define B4PrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"

class G4ParticleGun;
class G4Event;

/// Primary generator action class.
///
/// Default source definition:
///
///   particle  : gamma
///   energy    : 59.5 keV
///   position  : (0, 0, -5 cm)
///   direction : +z
///
/// These settings can still be overridden from macro files using standard
/// /gun commands.

class B4PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
  public:
    B4PrimaryGeneratorAction();
    virtual ~B4PrimaryGeneratorAction();

    virtual void GeneratePrimaries(G4Event* event);

    // Set methods
    void SetRandomFlag(G4bool value);

  private:
    G4ParticleGun* fParticleGun;   // G4 particle gun
};

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
