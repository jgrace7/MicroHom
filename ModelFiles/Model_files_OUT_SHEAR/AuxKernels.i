[AuxKernels]
  [./gamma_xz]
    type = VariableGradientComponent
    variable = gamma_xz
    gradient_variable = u_z
    component = x
  [../]

  [./gamma_yz]
    type = VariableGradientComponent
    variable = gamma_yz
    gradient_variable = u_z
    component = y
  [../]

  [./G_aux]
    type = MaterialRankTwoTensorAux
    variable = G
    property = thermal_conductivity
    i = 0
    j = 0
  [../]


  [./tau_xz]
    type = ParsedAux
    variable = tau_xz
    expression = 'G * gamma_xz'
    coupled_variables = 'G gamma_xz'
  [../]

  [./tau_yz]
    type = ParsedAux
    variable = tau_yz
    expression = 'G * gamma_yz'
    coupled_variables = 'G gamma_yz'
  [../]
[]