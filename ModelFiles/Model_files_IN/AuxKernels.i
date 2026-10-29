# --- C11 (0000) ---
  [./C11_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C11_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 0
    k = 0
    l = 0
  [../]
  # --- C22 (1111) ---
  [./C22_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C22_{{PHASE}}
    property = elasticity_tensor
    i = 1
    j = 1
    k = 1
    l = 1
  [../]
  # --- C33 (2222) ---
  [./C33_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C33_{{PHASE}}
    property = elasticity_tensor
    i = 2
    j = 2
    k = 2
    l = 2
  [../]
  
  # --- C44 (2323 / 1212 in tensor indices) ---
  [./C44_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C44_{{PHASE}}
    property = elasticity_tensor
    i = 1
    j = 2
    k = 1
    l = 2
  [../]
  # --- C55 (1313 / 0202) ---
  [./C55_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C55_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 2
    k = 0
    l = 2
  [../]
  # --- C66 (1212 / 0101) ---
  [./C66_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C66_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 1
    k = 0
    l = 1
  [../]

  # --- C12 (0011) ---
  [./C12_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C12_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 0
    k = 1
    l = 1
  [../]
  # --- C13 (0022) ---
  [./C13_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C13_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 0
    k = 2
    l = 2
  [../]
  # --- C14 (0023) ---
  [./C14_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C14_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 0
    k = 1
    l = 2
  [../]
  # --- C15 (0013) ---
  [./C15_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C15_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 0
    k = 0
    l = 2
  [../]
  # --- C16 (0012) ---
  [./C16_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C16_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 0
    k = 0
    l = 1
  [../]

  # --- C23 (1122) ---
  [./C23_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C23_{{PHASE}}
    property = elasticity_tensor
    i = 1
    j = 1
    k = 2
    l = 2
  [../]
  # --- C24 (1123) ---
  [./C24_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C24_{{PHASE}}
    property = elasticity_tensor
    i = 1
    j = 1
    k = 1
    l = 2
  [../]
  # --- C25 (1113) ---
  [./C25_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C25_{{PHASE}}
    property = elasticity_tensor
    i = 1
    j = 1
    k = 0
    l = 2
  [../]
  # --- C26 (1112) ---
  [./C26_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C26_{{PHASE}}
    property = elasticity_tensor
    i = 1
    j = 1
    k = 0
    l = 1
  [../]

  # --- C34 (2223) ---
  [./C34_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C34_{{PHASE}}
    property = elasticity_tensor
    i = 2
    j = 2
    k = 1
    l = 2
  [../]
  # --- C35 (2213) ---
  [./C35_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C35_{{PHASE}}
    property = elasticity_tensor
    i = 2
    j = 2
    k = 0
    l = 2
  [../]
  # --- C36 (2212) ---
  [./C36_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C36_{{PHASE}}
    property = elasticity_tensor
    i = 2
    j = 2
    k = 0
    l = 1
  [../]

  # --- C45 (2313) ---
  [./C45_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C45_{{PHASE}}
    property = elasticity_tensor
    i = 1
    j = 2
    k = 0
    l = 2
  [../]
  # --- C46 (2312) ---
  [./C46_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C46_{{PHASE}}
    property = elasticity_tensor
    i = 1
    j = 2
    k = 0
    l = 1
  [../]
  # --- C56 (1312) ---
  [./C56_{{PHASE}}_fill]
    type = MaterialRankFourTensorAux
    variable = C56_{{PHASE}}
    property = elasticity_tensor
    i = 0
    j = 2
    k = 0
    l = 1
  [../]