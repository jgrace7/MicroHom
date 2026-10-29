# --- Normals ---
  [./C11_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C22_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C33_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  
  # --- Shears ---
  [./C44_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C55_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C66_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]

  # --- Off-Diagonals (Row 1) ---
  [./C12_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C13_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C14_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C15_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C16_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]

  # --- Off-Diagonals (Row 2) ---
  [./C23_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C24_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C25_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C26_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]

  # --- Off-Diagonals (Row 3) ---
  [./C34_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C35_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C36_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]

  # --- Off-Diagonals (Row 4 & 5 Interaction) ---
  [./C45_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C46_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]
  [./C56_{{PHASE}}]
    order = CONSTANT
    family = MONOMIAL
    block = '{{BLOCKS}}'
  [../]