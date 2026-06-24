//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// *  The Geant4 software is copyright of the Copyright Holders of    *
// *  the Geant4 Collaboration.                                       *
// ********************************************************************
//
//
/// \file B4DetectorConstruction.cc
/// \brief Implementation of the B4DetectorConstruction class
///
/// Modified geometry for NaI(Tl) 59.5 keV gamma energy-deposition study.
/// Original B4a absorber/gap sampling calorimeter is replaced by a single
/// cylindrical NaI(Tl) scintillator crystal.

#include "B4DetectorConstruction.hh"

#include "G4Material.hh"
#include "G4NistManager.hh"

#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4GlobalMagFieldMessenger.hh"
#include "G4AutoDelete.hh"

#include "G4GeometryManager.hh"
#include "G4PhysicalVolumeStore.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4SolidStore.hh"

#include "G4VisAttributes.hh"
#include "G4Colour.hh"

#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4ThreadLocal
G4GlobalMagFieldMessenger* B4DetectorConstruction::fMagFieldMessenger = nullptr;

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4DetectorConstruction::B4DetectorConstruction()
 : G4VUserDetectorConstruction(),
   fCrystalPV(nullptr),
   fCheckOverlaps(true)
{
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

B4DetectorConstruction::~B4DetectorConstruction()
{
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4VPhysicalVolume* B4DetectorConstruction::Construct()
{
  // Define materials
  DefineMaterials();

  // Define geometry
  return DefineVolumes();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void B4DetectorConstruction::DefineMaterials()
{
  auto nistManager = G4NistManager::Instance();

  // World material
  nistManager->FindOrBuildMaterial("G4_AIR");

  // NaI(Tl) scintillator approximation.
  // The thallium activator is neglected in the material definition because
  // it is only a trace dopant and has negligible influence on photon
  // interaction cross sections for this energy-deposition study.
  nistManager->FindOrBuildMaterial("G4_SODIUM_IODIDE");

  // Optional vacuum material, kept for possible later source/beamline studies.
  G4double z;
  G4double a;
  G4double density;

  if (!G4Material::GetMaterial("Galactic", false)) {
    new G4Material("Galactic",
                   z = 1.,
                   a = 1.01*g/mole,
                   density = universe_mean_density,
                   kStateGas,
                   2.73*kelvin,
                   3.e-18*pascal);
  }

  // Print material table
  G4cout << *(G4Material::GetMaterialTable()) << G4endl;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4VPhysicalVolume* B4DetectorConstruction::DefineVolumes()
{
  // --------------------------------------------------------------------------
  // Geometry parameters
  // --------------------------------------------------------------------------
  //
  // Initial detector model:
  // 2 inch diameter x 2 inch length cylindrical NaI(Tl) crystal.
  //
  // Coordinate convention:
  // - Crystal axis is along the z direction.
  // - Monoenergetic 59.5 keV gammas will later be emitted from negative z
  //   toward positive z using PrimaryGeneratorAction or macro commands.
  //
  // --------------------------------------------------------------------------

  const G4double crystalRadius = 25.4*mm;       // 2 inch diameter -> 1 inch radius
  const G4double crystalLength = 50.8*mm;       // 2 inch length
  const G4double worldSizeXY   = 15.0*cm;
  const G4double worldSizeZ    = 20.0*cm;

  // Get materials
  auto worldMaterial   = G4Material::GetMaterial("G4_AIR");
  auto crystalMaterial = G4Material::GetMaterial("G4_SODIUM_IODIDE");

  if (!worldMaterial || !crystalMaterial) {
    G4ExceptionDescription msg;
    msg << "Cannot retrieve materials already defined.";
    G4Exception("B4DetectorConstruction::DefineVolumes()",
                "NaI59keV001",
                FatalException,
                msg);
  }

  // --------------------------------------------------------------------------
  // World
  // --------------------------------------------------------------------------

  auto worldS =
    new G4Box("World",
              worldSizeXY/2.,
              worldSizeXY/2.,
              worldSizeZ/2.);

  auto worldLV =
    new G4LogicalVolume(worldS,
                        worldMaterial,
                        "World");

  auto worldPV =
    new G4PVPlacement(nullptr,
                      G4ThreeVector(),
                      worldLV,
                      "World",
                      nullptr,
                      false,
                      0,
                      fCheckOverlaps);

  // --------------------------------------------------------------------------
  // NaI(Tl) crystal
  // --------------------------------------------------------------------------

  auto crystalS =
    new G4Tubs("NaI_Crystal",
               0.0,
               crystalRadius,
               crystalLength/2.,
               0.0*deg,
               360.0*deg);

  auto crystalLV =
    new G4LogicalVolume(crystalS,
                        crystalMaterial,
                        "NaI_Crystal");

  fCrystalPV =
    new G4PVPlacement(nullptr,
                      G4ThreeVector(0., 0., 0.),
                      crystalLV,
                      "NaI_Crystal",
                      worldLV,
                      false,
                      0,
                      fCheckOverlaps);

  // --------------------------------------------------------------------------
  // Print geometry parameters
  // --------------------------------------------------------------------------

  G4cout
    << G4endl
    << "------------------------------------------------------------" << G4endl
    << " NaI(Tl) 59.5 keV gamma energy-deposition geometry" << G4endl
    << "------------------------------------------------------------" << G4endl
    << " World material      : " << worldMaterial->GetName() << G4endl
    << " Crystal material    : " << crystalMaterial->GetName() << G4endl
    << " Crystal radius      : " << crystalRadius/mm << " mm" << G4endl
    << " Crystal diameter    : " << 2.0*crystalRadius/mm << " mm" << G4endl
    << " Crystal length      : " << crystalLength/mm << " mm" << G4endl
    << " World size XY       : " << worldSizeXY/cm << " cm" << G4endl
    << " World size Z        : " << worldSizeZ/cm << " cm" << G4endl
    << " Scoring volume      : NaI_Crystal" << G4endl
    << "------------------------------------------------------------"
    << G4endl;

  // --------------------------------------------------------------------------
  // Visualization attributes
  // --------------------------------------------------------------------------

  worldLV->SetVisAttributes(G4VisAttributes::GetInvisible());

  auto crystalVisAtt = new G4VisAttributes(G4Colour(0.2, 0.8, 1.0, 0.35));
  crystalVisAtt->SetVisibility(true);
  crystalVisAtt->SetForceSolid(true);
  crystalLV->SetVisAttributes(crystalVisAtt);

  // Always return the physical World
  return worldPV;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void B4DetectorConstruction::ConstructSDandField()
{
  // No magnetic field is required for this gamma energy-deposition study.
  // The global field messenger is kept from the original B4a structure with
  // zero field for compatibility.

  G4ThreeVector fieldValue = G4ThreeVector();
  fMagFieldMessenger = new G4GlobalMagFieldMessenger(fieldValue);
  fMagFieldMessenger->SetVerboseLevel(1);

  // Register the field messenger for deletion
  G4AutoDelete::Register(fMagFieldMessenger);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
